from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional
import uvicorn

from github_similarity_service import SimilarityService
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


class IndexRequest(BaseModel):
    owner: str = Field(..., description="Repository owner/organization")
    repo: str = Field(..., description="Repository name")
    max_issues: int = Field(100, description="Maximum number of issues to index", ge=1, le=1000)
    include_discussions: bool = Field(False, description="Also index GitHub discussions")


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
            include_discussions=request.include_discussions
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
        return results
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