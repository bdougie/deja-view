from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional
import uvicorn

from github_similarity_service import SimilarityService
from discussions_metrics import DiscussionsMetricsService
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

similarity_service = SimilarityService()
discussions_service = DiscussionsMetricsService()


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


class DiscussionsMetricsRequest(BaseModel):
    owner: str = Field(..., description="Repository owner/organization")
    repo: str = Field(..., description="Repository name")
    weeks_back: int = Field(4, description="Number of weeks to analyze", ge=1, le=52)


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


@app.post("/discussions_metrics")
async def get_discussions_metrics(request: DiscussionsMetricsRequest):
    """Get GitHub Discussions metrics and analytics"""
    try:
        metrics = discussions_service.fetch_discussions_metrics(
            owner=request.owner,
            repo=request.repo,
            weeks_back=request.weeks_back
        )
        
        # Convert dataclass to dict for JSON serialization
        from dataclasses import asdict
        return asdict(metrics)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Repository {request.owner}/{request.repo} not found or discussions not enabled")
        elif e.response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded or authentication required")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/discussions_metrics/{owner}/{repo}")
async def get_discussions_metrics_simple(owner: str, repo: str, weeks_back: int = 4):
    """Get GitHub Discussions metrics (simple GET endpoint)"""
    try:
        metrics = discussions_service.fetch_discussions_metrics(
            owner=owner,
            repo=repo,
            weeks_back=weeks_back
        )
        
        # Convert dataclass to dict for JSON serialization
        from dataclasses import asdict
        return asdict(metrics)
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Repository {owner}/{repo} not found or discussions not enabled")
        elif e.response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API rate limit exceeded or authentication required")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message": "GitHub Issues Similarity API",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)