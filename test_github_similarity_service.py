#!/usr/bin/env python3
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import requests
from github_similarity_service import SimilarityService, Issue, Discussion


class TestModels:
    def test_issue_model(self):
        issue = Issue(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/issues/123",
            labels=["bug", "high-priority"],
            is_pull_request=False,
            is_discussion=False
        )
        
        assert issue.number == 123
        assert issue.title == "Test Issue"
        assert issue.labels == ["bug", "high-priority"]
        assert not issue.is_pull_request
        assert not issue.is_discussion
    
    def test_discussion_model(self):
        discussion = Discussion(
            number=456,
            title="How to use feature X?",
            body="I need help with...",
            category="Q&A",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/discussions/456",
            labels=["question"]
        )
        
        assert discussion.number == 456
        assert discussion.title == "How to use feature X?"
        assert discussion.category == "Q&A"
        assert discussion.labels == ["question"]


class TestSimilarityService:
    @patch.dict(os.environ, {
        'CHROMA_API_KEY': 'test-key',
        'CHROMA_TENANT': 'test-tenant',
        'CHROMA_DATABASE': 'test-db',
        'GITHUB_TOKEN': 'test-token'
    })
    @patch('github_similarity_service.chromadb.CloudClient')
    def test_init_success(self, mock_chroma_client):
        mock_collection = Mock()
        mock_chroma_client.return_value.get_collection.return_value = mock_collection
        
        service = SimilarityService()
        
        assert service.api_key == 'test-key'
        assert service.tenant == 'test-tenant'
        assert service.github_token == 'test-token'
        mock_chroma_client.assert_called_once()
    
    @patch.dict(os.environ, {}, clear=True)
    def test_init_missing_api_key(self):
        with pytest.raises(ValueError, match="CHROMA_API_KEY environment variable is required"):
            SimilarityService()
    
    @patch.dict(os.environ, {'CHROMA_API_KEY': 'test-key'}, clear=True)
    def test_init_missing_tenant(self):
        with pytest.raises(ValueError, match="CHROMA_TENANT environment variable is required"):
            SimilarityService()
    
    @patch.dict(os.environ, {
        'CHROMA_API_KEY': 'test-key',
        'CHROMA_TENANT': 'test-tenant'
    })
    @patch('github_similarity_service.chromadb.CloudClient')
    def test_init_collection_creation(self, mock_chroma_client):
        mock_client = Mock()
        mock_chroma_client.return_value = mock_client
        mock_client.get_collection.side_effect = Exception("Collection not found")
        mock_client.create_collection.return_value = Mock()
        
        service = SimilarityService()
        
        mock_client.create_collection.assert_called_once_with(
            name="github_issues",
            metadata={"hnsw:space": "cosine"}
        )


class TestGitHubAPIInteractions:
    @patch.dict(os.environ, {
        'CHROMA_API_KEY': 'test-key',
        'CHROMA_TENANT': 'test-tenant',
        'GITHUB_TOKEN': 'test-token'
    })
    @patch('github_similarity_service.chromadb.CloudClient')
    def setup_method(self, method, mock_chroma_client):
        mock_collection = Mock()
        mock_chroma_client.return_value.get_collection.return_value = mock_collection
        self.service = SimilarityService()
        self.service.collection = mock_collection
    
    @patch('github_similarity_service.requests.get')
    def test_fetch_issues_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "Body 1",
                "state": "open",
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "html_url": "https://github.com/owner/repo/issues/1",
                "labels": [{"name": "bug"}]
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "Body 2",
                "state": "closed",
                "created_at": "2023-01-02T00:00:00Z",
                "updated_at": "2023-01-02T00:00:00Z",
                "html_url": "https://github.com/owner/repo/issues/2",
                "labels": [],
                "pull_request": {"url": "..."}
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        issues = self.service._fetch_issues("owner", "repo", max_issues=2)
        
        assert len(issues) == 2
        assert issues[0].number == 1
        assert issues[0].title == "Issue 1"
        assert issues[0].labels == ["bug"]
        assert not issues[0].is_pull_request
        assert issues[1].is_pull_request
    
    @patch('github_similarity_service.requests.get')
    def test_fetch_single_issue(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "number": 123,
            "title": "Test Issue",
            "body": "Test body",
            "state": "open",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
            "html_url": "https://github.com/owner/repo/issues/123",
            "labels": [{"name": "bug"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        issue = self.service._fetch_single_issue("owner", "repo", 123)
        
        assert issue.number == 123
        assert issue.title == "Test Issue"
        mock_get.assert_called_once_with(
            "https://api.github.com/repos/owner/repo/issues/123",
            headers={"Accept": "application/vnd.github.v3+json", "Authorization": "token test-token"}
        )
    
    @patch('github_similarity_service.requests.post')
    def test_fetch_discussions(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "repository": {
                    "discussions": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {
                                "number": 1,
                                "title": "Discussion 1",
                                "body": "Body 1",
                                "category": {"name": "Q&A"},
                                "createdAt": "2023-01-01T00:00:00Z",
                                "updatedAt": "2023-01-01T00:00:00Z",
                                "url": "https://github.com/owner/repo/discussions/1",
                                "labels": {"nodes": [{"name": "question"}]}
                            }
                        ]
                    }
                }
            }
        }
        mock_post.return_value = mock_response
        
        discussions = self.service._fetch_discussions("owner", "repo", max_discussions=1)
        
        assert len(discussions) == 1
        assert discussions[0].number == 1
        assert discussions[0].title == "Discussion 1"
        assert discussions[0].category == "Q&A"
        assert discussions[0].labels == ["question"]
    
    def test_create_document_text_issue(self):
        issue = Issue(
            number=123,
            title="Test Issue",
            body="This is a test body",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/issues/123",
            labels=["bug", "urgent"],
            is_pull_request=False,
            is_discussion=False
        )
        
        doc_text = self.service._create_document_text(issue)
        
        assert "Title: Test Issue" in doc_text
        assert "Type: Issue" in doc_text
        assert "State: open" in doc_text
        assert "Labels: bug, urgent" in doc_text
        assert "Body: This is a test body" in doc_text
    
    def test_create_document_text_discussion(self):
        discussion = Discussion(
            number=456,
            title="Test Discussion",
            body="Discussion body",
            category="Q&A",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/discussions/456",
            labels=["help"]
        )
        
        doc_text = self.service._create_document_text(discussion)
        
        assert "Title: Test Discussion" in doc_text
        assert "Type: Discussion" in doc_text
        assert "Category: Q&A" in doc_text
        assert "Labels: help" in doc_text
        assert "Body: Discussion body" in doc_text


