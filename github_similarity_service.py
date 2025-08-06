import os
from typing import List, Dict, Optional, Union
from datetime import datetime
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
import requests
import re
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
    is_discussion: bool = False


class Discussion(BaseModel):
    number: int
    title: str
    body: Optional[str] = None
    category: str
    created_at: str
    updated_at: str
    url: str
    labels: List[str] = Field(default_factory=list)


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
        
        # Discussion suggestion patterns - more aggressive matching
        self.question_patterns = [
            r'^(how|what|why|when|where|which|who|can|could|should|would|will|is|are|do|does|did)\b',
            r'\?',
            r'\b(help|guidance|advice|opinion|thoughts|suggestions?|input|feedback)\b',
            r'\b(best practices?|recommendations?|approach|strategy|way)\b',
            r'\b(anyone|somebody|someone)\b.*\b(know|tried|experience|success)\b',
            r'\b(how to|how do|how can|how should)\b',
            r'\b(what.*think|thoughts on|opinions on)\b'
        ]
        
        self.feature_patterns = [
            r'\b(feature request|enhancement|suggestion|proposal|idea|rfc)\b',
            r'\b(would like|wish|hope|want|need|desire)\b.*\b(feature|functionality|capability|ability|option)\b',
            r'\b(add|implement|support|include|introduce|create)\b.*\b(feature|option|ability|functionality|support|capability)\b',
            r'\b(it would be|would be nice|would be great|would be helpful)\b',
            r'\b(request|requesting)\b.*\b(feature|enhancement|addition)\b',
            r'\b(can we|could we|should we)\b.*\b(add|implement|support|have)\b',
            r'\b(feature|functionality|capability)\b.*\b(request|suggestion|proposal)\b'
        ]
        
        self.discussion_labels = [
            'question', 'help wanted', 'discussion', 'feature request',
            'enhancement', 'idea', 'proposal', 'feedback', 'opinions',
            'rfc', 'design', 'brainstorming', 'suggestion'
        ]
        
        # RFC/Proposal patterns
        self.proposal_patterns = [
            r'\b(rfc|proposal|design doc|spec|specification)\b',
            r'\b(propose|proposing|suggest|suggesting)\b',
            r'\b(approach|solution|design|architecture)\b.*\b(discussion|feedback|thoughts)\b'
        ]
        
        # Discussion-oriented phrases
        self.discussion_phrases = [
            r'\b(open to|looking for|seeking)\b.*\b(feedback|input|thoughts|suggestions)\b',
            r'\b(brainstorm|discuss|explore|consider)\b',
            r'\b(community|everyone|folks|people)\b.*\b(think|opinion|experience)\b',
            r'\b(share.*experience|lessons learned|what.*worked)\b'
        ]
    
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
    
    def _get_github_graphql_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        return headers
    
    def _fetch_issues(self, owner: str, repo: str, max_issues: int = 100, state: str = "open") -> List[Issue]:
        issues = []
        page = 1
        per_page = min(100, max_issues)
        
        while len(issues) < max_issues:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues"
            params = {
                "state": state,
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
                    is_pull_request="pull_request" in item,
                    is_discussion=False
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
            is_pull_request="pull_request" in item,
            is_discussion=False
        )
    
    def _create_document_text(self, item: Union[Issue, Discussion]) -> str:
        if isinstance(item, Discussion):
            text_parts = [
                f"Title: {item.title}",
                f"Type: Discussion",
                f"Category: {item.category}",
            ]
        else:
            text_parts = [
                f"Title: {item.title}",
                f"Type: {'Pull Request' if item.is_pull_request else 'Discussion' if item.is_discussion else 'Issue'}",
                f"State: {item.state}",
            ]
        
        if item.labels:
            text_parts.append(f"Labels: {', '.join(item.labels)}")
        
        if item.body:
            # Truncate body to stay under 16KB limit (leaving room for other fields)
            max_body_length = 10000  # ~10KB for body, leaving room for other fields
            body = item.body[:max_body_length]
            if len(item.body) > max_body_length:
                body += "... [truncated]"
            text_parts.append(f"Body: {body}")
        
        return "\n\n".join(text_parts)
    
    def _fetch_discussions(self, owner: str, repo: str, max_discussions: int = 100) -> List[Discussion]:
        """Fetch discussions using GitHub GraphQL API"""
        if not self.github_token:
            return []  # GraphQL API requires authentication
        
        discussions = []
        cursor = None
        
        while len(discussions) < max_discussions:
            query = """
            query($owner: String!, $repo: String!, $first: Int!, $after: String) {
                repository(owner: $owner, name: $repo) {
                    discussions(first: $first, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
                        pageInfo {
                            hasNextPage
                            endCursor
                        }
                        nodes {
                            number
                            title
                            body
                            category {
                                name
                            }
                            createdAt
                            updatedAt
                            url
                            labels(first: 10) {
                                nodes {
                                    name
                                }
                            }
                        }
                    }
                }
            }
            """
            
            variables = {
                "owner": owner,
                "repo": repo,
                "first": min(100, max_discussions - len(discussions)),
                "after": cursor
            }
            
            response = requests.post(
                "https://api.github.com/graphql",
                headers=self._get_github_graphql_headers(),
                json={"query": query, "variables": variables}
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            if "errors" in data or "data" not in data:
                break
                
            repo_data = data["data"]["repository"]
            if not repo_data or not repo_data["discussions"]:
                break
                
            discussions_data = repo_data["discussions"]
            
            for item in discussions_data["nodes"]:
                discussion = Discussion(
                    number=item["number"],
                    title=item["title"],
                    body=item.get("body", ""),
                    category=item["category"]["name"],
                    created_at=item["createdAt"],
                    updated_at=item["updatedAt"],
                    url=item["url"],
                    labels=[label["name"] for label in item.get("labels", {}).get("nodes", [])]
                )
                discussions.append(discussion)
                
                if len(discussions) >= max_discussions:
                    break
            
            if not discussions_data["pageInfo"]["hasNextPage"]:
                break
                
            cursor = discussions_data["pageInfo"]["endCursor"]
        
        return discussions[:max_discussions]
    
    def index_repository(self, owner: str, repo: str, max_issues: int = 100, include_discussions: bool = False, issue_state: str = "open") -> Dict[str, Union[int, str]]:
        issues = self._fetch_issues(owner, repo, max_issues, state=issue_state)
        discussions = []
        
        if include_discussions:
            discussions = self._fetch_discussions(owner, repo, max_issues)
        
        all_items = issues + discussions
        
        if not all_items:
            return {"indexed": 0, "repository": f"{owner}/{repo}"}
        
        documents = []
        metadatas = []
        ids = []
        
        for item in all_items:
            if isinstance(item, Discussion):
                doc_id = f"{owner}/{repo}/discussions/{item.number}"
                metadata = {
                    "owner": owner,
                    "repo": repo,
                    "number": str(item.number),
                    "title": item.title,
                    "type": "discussion",
                    "category": item.category,
                    "url": item.url,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "is_pull_request": "False",
                    "is_discussion": "True",
                    "labels": ",".join(item.labels) if item.labels else ""
                }
            else:
                doc_id = f"{owner}/{repo}/issues/{item.number}"
                metadata = {
                    "owner": owner,
                    "repo": repo,
                    "number": str(item.number),
                    "title": item.title,
                    "type": "pull_request" if item.is_pull_request else "issue",
                    "state": item.state,
                    "url": item.url,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "is_pull_request": str(item.is_pull_request),
                    "is_discussion": str(item.is_discussion),
                    "labels": ",".join(item.labels) if item.labels else ""
                }
            
            documents.append(self._create_document_text(item))
            metadatas.append(metadata)
            ids.append(doc_id)
        
        self.collection.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "indexed": len(all_items),
            "issues": len(issues),
            "discussions": len(discussions),
            "repository": f"{owner}/{repo}",
            "message": f"Successfully indexed {len(issues)} issues" + (f" and {len(discussions)} discussions" if discussions else "")
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
                        "state": metadata.get("state", "open"),
                        "url": metadata["url"],
                        "type": metadata.get("type", "issue"),
                        "is_pull_request": metadata["is_pull_request"] == "True",
                        "is_discussion": metadata.get("is_discussion", "False") == "True",
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
    
    def _calculate_discussion_score(self, issue: Issue) -> tuple[float, List[str]]:
        """Calculate how likely an issue should be a discussion - more aggressive scoring"""
        score = 0.0
        reasons = []
        
        title_lower = issue.title.lower()
        body_lower = (issue.body or "").lower()
        combined_text = f"{title_lower} {body_lower}"
        
        # Check question patterns (increased weight)
        for pattern in self.question_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += 0.4
                reasons.append("Contains question pattern")
                break
        
        # Check feature request patterns (increased weight)
        for pattern in self.feature_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += 0.35
                reasons.append("Feature request pattern")
                break
        
        # Check RFC/Proposal patterns
        for pattern in self.proposal_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += 0.45
                reasons.append("RFC/Proposal pattern")
                break
        
        # Check discussion-oriented phrases
        for pattern in self.discussion_phrases:
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += 0.3
                reasons.append("Discussion-oriented language")
                break
        
        # Check labels (increased weight)
        for label in issue.labels:
            if label.lower() in [dl.lower() for dl in self.discussion_labels]:
                score += 0.5
                reasons.append(f"Has '{label}' label")
                break
        
        # Check for discussion-worthy keywords (expanded list)
        discussion_keywords = [
            'opinion', 'thoughts', 'feedback', 'advice', 'best practice',
            'recommendation', 'approach', 'strategy', 'philosophy', 'design decision',
            'brainstorm', 'explore', 'consider', 'community', 'input', 'guidance',
            'experience', 'lessons', 'workflow', 'process', 'methodology'
        ]
        
        keyword_count = 0
        for keyword in discussion_keywords:
            if keyword in combined_text:
                keyword_count += 1
                if keyword_count == 1:  # Only add reason once
                    reasons.append(f"Contains discussion keywords")
        
        # Scale score based on number of keywords found
        if keyword_count > 0:
            score += min(0.3, keyword_count * 0.1)
        
        # Reduced penalty for bug-related keywords (they might still be feature requests)
        bug_keywords = ['crash', 'exception', 'traceback', 'stacktrace', 'segfault']
        for keyword in bug_keywords:
            if keyword in combined_text:
                score -= 0.15  # Reduced from 0.3
                reasons.append(f"Possible bug report: '{keyword}'")
                break
        
        # Check if issue title suggests it's not a bug
        non_bug_indicators = ['feature', 'enhancement', 'suggestion', 'idea', 'proposal', 'rfc', 'discussion']
        for indicator in non_bug_indicators:
            if indicator in title_lower:
                score += 0.2
                reasons.append(f"Non-bug indicator in title: '{indicator}'")
                break
        
        # Bonus for open issues (closed issues less likely to be converted)
        if issue.state == 'open':
            score += 0.15  # Increased from 0.1
        
        # Additional scoring for title patterns that suggest discussion
        title_discussion_patterns = [
            r'^(rfc|proposal|idea|suggestion|enhancement|feature)[:.]',
            r'\[(rfc|proposal|idea|suggestion|enhancement|feature)\]',
            r'\b(thoughts|feedback|opinions)\b.*\?'
        ]
        
        for pattern in title_discussion_patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                score += 0.25
                reasons.append("Title suggests discussion format")
                break
        
        return max(0.0, min(1.0, score)), reasons
    
    def suggest_discussions(
        self, 
        owner: str, 
        repo: str, 
        min_score: float = 0.3,
        max_suggestions: int = 20,
        dry_run: bool = True
    ) -> Dict[str, Union[List[Dict], int, str]]:
        """Suggest which issues should be converted to discussions"""
        
        # Get all issues from the repository
        all_issues = self.collection.get(
            where={"$and": [
                {"owner": owner}, 
                {"repo": repo},
                {"type": "issue"}  # Only analyze issues, not PRs or existing discussions
            ]}
        )
        
        if not all_issues["ids"]:
            return {
                "suggestions": [],
                "total_analyzed": 0,
                "repository": f"{owner}/{repo}",
                "dry_run": dry_run,
                "message": "No issues found to analyze"
            }
        
        suggestions = []
        
        for i, metadata in enumerate(all_issues["metadatas"]):
            # Reconstruct issue from metadata
            issue = Issue(
                number=int(metadata["number"]),
                title=metadata["title"],
                body="",  # We don't store full body in metadata, would need to fetch
                state=metadata.get("state", "open"),
                created_at=metadata["created_at"],
                updated_at=metadata["updated_at"],
                url=metadata["url"],
                labels=metadata["labels"].split(",") if metadata["labels"] else [],
                is_pull_request=metadata["is_pull_request"] == "True",
                is_discussion=metadata.get("is_discussion", "False") == "True"
            )
            
            # Skip pull requests
            if issue.is_pull_request:
                continue
            
            score, reasons = self._calculate_discussion_score(issue)
            
            if score >= min_score:
                suggestions.append({
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.url,
                    "score": round(score, 3),
                    "reasons": reasons,
                    "state": issue.state,
                    "labels": issue.labels,
                    "created_at": issue.created_at
                })
        
        # Sort by score (highest first)
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        suggestions = suggestions[:max_suggestions]
        
        result = {
            "suggestions": suggestions,
            "total_analyzed": len([m for m in all_issues["metadatas"] if m.get("type") == "issue"]),
            "total_suggestions": len(suggestions),
            "repository": f"{owner}/{repo}",
            "dry_run": dry_run,
            "min_score": min_score
        }
        
        if dry_run:
            result["message"] = f"Dry run: Found {len(suggestions)} issues that could be discussions"
        else:
            result["message"] = f"Found {len(suggestions)} issues that could be discussions (conversion not implemented)"
        
        return result


if __name__ == "__main__":
    pass