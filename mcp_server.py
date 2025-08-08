#!/usr/bin/env python3
"""
FastMCP Server for Deja-View
Exposes GitHub issue similarity and user comment tools via MCP protocol
"""

from fastmcp import FastMCP
from github_similarity_service import SimilarityService
from gh_auth_helper import ensure_gh_auth, format_auth_check_message
import subprocess
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys

# Initialize MCP server
mcp = FastMCP("deja-view")
mcp.description = "GitHub issue similarity search and user activity tracking tools"

# Check GitHub CLI authentication on initialization
print("Checking GitHub CLI authentication...", file=sys.stderr)
is_authenticated, github_username = ensure_gh_auth(exit_on_failure=False, context="The MCP server")

if is_authenticated and github_username:
    print(f"✅ GitHub CLI authenticated as: {github_username}", file=sys.stderr)
else:
    print("⚠️  WARNING: GitHub CLI is not authenticated!", file=sys.stderr)
    print("Some tools will have limited functionality.", file=sys.stderr)
    print("To authenticate, run: gh auth login", file=sys.stderr)
    print("After authenticating, restart the MCP server.", file=sys.stderr)

# Initialize similarity service
try:
    similarity_service = SimilarityService()
except Exception as e:
    print(f"Warning: Could not initialize SimilarityService: {e}", file=sys.stderr)
    similarity_service = None


@mcp.tool()
def check_github_auth() -> Dict[str, Any]:
    """
    Check GitHub CLI authentication status.
    
    Returns:
        Dictionary containing authentication status and username
    
    Example:
        check_github_auth()
    """
    is_auth, username = ensure_gh_auth(exit_on_failure=False)
    
    return {
        "authenticated": is_auth,
        "username": username,
        "message": format_auth_check_message(is_auth, username),
        "auth_command": "gh auth login" if not is_auth else None,
        "note": "Run 'gh auth login' in terminal if not authenticated"
    }