class TestIndexingAndSearch:
    @patch.dict(os.environ, {
        'CHROMA_API_KEY': 'test-key',
        'CHROMA_TENANT': 'test-tenant',
        'GITHUB_TOKEN': 'test-token'
    })
    @patch('github_similarity_service.chromadb.CloudClient')
    def setup_method(self, method, mock_chroma_client):
        mock_collection = Mock()
        mock_chroma_client.return_value.get_collection.return_value = mock_collection
        self.service = SimilarityService()
        self.service.collection = mock_collection
    
    @patch.object(SimilarityService, '_fetch_issues')
    @patch.object(SimilarityService, '_fetch_discussions')
    def test_index_repository_issues_only(self, mock_fetch_discussions, mock_fetch_issues):
        mock_fetch_issues.return_value = [
            Issue(
                number=1,
                title="Issue 1",
                body="Body 1",
                state="open",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
                url="https://github.com/owner/repo/issues/1",
                labels=["bug"]
            )
        ]
        mock_fetch_discussions.return_value = []
        
        result = self.service.index_repository("owner", "repo", max_issues=1, include_discussions=False)
        
        assert result["indexed"] == 1
        assert result["issues"] == 1
        assert result["discussions"] == 0
        mock_fetch_issues.assert_called_once_with("owner", "repo", 1)
        mock_fetch_discussions.assert_not_called()
        self.service.collection.upsert.assert_called_once()
    
    @patch.object(SimilarityService, '_fetch_issues')
    @patch.object(SimilarityService, '_fetch_discussions')
    def test_index_repository_with_discussions(self, mock_fetch_discussions, mock_fetch_issues):
        mock_fetch_issues.return_value = [
            Issue(
                number=1,
                title="Issue 1",
                body="Body 1",
                state="open",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
                url="https://github.com/owner/repo/issues/1",
                labels=[]
            )
        ]
        mock_fetch_discussions.return_value = [
            Discussion(
                number=1,
                title="Discussion 1",
                body="Body 1",
                category="Q&A",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z",
                url="https://github.com/owner/repo/discussions/1",
                labels=[]
            )
        ]
        
        result = self.service.index_repository("owner", "repo", max_issues=1, include_discussions=True)
        
        assert result["indexed"] == 2
        assert result["issues"] == 1
        assert result["discussions"] == 1
        mock_fetch_discussions.assert_called_once_with("owner", "repo", 1)
    
    @patch.object(SimilarityService, '_fetch_single_issue')
    def test_find_similar_issues(self, mock_fetch_issue):
        mock_fetch_issue.return_value = Issue(
            number=123,
            title="Test Issue",
            body="Test body",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/issues/123",
            labels=[]
        )
        
        self.service.collection.query.return_value = {
            "ids": [["owner/repo/issues/1", "owner/repo/issues/123", "owner/repo/issues/2"]],
            "distances": [[0.1, 0.0, 0.2]],
            "metadatas": [[
                {
                    "number": "1",
                    "title": "Similar Issue 1",
                    "state": "open",
                    "url": "https://github.com/owner/repo/issues/1",
                    "type": "issue",
                    "is_pull_request": "False",
                    "is_discussion": "False",
                    "labels": "bug,help"
                },
                {
                    "number": "123",
                    "title": "Test Issue",
                    "state": "open",
                    "url": "https://github.com/owner/repo/issues/123",
                    "type": "issue",
                    "is_pull_request": "False",
                    "is_discussion": "False",
                    "labels": ""
                },
                {
                    "number": "2",
                    "title": "Similar Issue 2",
                    "state": "closed",
                    "url": "https://github.com/owner/repo/issues/2",
                    "type": "issue",
                    "is_pull_request": "False",
                    "is_discussion": "False",
                    "labels": ""
                }
            ]]
        }
        
        results = self.service.find_similar_issues("owner", "repo", 123, top_k=2, min_similarity=0.5)
        
        assert len(results) == 2
        assert results[0]["number"] == 1
        assert results[0]["similarity"] == 0.9
        assert results[0]["labels"] == ["bug", "help"]
        assert results[1]["number"] == 2
        assert results[1]["similarity"] == 0.8
    
    def test_get_stats(self):
        self.service.collection.get.return_value = {
            "ids": ["owner/repo1/issues/1", "owner/repo1/issues/2", "owner/repo2/issues/1"],
            "metadatas": [
                {"owner": "owner", "repo": "repo1"},
                {"owner": "owner", "repo": "repo1"},
                {"owner": "owner", "repo": "repo2"}
            ]
        }
        
        stats = self.service.get_stats()
        
        assert stats["total_issues"] == 3
        assert stats["repositories"] == ["owner/repo1", "owner/repo2"]
    
    def test_clear_all(self):
        self.service.client = Mock()
        self.service.client.delete_collection.return_value = None
        self.service.client.create_collection.return_value = Mock()
        
        result = self.service.clear_all()
        
        assert result["message"] == "All issues cleared successfully"
        self.service.client.delete_collection.assert_called_once_with("github_issues")


