from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional
import uvicorn
import subprocess
import json
from datetime import datetime
import sys

from github_similarity_service import SimilarityService
from gh_auth_helper import ensure_gh_auth, format_auth_check_message
import requests


app = FastAPI(
    title="GitHub Issues Similarity API",
    description="Find similar GitHub issues using semantic similarity",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check GitHub CLI authentication on startup
github_auth_status = {"authenticated": False, "username": None, "checked": False}

@app.on_event("startup")
async def check_github_auth():
    """Check GitHub CLI authentication on API startup"""
    global github_auth_status
    print("=" * 60)
    print("GitHub Issues Similarity API")
    print("=" * 60)
    print("\nChecking GitHub CLI authentication...")
    
    is_auth, username = ensure_gh_auth(exit_on_failure=False, context="The API server")
    github_auth_status["authenticated"] = is_auth
    github_auth_status["username"] = username
    github_auth_status["checked"] = True
    
    if is_auth and username:
        print(f"✅ Authenticated as: {username}")
        print("=" * 60)
    else:
        print("\n⚠️  WARNING: GitHub CLI is not authenticated!")
        print("Some endpoints will have limited functionality.")
        print("To authenticate, run: gh auth login")
        print("=" * 60)

similarity_service = SimilarityService()


class IndexRequest(BaseModel):
    owner: str = Field(..., description="Repository owner/organization")
    repo: str = Field(..., description="Repository name")
    max_issues: int = Field(100, description="Maximum number of issues to index", ge=1, le=1000)
    include_discussions: bool = Field(False, description="Also index GitHub discussions")
    issue_state: str = Field("open", description="Issue state to index: open, closed, or all")


class FindSimilarRequest(BaseModel):
    owner: str = Field(..., description="Repository owner/organization")
    repo: str = Field(..., description="Repository name")
    issue_number: int = Field(..., description="Issue number to find similar issues for")
    top_k: int = Field(10, description="Number of similar issues to return", ge=1, le=50)
    min_similarity: float = Field(0.0, description="Minimum similarity score", ge=0.0, le=1.0)


class SuggestDiscussionsRequest(BaseModel):
    owner: str = Field(..., description="Repository owner/organization")
    repo: str = Field(..., description="Repository name")
    min_score: float = Field(0.5, description="Minimum discussion score", ge=0.0, le=1.0)
    max_suggestions: int = Field(20, description="Maximum number of suggestions", ge=1, le=100)
    dry_run: bool = Field(True, description="Dry run mode (no actual changes)")
    add_labels: bool = Field(False, description="Add labels to suggested issues based on confidence level")


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        service="github-issues-similarity"
    )


@app.get("/auth/status")
async def get_auth_status():
    """Check GitHub CLI authentication status"""
    global github_auth_status
    
    # Re-check if not checked yet or if requested
    if not github_auth_status["checked"]:
        is_auth, username = ensure_gh_auth(exit_on_failure=False)
        github_auth_status["authenticated"] = is_auth
        github_auth_status["username"] = username
        github_auth_status["checked"] = True
    
    return {
        "github_cli_authenticated": github_auth_status["authenticated"],
        "github_username": github_auth_status["username"],
        "message": format_auth_check_message(
            github_auth_status["authenticated"], 
            github_auth_status["username"]
        ),
        "auth_command": "gh auth login" if not github_auth_status["authenticated"] else None
    }


@app.post("/index")
async def index_repository(request: IndexRequest):
    try:
        result = similarity_service.index_repository(
            owner=request.owner,
            repo=request.repo,
            max_issues=request.max_issues,
            include_discussions=request.include_discussions,
            issue_state=request.issue_state
        )
        return result
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Repository {request.owner}/{request.repo} not found")
        elif e.response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded or authentication required")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/find_similar")
