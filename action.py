#!/usr/bin/env python3
"""
GitHub Action entry point for Deja View
Automatically comments on new issues with similar existing issues
"""
import os
import sys
import json
import requests
from github_similarity_service import SimilarityService


def get_input(name: str, default: str = "") -> str:
    """Get input from GitHub Actions environment"""
    env_name = f"INPUT_{name.upper().replace('-', '_')}"
    return os.environ.get(env_name, default)


def set_output(name: str, value: str):
    """Set output for GitHub Actions"""
    output_file = os.environ.get('GITHUB_OUTPUT', '')
    if output_file:
        with open(output_file, 'a') as f:
            f.write(f"{name}={value}\n")
    else:
        print(f"::set-output name={name}::{value}")


def format_issues_table(issues):
    """Format similar issues as a markdown table"""
    if not issues:
        return "No similar issues found."
    
    table = "| # | Title | Similarity | State | Type |\n"
    table += "|---|-------|------------|-------|------|\n"
    
    for issue in issues:
        number = issue['number']
        title = issue['title']
        if len(title) > 50:
            title = title[:47] + "..."
        
        similarity = f"{issue['similarity']:.1%}"
        state = issue['state']
        
        # Determine type with emoji
        if issue.get('is_discussion', False):
            type_str = "💬 Discussion"
        elif issue['is_pull_request']:
            type_str = "🔀 PR"
        else:
            type_str = "🐛 Issue"
        
        table += f"| #{number} | {title} | {similarity} | {state} | {type_str} |\n"
    
    return table


def post_comment(owner: str, repo: str, issue_number: int, body: str, token: str):
    """Post a comment on a GitHub issue"""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.post(url, json={"body": body}, headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    # Get GitHub context
    github_event_path = os.environ.get('GITHUB_EVENT_PATH')
    if not github_event_path:
        print("Error: GITHUB_EVENT_PATH not found")
        sys.exit(1)
    
    with open(github_event_path, 'r') as f:
        event = json.load(f)
    
    # Check if this is an issue opened event
    if event.get('action') != 'opened' or 'issue' not in event:
        print("This action only runs on opened issues")
        set_output("similar-issues-found", "0")
        set_output("commented", "false")
        return
    
    # Skip if it's a pull request
    if event['issue'].get('pull_request'):
        print("Skipping pull request")
        set_output("similar-issues-found", "0")
        set_output("commented", "false")
        return
    
    # Get repository information
    repo_full_name = event['repository']['full_name']
    owner, repo = repo_full_name.split('/')
    issue_number = event['issue']['number']
    
    # Get action inputs
    max_issues = int(get_input('max-issues', '200'))
    similarity_threshold = float(get_input('similarity-threshold', '0.7'))
    max_similar_issues = int(get_input('max-similar-issues', '5'))
    index_on_run = get_input('index-on-run', 'true').lower() == 'true'
    include_discussions = get_input('include-discussions', 'false').lower() == 'true'
    comment_template = get_input('comment-template')
    github_token = os.environ.get('GITHUB_TOKEN')
    
    if not github_token:
        print("Error: GITHUB_TOKEN not found")
        sys.exit(1)
    
    try:
        # Initialize service
        service = SimilarityService()
        
        # Index repository if requested
        if index_on_run:
            print(f"Indexing {repo_full_name} with up to {max_issues} issues...")
            result = service.index_repository(owner, repo, max_issues, include_discussions)
            print(f"Indexed {result['indexed']} items from {result['repository']}")
        
        # Find similar issues
        print(f"Finding similar issues to #{issue_number}...")
        similar_issues = service.find_similar_issues(
            owner, repo, issue_number, 
            top_k=max_similar_issues + 10,  # Get extra to filter by threshold
            min_similarity=similarity_threshold
        )
        
        # Filter to max_similar_issues
        similar_issues = similar_issues[:max_similar_issues]
        
        if not similar_issues:
            print("No similar issues found above threshold")
            set_output("similar-issues-found", "0")
            set_output("commented", "false")
            return
        
        # Format comment
        issues_table = format_issues_table(similar_issues)
        
        # Use custom template or default
        if not comment_template:
            comment_template = """## 🔍 Similar Issues Found

I found these similar issues that might be related:

{issues_table}

> This comment was automatically generated by [Deja View](https://github.com/yourusername/deja-view) using semantic similarity search."""
        
        comment_body = comment_template.replace('{issues_table}', issues_table)
        
        # Post comment
        print(f"Posting comment with {len(similar_issues)} similar issues...")
        post_comment(owner, repo, issue_number, comment_body, github_token)
        
        print("Comment posted successfully!")
        set_output("similar-issues-found", str(len(similar_issues)))
        set_output("commented", "true")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()