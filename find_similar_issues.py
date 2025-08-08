#!/usr/bin/env python3
"""
Find open issues that have similar issues in the repository.
This helps identify potential duplicates or related issues.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
from github import Github
from github_similarity_service import SimilarityService
import chromadb

def find_issues_with_similar(
    repo_name: str,
    similarity_threshold: float = 0.7,
    max_similar: int = 3,
    max_issues: int = 100,
    include_closed: bool = False
) -> List[Dict]:
    """Find open issues that have similar issues."""
    
    # Initialize service
    service = SimilarityService()
    
    # Get GitHub client
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    g = Github(github_token)
    repo = g.get_repo(repo_name)
    
    # Get Chroma client
    chroma_api_key = os.environ.get('CHROMA_API_KEY') or os.environ.get('CHROMA_CLOUD_API_KEY')
    if not chroma_api_key:
        raise ValueError("CHROMA_API_KEY or CHROMA_CLOUD_API_KEY environment variable is required")
    
    chroma_tenant = os.environ.get('CHROMA_TENANT')
    if not chroma_tenant:
        raise ValueError("CHROMA_TENANT environment variable is required")
    
    chroma_database = os.environ.get('CHROMA_DATABASE', 'default-database')
    
    client = chromadb.CloudClient(
        tenant=chroma_tenant,
        database=chroma_database,
        api_key=chroma_api_key
    )
    
    collection_name = "github_issues"  # Use the same collection as the main service
    
    try:
        collection = client.get_collection(collection_name)
    except:
        print(f"Collection {collection_name} not found. Please index the repository first.")
        return []
    
    # Get open issues
    print(f"Fetching all open issues from {repo_name}...")
    issues_list = list(repo.get_issues(state='open', sort='created', direction='desc'))
    
    # Filter out pull requests
    issues_list = [issue for issue in issues_list if not issue.pull_request]
    
    total_issues = len(issues_list)
    print(f"Found {total_issues} open issues to analyze")
    
    issues_with_similar = []
    analyzed_count = 0
    
    for issue in issues_list:
        if max_issues and analyzed_count >= max_issues:
            break
            
        analyzed_count += 1
        
        if analyzed_count % 25 == 0:
            print(f"Processed {analyzed_count}/{total_issues} issues ({analyzed_count*100/total_issues:.1f}%)...")
        
        # Search for similar issues
        issue_text = f"{issue.title} {issue.body or ''}"
        
        try:
            results = collection.query(
                query_texts=[issue_text],
                n_results=max_similar + 1,  # +1 to exclude self
                where={"state": "all"} if include_closed else None
            )
            
            if results and results['documents'] and len(results['documents'][0]) > 0:
                similar_issues = []
                
                for i, (doc, meta, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    # Skip self - check both as int and string
                    issue_num = meta.get('number')
                    if issue_num and (str(issue_num) == str(issue.number) or int(issue_num) == issue.number):
                        continue
                    
                    # Calculate similarity score (1 - normalized distance)
                    similarity = 1 - (distance / 2)  # Normalize to 0-1 range
                    
                    if similarity >= similarity_threshold:
                        similar_issues.append({
                            'number': meta.get('number'),
                            'title': meta.get('title'),
                            'url': meta.get('url'),
                            'state': meta.get('state', 'unknown'),
                            'similarity': similarity,
                            'created_at': meta.get('created_at'),
                            'labels': meta.get('labels', [])
                        })
                
                if similar_issues:
                    issues_with_similar.append({
                        'issue': {
                            'number': issue.number,
                            'title': issue.title,
                            'url': issue.html_url,
                            'created_at': issue.created_at.isoformat(),
                            'labels': [label.name for label in issue.labels]
                        },
                        'similar_issues': similar_issues[:max_similar],
                        'max_similarity': max(s['similarity'] for s in similar_issues)
                    })
                    
        except Exception as e:
            print(f"Error processing issue #{issue.number}: {e}")
            continue
    
    # Sort by max similarity score
    issues_with_similar.sort(key=lambda x: x['max_similarity'], reverse=True)
    
    return issues_with_similar

def generate_markdown_report(
    issues_data: List[Dict],
    repo_name: str,
    threshold: float
) -> str:
    """Generate a markdown report of issues with similar issues."""
    
    report = f"# Similar Issues Report for {repo_name}\n\n"
    report += f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"**Open Issues with Similar Issues:** {len(issues_data)}\n"
    report += f"**Similarity Threshold:** {threshold * 100:.0f}%\n\n"
    
    if not issues_data:
        report += "_No open issues with similar issues found._\n"
        return report
    
    # Group by similarity level
    high_similarity = [d for d in issues_data if d['max_similarity'] >= 0.85]
    medium_similarity = [d for d in issues_data if 0.7 <= d['max_similarity'] < 0.85]
    
    if high_similarity:
        report += "## 🔴 High Similarity (≥85%)\n\n"
        report += "These issues have very similar existing issues and might be duplicates.\n\n"
        
        for data in high_similarity:
            issue = data['issue']
            similar = data['similar_issues']
            
            report += f"### [{issue['title']}](#{issue['number']})\n"
            report += f"**Issue:** [#{issue['number']}]({issue['url']})\n"
            report += f"**Created:** {issue['created_at'][:10]}\n"
            
            if issue['labels']:
                report += f"**Labels:** {', '.join(issue['labels'])}\n"
            
            report += "\n**Similar Issues:**\n"
            
            for sim in similar:
                state_emoji = '🟢' if sim['state'] == 'open' else '🔴'
                report += f"- {state_emoji} [#{sim['number']}: {sim['title']}]({sim['url']}) "
                report += f"({sim['similarity'] * 100:.0f}% similar)\n"
            
            report += "\n---\n\n"
    
    if medium_similarity:
        report += "## 🟡 Medium Similarity (70-84%)\n\n"
        report += "These issues have related existing issues that might be worth linking.\n\n"
        
        report += "| Issue | Similar Issues | Max Similarity |\n"
        report += "|-------|----------------|----------------|\n"
        
        for data in medium_similarity:
            issue = data['issue']
            similar = data['similar_issues']
            
            # Format issue link
            issue_link = f"[#{issue['number']}]({issue['url']})"
            
            # Format similar issues
            similar_links = []
            for sim in similar[:2]:  # Show top 2 for table format
                state = '🟢' if sim['state'] == 'open' else '🔴'
                similar_links.append(f"{state} #{sim['number']}")
            
            max_sim = f"{data['max_similarity'] * 100:.0f}%"
            
            report += f"| {issue_link} | {', '.join(similar_links)} | {max_sim} |\n"
    
    # Add summary statistics
    report += "\n## Summary\n\n"
    report += f"- **High Similarity (≥85%):** {len(high_similarity)} issues\n"
    report += f"- **Medium Similarity (70-84%):** {len(medium_similarity)} issues\n"
    report += f"- **Total:** {len(issues_data)} open issues with similar issues\n\n"
    
    # Add quick actions
    if high_similarity:
        report += "## Quick Actions\n\n"
        report += "### Review potential duplicates:\n"
        report += "```bash\n"
        for data in high_similarity[:5]:  # Limit to first 5
            issue = data['issue']
            report += f"# Review issue #{issue['number']} and its similar issues\n"
            report += f"gh issue view {issue['number']} -R {repo_name}\n"
        report += "```\n\n"
        
        report += "### Add 'potential-duplicate' label:\n"
        report += "```bash\n"
        for data in high_similarity[:5]:
            issue = data['issue']
            report += f"gh issue edit {issue['number']} --add-label 'potential-duplicate' -R {repo_name}\n"
        report += "```\n\n"
    
    report += "---\n"
    report += "_Generated by [deja-view](https://github.com/bdougie/deja-view)_\n"
    
    return report

def main():
    parser = argparse.ArgumentParser(
        description='Find open issues that have similar existing issues'
    )
    parser.add_argument(
        'repo',
        help='Repository name (e.g., continuedev/continue)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.7,
        help='Similarity threshold (0.0-1.0, default: 0.7)'
    )
    parser.add_argument(
        '--max-similar',
        type=int,
        default=3,
        help='Maximum number of similar issues to show per issue (default: 3)'
    )
    parser.add_argument(
        '--max-issues',
        type=int,
        default=None,
        help='Maximum number of open issues to analyze (default: all)'
    )
    parser.add_argument(
        '--include-closed',
        action='store_true',
        help='Include closed issues in similarity search'
    )
    parser.add_argument(
        '--output',
        default='similar-issues-report.md',
        help='Output file for markdown report (default: similar-issues-report.md)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Also output raw JSON data'
    )
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.environ.get('GITHUB_TOKEN'):
        print("Error: GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    if not (os.environ.get('CHROMA_API_KEY') or os.environ.get('CHROMA_CLOUD_API_KEY')):
        print("Error: CHROMA_API_KEY or CHROMA_CLOUD_API_KEY environment variable is required")
        sys.exit(1)
    
    print(f"Finding open issues with similar issues in {args.repo}...")
    print(f"Similarity threshold: {args.threshold * 100:.0f}%")
    if args.max_issues:
        print(f"Analyzing up to {args.max_issues} open issues...")
    else:
        print(f"Analyzing ALL open issues...")
    
    try:
        # Find issues with similar issues
        issues_data = find_issues_with_similar(
            args.repo,
            similarity_threshold=args.threshold,
            max_similar=args.max_similar,
            max_issues=args.max_issues,
            include_closed=args.include_closed
        )
        
        print(f"Found {len(issues_data)} open issues with similar issues")
        
        # Generate markdown report
        report = generate_markdown_report(issues_data, args.repo, args.threshold)
        
        # Save report
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
        
        # Optionally save JSON data
        if args.json:
            json_file = args.output.replace('.md', '.json')
            with open(json_file, 'w') as f:
                json.dump(issues_data, f, indent=2)
            print(f"JSON data saved to {json_file}")
        
        # Print summary
        if issues_data:
            high_count = len([d for d in issues_data if d['max_similarity'] >= 0.85])
            if high_count > 0:
                print(f"\n⚠️  Found {high_count} issues with high similarity (≥85%) - potential duplicates!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()