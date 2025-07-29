import os
from typing import List, Dict, Optional, Union
from datetime import datetime
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field

load_dotenv()


class Issue(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    state: str
    created_at: str
    updated_at: str
    url: str
    labels: List[str] = Field(default_factory=list)
    is_pull_request: bool = False


class SimilarityService:
    def __init__(self):
        self.api_key = os.getenv("CHROMA_API_KEY")
        self.tenant = os.getenv("CHROMA_TENANT")
        self.database = os.getenv("CHROMA_DATABASE", "default-database")
        self.github_token = os.getenv("GITHUB_TOKEN")
        
        if not self.api_key:
            raise ValueError("CHROMA_API_KEY environment variable is required")
        
        if not self.tenant:
            raise ValueError("CHROMA_TENANT environment variable is required")
        
        self.client = chromadb.CloudClient(
            tenant=self.tenant,
            database=self.database,
            api_key=self.api_key
        )
        
        self.collection_name = "github_issues"
        self._init_collection()
    
    def _init_collection(self):
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _get_github_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        return headers
    
    def _fetch_issues(self, owner: str, repo: str, max_issues: int = 100) -> List[Issue]:
        issues = []
        page = 1
        per_page = min(100, max_issues)
        
        while len(issues) < max_issues:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            params = {
                "state": "all",
                "per_page": per_page,
                "page": page,
                "sort": "updated",
                "direction": "desc"
            }
            
            response = requests.get(url, headers=self._get_github_headers(), params=params)
            response.raise_for_status()
            
            batch = response.json()
            if not batch:
                break
            
            for item in batch:
                issue = Issue(
                    number=item["number"],
                    title=item["title"],
                    body=item.get("body", ""),
                    state=item["state"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"],
                    url=item["html_url"],
                    labels=[label["name"] for label in item.get("labels", [])],
                    is_pull_request="pull_request" in item
                )
                issues.append(issue)
                
                if len(issues) >= max_issues:
                    break
            
            page += 1
        
        return issues[:max_issues]
    
    def _fetch_single_issue(self, owner: str, repo: str, issue_number: int) -> Issue:
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        response = requests.get(url, headers=self._get_github_headers())
        response.raise_for_status()
        
        item = response.json()
        return Issue(
            number=item["number"],
            title=item["title"],
            body=item.get("body", ""),
            state=item["state"],
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            url=item["html_url"],
            labels=[label["name"] for label in item.get("labels", [])],
            is_pull_request="pull_request" in item
        )
    
    def _create_document_text(self, issue: Issue) -> str:
        text_parts = [
            f"Title: {issue.title}",
            f"Type: {'Pull Request' if issue.is_pull_request else 'Issue'}",
            f"State: {issue.state}",
        ]
        
        if issue.labels:
            text_parts.append(f"Labels: {', '.join(issue.labels)}")
        
        if issue.body:
            # Truncate body to stay under 16KB limit (leaving room for other fields)
            max_body_length = 10000  # ~10KB for body, leaving room for other fields
            body = issue.body[:max_body_length]
            if len(issue.body) > max_body_length:
                body += "... [truncated]"
            text_parts.append(f"Body: {body}")
        
        return "\n\n".join(text_parts)
    
    def index_repository(self, owner: str, repo: str, max_issues: int = 100) -> Dict[str, Union[int, str]]:
        issues = self._fetch_issues(owner, repo, max_issues)
        
        if not issues:
            return {"indexed": 0, "repository": f"{owner}/{repo}"}
        
        documents = []
        metadatas = []
        ids = []
        
        for issue in issues:
            doc_id = f"{owner}/{repo}/issues/{issue.number}"
            documents.append(self._create_document_text(issue))
            metadatas.append({
                "owner": owner,
                "repo": repo,
                "number": str(issue.number),
                "title": issue.title,
                "state": issue.state,
                "url": issue.url,
                "created_at": issue.created_at,
                "updated_at": issue.updated_at,
                "is_pull_request": str(issue.is_pull_request),
                "labels": ",".join(issue.labels) if issue.labels else ""
            })
            ids.append(doc_id)
        
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "indexed": len(issues),
            "repository": f"{owner}/{repo}",
            "message": f"Successfully indexed {len(issues)} issues"
        }
    
    def find_similar_issues(
        self, 
        owner: str, 
        repo: str, 
        issue_number: int, 
        top_k: int = 10,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Union[str, float, int]]]:
        target_issue = self._fetch_single_issue(owner, repo, issue_number)
        query_text = self._create_document_text(target_issue)
        
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k + 1,
            where={"$and": [{"owner": owner}, {"repo": repo}]}
        )
        
        similar_issues = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                if results["metadatas"][0][i]["number"] == str(issue_number):
                    continue
                
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance
                
                if similarity >= min_similarity:
                    metadata = results["metadatas"][0][i]
                    similar_issues.append({
                        "number": int(metadata["number"]),
                        "title": metadata["title"],
                        "similarity": round(similarity, 4),
                        "state": metadata["state"],
                        "url": metadata["url"],
                        "is_pull_request": metadata["is_pull_request"] == "True",
                        "labels": metadata["labels"].split(",") if metadata["labels"] else []
                    })
        
        return similar_issues
    
    def get_stats(self) -> Dict[str, Union[int, List[str]]]:
        all_items = self.collection.get()
        
        if not all_items["ids"]:
            return {"total_issues": 0, "repositories": []}
        
        repos = set()
        for metadata in all_items["metadatas"]:
            repos.add(f"{metadata['owner']}/{metadata['repo']}")
        
        return {
            "total_issues": len(all_items["ids"]),
            "repositories": sorted(list(repos))
        }
    
    def clear_all(self) -> Dict[str, str]:
        try:
            self.client.delete_collection(self.collection_name)
            self._init_collection()
            return {"message": "All issues cleared successfully"}
        except Exception as e:
            return {"error": str(e)}