class TestDiscussionSuggestions:
    @patch.dict(os.environ, {
        'CHROMA_API_KEY': 'test-key',
        'CHROMA_TENANT': 'test-tenant'
    })
    @patch('github_similarity_service.chromadb.CloudClient')
    def setup_method(self, method, mock_chroma_client):
        mock_collection = Mock()
        mock_chroma_client.return_value.get_collection.return_value = mock_collection
        self.service = SimilarityService()
        self.service.collection = mock_collection
    
    def test_calculate_discussion_score_question(self):
        issue = Issue(
            number=1,
            title="How do I configure the model?",
            body="I need help understanding how to set up the configuration",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/issues/1",
            labels=["question"]
        )
        
        score, reasons = self.service._calculate_discussion_score(issue)
        
        assert score > 0.5
        assert any("question" in r.lower() for r in reasons)
        assert any("label" in r.lower() for r in reasons)
    
    def test_calculate_discussion_score_feature_request(self):
        issue = Issue(
            number=2,
            title="Feature request: Add dark mode",
            body="It would be great to have a dark mode option",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/issues/2",
            labels=["enhancement"]
        )
        
        score, reasons = self.service._calculate_discussion_score(issue)
        
        assert score > 0.5
        assert any("feature" in r.lower() for r in reasons)
    
    def test_calculate_discussion_score_bug_report(self):
        issue = Issue(
            number=3,
            title="Application crashes on startup",
            body="Getting segfault when trying to start the app",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="https://github.com/owner/repo/issues/3",
            labels=["bug"]
        )
        
        score, reasons = self.service._calculate_discussion_score(issue)
        
        assert score < 0.5
        assert any("bug" in r.lower() for r in reasons)
    
    def test_suggest_discussions(self):
        self.service.collection.get.return_value = {
            "ids": ["owner/repo/issues/1", "owner/repo/issues/2"],
            "metadatas": [
                {
                    "owner": "owner",
                    "repo": "repo",
                    "number": "1",
                    "title": "How to use feature X?",
                    "type": "issue",
                    "state": "open",
                    "url": "https://github.com/owner/repo/issues/1",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                    "is_pull_request": "False",
                    "is_discussion": "False",
                    "labels": "question"
                },
                {
                    "owner": "owner",
                    "repo": "repo",
                    "number": "2",
                    "title": "Bug: app crashes",
                    "type": "issue",
                    "state": "open",
                    "url": "https://github.com/owner/repo/issues/2",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                    "is_pull_request": "False",
                    "is_discussion": "False",
                    "labels": "bug"
                }
            ]
        }
        
        result = self.service.suggest_discussions("owner", "repo", min_score=0.3, max_suggestions=10, dry_run=True)
        
        assert "suggestions" in result
        assert len(result["suggestions"]) >= 1
        assert result["suggestions"][0]["number"] == 1
        assert result["suggestions"][0]["score"] > 0.3
        assert result["dry_run"] is True
        assert result["total_analyzed"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])