@mcp.tool()
def find_similar_issues(
    repository: str,
    issue_number: int,
    limit: int = 10,
    min_similarity: float = 0.0
) -> Dict[str, Any]:
    """
    Find issues similar to a specific GitHub issue.
    
    Args:
        repository: Repository in format "owner/repo"
        issue_number: Issue number to find similar issues for
        limit: Maximum number of similar issues to return (default: 10)
        min_similarity: Minimum similarity score between 0 and 1 (default: 0.0)
    
    Returns:
        Dictionary containing similar issues with similarity scores
    
    Example:
        find_similar_issues("facebook/react", 1234, limit=5, min_similarity=0.7)
    """
    if not similarity_service:
        return {
            "error": "SimilarityService not initialized. Please check environment variables.",
            "required_vars": ["CHROMA_API_KEY", "CHROMA_TENANT", "GITHUB_TOKEN"]
        }
    
    try:
        owner, repo = repository.split("/")
        
        results = similarity_service.find_similar_issues(
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            top_k=limit,
            min_similarity=min_similarity
        )
        
        return {
            "query_issue": {
                "number": issue_number,
                "repository": repository,
                "url": f"https://github.com/{repository}/issues/{issue_number}"
            },
            "similar_issues": results,
            "count": len(results)
        }
    except ValueError:
        return {"error": "Repository must be in format 'owner/repo'"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def index_repository(
    repository: str,
    max_issues: int = 100,
    include_discussions: bool = False,
    issue_state: str = "open"
) -> Dict[str, Any]:
    """
    Index GitHub repository issues for similarity search.
    
    Args:
        repository: Repository in format "owner/repo"
        max_issues: Maximum number of issues to index (default: 100)
        include_discussions: Also index GitHub discussions (default: False)
        issue_state: Issue state to index - "open", "closed", or "all" (default: "open")
    
    Returns:
        Dictionary with indexing results
    
    Example:
        index_repository("continuedev/continue", max_issues=200, issue_state="all")
    """
    if not similarity_service:
        return {
            "error": "SimilarityService not initialized. Please check environment variables.",
            "required_vars": ["CHROMA_API_KEY", "CHROMA_TENANT", "GITHUB_TOKEN"]
        }
    
    try:
        owner, repo = repository.split("/")
        
        result = similarity_service.index_repository(
            owner=owner,
            repo=repo,
            max_issues=max_issues,
            include_discussions=include_discussions,
            issue_state=issue_state
        )
        
        return {
            "success": True,
            "repository": repository,
            "indexed": result.get("indexed", 0),
            "issues": result.get("issues", 0),
            "discussions": result.get("discussions", 0) if include_discussions else 0,
            "message": f"Successfully indexed {result.get('indexed', 0)} items from {repository}"
        }
    except ValueError:
        return {"error": "Repository must be in format 'owner/repo'"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_user_comments(
    username: str,
    limit: int = 10,
    repository: Optional[str] = None,
    since_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch a user's recent comments from GitHub issues and PRs.
    
    Args:
        username: GitHub username
        limit: Number of comments to fetch (default: 10)
        repository: Optional repository filter in format "owner/repo"
        since_date: Optional date filter in format "YYYY-MM-DD"
    
    Returns:
        Dictionary containing user's recent comments with issue context
    
    Example:
        get_user_comments("octocat", limit=5, repository="facebook/react")
    """
    # Check if GitHub CLI is authenticated
    if not is_authenticated:
        return {
            "error": "GitHub CLI is not authenticated",
            "message": "Please run 'gh auth login' in your terminal to authenticate",
            "authenticated": False
        }
    
    try:
        # Build the search query
        search_query_parts = [f"commenter:{username}"]
        
        if repository:
            search_query_parts.append(f"repo:{repository}")
        
        search_query = " ".join(search_query_parts)
        
        # Use gh search to find issues/PRs where user has commented
        cmd = [
            "gh", "search", "issues",
            search_query,
            "--limit", str(limit * 2),  # Get more to ensure we have enough after filtering
            "--json", "number,title,repository,state,updatedAt,url,isPullRequest,labels"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.returncode != 0:
            return {"error": f"Failed to fetch data: {result.stderr}"}
        
        items = json.loads(result.stdout) if result.stdout else []
        
        if not items:
            return {
                "username": username,
                "repository_filter": repository,
                "since_date": since_date,
                "count": 0,
                "comments": [],
                "message": "No comments found for the specified criteria"
            }
        
        # Fetch actual comments for each issue/PR
        comments_data = []
        for item in items[:limit]:
            repo_name = item['repository']['nameWithOwner']
            issue_number = item['number']
            
            # Fetch comments for this issue/PR
            comment_cmd = [
                "gh", "api",
                f"repos/{repo_name}/issues/{issue_number}/comments",
                "--jq", f'[.[] | select(.user.login == "{username}") | {{body: .body, created_at: .created_at, html_url: .html_url}}] | last'
            ]
            
            try:
                comment_result = subprocess.run(comment_cmd, capture_output=True, text=True, check=True, timeout=5)
                if comment_result.stdout.strip():
                    comment = json.loads(comment_result.stdout)
                    
                    # Check date filter if provided
                    if since_date:
                        comment_date = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                        since_datetime = datetime.fromisoformat(since_date)
                        if comment_date.date() < since_datetime.date():
                            continue
                    
                    comments_data.append({
                        'issue_number': issue_number,
                        'issue_title': item['title'],
                        'repository': repo_name,
                        'state': item['state'],
                        'is_pull_request': item['isPullRequest'],
                        'issue_url': item['url'],
                        'comment_preview': comment['body'][:200] + "..." if len(comment['body']) > 200 else comment['body'],
                        'comment_date': comment['created_at'],
                        'comment_url': comment['html_url']
                    })
                    
                    if len(comments_data) >= limit:
                        break
            except subprocess.CalledProcessError:
                continue
            except Exception:
                continue
        
        return {
            "username": username,
            "repository_filter": repository,
            "since_date": since_date,
            "count": len(comments_data),
            "comments": comments_data
        }
        
    except subprocess.CalledProcessError as e:
        if "gh: command not found" in str(e.stderr):
            return {"error": "GitHub CLI (gh) is not installed"}
        elif "not authenticated" in str(e.stderr):
            return {"error": "Not authenticated with GitHub CLI. Run: gh auth login"}
        else:
            return {"error": f"GitHub CLI error: {str(e.stderr)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse GitHub response: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def suggest_discussion_candidates(
    repository: str,
    min_score: float = 0.5,
    max_suggestions: int = 20
) -> Dict[str, Any]:
    """
    Suggest which issues should potentially be converted to discussions.
    
    Args:
        repository: Repository in format "owner/repo"
        min_score: Minimum discussion score between 0 and 1 (default: 0.5)
        max_suggestions: Maximum number of suggestions (default: 20)
    
    Returns:
        Dictionary containing suggested issues with reasons
    
    Example:
        suggest_discussion_candidates("facebook/react", min_score=0.7)
    """
    if not similarity_service:
        return {
            "error": "SimilarityService not initialized. Please check environment variables.",
            "required_vars": ["CHROMA_API_KEY", "CHROMA_TENANT", "GITHUB_TOKEN"]
        }
    
    try:
        owner, repo = repository.split("/")
        
        results = similarity_service.suggest_discussions(
            owner=owner,
            repo=repo,
            min_score=min_score,
            max_suggestions=max_suggestions,
            dry_run=True  # Always dry run for safety
        )
        
        suggestions = results.get("suggestions", [])
        
        # Group by confidence level
        high_confidence = [s for s in suggestions if s.get('score', 0) >= 0.7]
        medium_confidence = [s for s in suggestions if 0.5 <= s.get('score', 0) < 0.7]
        
        return {
            "repository": repository,
            "total_analyzed": results.get("total_analyzed", 0),
            "suggestions_count": len(suggestions),
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "summary": {
                "high_confidence_count": len(high_confidence),
                "medium_confidence_count": len(medium_confidence),
                "min_score": min_score
            }
        }
    except ValueError:
        return {"error": "Repository must be in format 'owner/repo'"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_similarity_stats() -> Dict[str, Any]:
    """
    Get statistics about indexed repositories and issues.
    
    Returns:
        Dictionary containing database statistics
    """
    if not similarity_service:
        return {
            "error": "SimilarityService not initialized. Please check environment variables.",
            "required_vars": ["CHROMA_API_KEY", "CHROMA_TENANT", "GITHUB_TOKEN"]
        }
    
    try:
        stats = similarity_service.get_stats()
        return {
            "total_issues": stats.get("total_issues", 0),
            "repositories": stats.get("repositories", []),
            "repository_count": len(stats.get("repositories", [])),
            "database_info": {
                "collection_name": "github_issues",
                "embeddings_model": "all-MiniLM-L6-v2"
            }
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def search_github_issues(
    query: str,
    repository: Optional[str] = None,
    limit: int = 10,
    sort: str = "relevance"
) -> Dict[str, Any]:
    """
    Search GitHub issues using GitHub's search API.
    
    Args:
        query: Search query string
        repository: Optional repository filter in format "owner/repo"
        limit: Maximum number of results (default: 10)
        sort: Sort order - "relevance", "created", "updated", "comments" (default: "relevance")
    
    Returns:
        Dictionary containing search results
    
    Example:
        search_github_issues("bug rendering", repository="facebook/react", limit=5)
    """
    # Check if GitHub CLI is authenticated
    if not is_authenticated:
        return {
            "error": "GitHub CLI is not authenticated",
            "message": "Please run 'gh auth login' in your terminal to authenticate",
            "authenticated": False
        }
    
    try:
        # Build the search query
        full_query = query
        if repository:
            full_query = f"{query} repo:{repository}"
        
        # Use gh search
        cmd = [
            "gh", "search", "issues",
            full_query,
            "--limit", str(limit),
            "--sort", sort,
            "--json", "number,title,repository,state,url,labels,createdAt,updatedAt,body"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.returncode != 0:
            return {"error": f"Search failed: {result.stderr}"}
        
        issues = json.loads(result.stdout) if result.stdout else []
        
        # Format the results
        formatted_issues = []
        for issue in issues:
            formatted_issues.append({
                "number": issue.get("number"),
                "title": issue.get("title"),
                "repository": issue.get("repository", {}).get("nameWithOwner"),
                "state": issue.get("state"),
                "url": issue.get("url"),
                "labels": [label.get("name") for label in issue.get("labels", [])],
                "body_preview": (issue.get("body", "")[:200] + "...") if issue.get("body") and len(issue.get("body", "")) > 200 else issue.get("body", ""),
                "created_at": issue.get("createdAt"),
                "updated_at": issue.get("updatedAt")
            })
        
        return {
            "query": query,
            "repository_filter": repository,
            "count": len(formatted_issues),
            "sort": sort,
            "results": formatted_issues
        }
        
    except subprocess.CalledProcessError as e:
        if "gh: command not found" in str(e.stderr):
            return {"error": "GitHub CLI (gh) is not installed"}
        elif "not authenticated" in str(e.stderr):
            return {"error": "Not authenticated with GitHub CLI. Run: gh auth login"}
        else:
            return {"error": f"Search error: {str(e.stderr)}"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse search results: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()