async def find_similar_issues(request: FindSimilarRequest):
    try:
        results = similarity_service.find_similar_issues(
            owner=request.owner,
            repo=request.repo,
            issue_number=request.issue_number,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        return {
            "query_issue": {
                "number": request.issue_number,
                "url": f"https://github.com/{request.owner}/{request.repo}/issues/{request.issue_number}"
            },
            "similar_issues": results,
            "count": len(results)
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Issue #{request.issue_number} not found in {request.owner}/{request.repo}")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    try:
        stats = similarity_service.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear")
async def clear_all_issues():
    try:
        result = similarity_service.clear_all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/suggest_discussions")
async def suggest_discussions(request: SuggestDiscussionsRequest):
    try:
        results = similarity_service.suggest_discussions(
            owner=request.owner,
            repo=request.repo,
            min_score=request.min_score,
            max_suggestions=request.max_suggestions,
            dry_run=request.dry_run
        )
        
        # Apply labels if requested and not in dry run
        if request.add_labels and not request.dry_run:
            labels_config = {
                "should-be-discussion": "8B5CF6",  # Purple
                "discussion": "0E7490",  # Teal
            }
            
            # Ensure labels exist
            similarity_service.ensure_labels_exist(request.owner, request.repo, labels_config)
            
            labeled_issues = []
            for suggestion in results.get("suggestions", []):
                confidence = suggestion.get("confidence", "low")
                labels_to_add = []
                
                if confidence == "high":
                    labels_to_add.append("should-be-discussion")
                elif confidence == "medium":
                    labels_to_add.append("discussion")
                
                if labels_to_add:
                    success = similarity_service.add_issue_labels(
                        request.owner, 
                        request.repo, 
                        suggestion["number"], 
                        labels_to_add
                    )
                    if success:
                        labeled_issues.append({
                            "number": suggestion["number"],
                            "labels": labels_to_add,
                            "confidence": confidence
                        })
            
            results["labeled_issues"] = labeled_issues
            results["labels_applied"] = len(labeled_issues) > 0
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{username}")
async def get_user_info(username: str):
    """
    Fetch GitHub user information using gh CLI.
    """
    try:
        # Run gh CLI command to get user info
        cmd = ["gh", "api", f"/users/{username}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to fetch user info: {result.stderr}")
        
        user_data = json.loads(result.stdout)
        
        # Extract relevant fields
        return {
            "login": user_data.get("login"),
            "name": user_data.get("name"),
            "bio": user_data.get("bio"),
            "company": user_data.get("company"),
            "location": user_data.get("location"),
            "public_repos": user_data.get("public_repos"),
            "followers": user_data.get("followers"),
            "following": user_data.get("following"),
            "created_at": user_data.get("created_at"),
            "avatar_url": user_data.get("avatar_url"),
            "html_url": user_data.get("html_url")
        }
    except subprocess.CalledProcessError as e:
        if "404" in str(e.stderr):
            raise HTTPException(status_code=404, detail=f"User {username} not found")
        raise HTTPException(status_code=500, detail=f"GitHub CLI error: {str(e)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse GitHub response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{username}/commented-issues")
async def get_user_commented_issues(
    username: str, 
    repo: str = None,
    limit: int = 5
):
    """
    Fetch the last N issues a user has commented on.
    Optionally filter by repository.
    """
    try:
        # Build the search query
        query = f"commenter:{username} is:issue"
        if repo:
            query += f" repo:{repo}"
        
        # Run gh CLI command to search for issues
        cmd = [
            "gh", "search", "issues",
            query,
            "--limit", str(limit),
            "--sort", "updated",
            "--json", "number,title,repository,state,updatedAt,url,labels"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to fetch issues: {result.stderr}")
        
        issues_data = json.loads(result.stdout) if result.stdout else []
        
        # Format the response
        formatted_issues = []
        for issue in issues_data:
            formatted_issues.append({
                "number": issue.get("number"),
                "title": issue.get("title"),
                "repository": issue.get("repository", {}).get("nameWithOwner"),
                "state": issue.get("state"),
                "url": issue.get("url"),
                "labels": [label.get("name") for label in issue.get("labels", [])],
                "updated_at": issue.get("updatedAt")
            })
        
        # For each issue, try to get the user's last comment
        for issue in formatted_issues:
            if issue["repository"]:
                try:
                    # Get comments for this issue
                    owner, repo_name = issue["repository"].split("/")
                    cmd_comments = [
                        "gh", "api",
                        f"/repos/{owner}/{repo_name}/issues/{issue['number']}/comments",
                        "--jq", f'[.[] | select(.user.login == "{username}")] | last | {{body: .body, created_at: .created_at}}'
                    ]
                    
                    comment_result = subprocess.run(cmd_comments, capture_output=True, text=True, timeout=5)
                    
                    if comment_result.returncode == 0 and comment_result.stdout.strip():
                        try:
                            comment_data = json.loads(comment_result.stdout)
                            issue["last_comment"] = {
                                "body": comment_data.get("body", "")[:200],  # First 200 chars
                                "created_at": comment_data.get("created_at")
                            }
                        except:
                            pass
                except:
                    # If we can't get the comment, that's okay
                    pass
        
        return {
            "username": username,
            "repository_filter": repo,
            "count": len(formatted_issues),
            "issues": formatted_issues
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = str(e.stderr) if e.stderr else str(e)
        if "not exist" in error_msg or "cannot be searched" in error_msg:
            # User might not exist or we don't have permission
            return {
                "username": username,
                "repository_filter": repo,
                "count": 0,
                "issues": [],
                "note": "User may not exist or may not have commented on any issues"
            }
        raise HTTPException(status_code=500, detail=f"GitHub CLI error: {error_msg}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse GitHub response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{username}/comments")
async def get_user_comments(
    username: str,
    limit: int = Query(10, description="Number of comments to fetch", ge=1, le=100),
    repo: Optional[str] = Query(None, description="Filter by repository (format: owner/repo)"),
    since: Optional[str] = Query(None, description="Show comments since date (YYYY-MM-DD)")
):
    """
    Fetch a user's recent comments from GitHub issues and PRs.
    This endpoint provides more detailed comment information.
    """
    try:
        # Build the search query
        search_query_parts = [f"commenter:{username}"]
        
        if repo:
            search_query_parts.append(f"repo:{repo}")
        
        search_query = " ".join(search_query_parts)
        
        # Use gh search to find issues/PRs where user has commented
        cmd = [
            "gh", "search", "issues",
            search_query,
            "--limit", str(limit * 2),  # Get more to ensure we have enough after filtering
            "--json", "number,title,repository,state,updatedAt,url,isPullRequest,labels,createdAt"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Failed to fetch data: {result.stderr}")
        
        items = json.loads(result.stdout) if result.stdout else []
        
        if not items:
            return {
                "username": username,
                "repository_filter": repo,
                "since_date": since,
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
                "--jq", f'[.[] | select(.user.login == "{username}") | {{body: .body, created_at: .created_at, html_url: .html_url, id: .id}}] | last'
            ]
            
            try:
                comment_result = subprocess.run(comment_cmd, capture_output=True, text=True, check=True, timeout=5)
                if comment_result.stdout.strip():
                    comment = json.loads(comment_result.stdout)
                    
                    # Check date filter if provided
                    if since:
                        comment_date = datetime.fromisoformat(comment['created_at'].replace('Z', '+00:00'))
                        since_date = datetime.fromisoformat(since)
                        if comment_date.date() < since_date.date():
                            continue
                    
                    comments_data.append({
                        'issue': {
                            'number': issue_number,
                            'title': item['title'],
                            'repository': repo_name,
                            'state': item['state'],
                            'is_pull_request': item['isPullRequest'],
                            'url': item['url'],
                            'labels': [label.get('name') for label in item.get('labels', [])]
                        },
                        'comment': {
                            'id': comment['id'],
                            'body': comment['body'],
                            'body_preview': comment['body'][:200] + "..." if len(comment['body']) > 200 else comment['body'],
                            'created_at': comment['created_at'],
                            'url': comment['html_url']
                        }
                    })
                    
                    if len(comments_data) >= limit:
                        break
            except subprocess.CalledProcessError:
                continue
            except Exception:
                continue
        
        return {
            "username": username,
            "repository_filter": repo,
            "since_date": since,
            "count": len(comments_data),
            "comments": comments_data
        }
        
    except subprocess.CalledProcessError as e:
        if "gh: command not found" in str(e.stderr):
            raise HTTPException(status_code=500, detail="GitHub CLI (gh) is not installed on the server")
        elif "not authenticated" in str(e.stderr):
            raise HTTPException(status_code=500, detail="Server is not authenticated with GitHub CLI")
        else:
            raise HTTPException(status_code=500, detail=f"GitHub CLI error: {str(e.stderr)}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse GitHub response: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/current/comments")
async def get_current_user_comments(
    limit: int = Query(10, description="Number of comments to fetch", ge=1, le=100),
    repo: Optional[str] = Query(None, description="Filter by repository (format: owner/repo)"),
    since: Optional[str] = Query(None, description="Show comments since date (YYYY-MM-DD)")
):
    """
    Fetch the authenticated user's recent comments from GitHub issues and PRs.
    """
    try:
        # Get authenticated user
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail="Failed to get authenticated user")
        
        username = result.stdout.strip()
        
        # Reuse the get_user_comments function logic
        return await get_user_comments(username, limit, repo, since)
        
    except subprocess.CalledProcessError as e:
        if "not authenticated" in str(e.stderr):
            raise HTTPException(status_code=401, detail="Server is not authenticated with GitHub CLI")
        else:
            raise HTTPException(status_code=500, detail=f"GitHub CLI error: {str(e.stderr)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message": "GitHub Issues Similarity API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "index": "/index",
            "find_similar": "/find_similar",
            "suggest_discussions": "/suggest_discussions",
            "stats": "/stats",
            "clear": "/clear",
            "user_info": "/user/{username}",
            "user_commented_issues": "/user/{username}/commented-issues",
            "user_comments": "/user/{username}/comments",
            "current_user_comments": "/user/current/comments"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)