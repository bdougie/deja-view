#!/usr/bin/env python3
"""
SIMPLIFIED GITHUB SERVICE TESTS
No async, no external calls, no hanging
Maximum duration: 5 seconds total
"""

import pytest
from unittest.mock import Mock, patch
from github_similarity_service import Issue, Discussion, SimilarityService


class TestServiceInitialization:
    """Test service initialization with mocked dependencies"""
    
    @patch.dict('os.environ', {
        'CHROMA_API_KEY': 'test',
        'CHROMA_TENANT': 'test',
        'GITHUB_TOKEN': 'test'
    })
    @patch('github_similarity_service.chromadb.CloudClient')
    def test_init_with_valid_env(self, mock_client):
        """Test initialization with valid environment"""
        mock_client.return_value.get_collection.return_value = Mock()
        
        service = SimilarityService()
        assert service.api_key == 'test'
        assert service.tenant == 'test'
        mock_client.assert_called_once()
    
    @patch.dict('os.environ', {}, clear=True)
    def test_init_missing_api_key(self):
        """Test initialization fails without API key"""
        with pytest.raises(ValueError, match="CHROMA_API_KEY"):
            SimilarityService()


class TestDataProcessing:
    """Test pure data processing functions"""
    
    def test_create_issue_document(self):
        """Test document creation from issue"""
        service = Mock(spec=SimilarityService)
        service._create_document_text = SimilarityService._create_document_text.__get__(service)
        
        issue = Issue(
            number=1,
            title="Test",
            body="Body",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="http://test.com/1",
            labels=["bug"]
        )
        
        doc = service._create_document_text(issue)
        assert "Title: Test" in doc
        assert "bug" in doc
    
    def test_label_extraction(self):
        """Test label extraction from issue"""
        issue = Issue(
            number=1,
            title="Test",
            body="Body",
            state="open",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
            url="http://test.com/1",
            labels=["question", "help", "urgent"]
        )
        
        assert len(issue.labels) == 3
        assert "question" in issue.labels
        assert "help" in issue.labels


class TestMockedOperations:
    """Test operations with fully mocked dependencies"""
    
    @patch.dict('os.environ', {
        'CHROMA_API_KEY': 'test',
        'CHROMA_TENANT': 'test'
    })
    @patch('github_similarity_service.chromadb.CloudClient')
    def test_clear_collection(self, mock_client):
        """Test clearing collection with mocked client"""
        mock_collection = Mock()
        mock_client.return_value.get_collection.return_value = mock_collection
        
        service = SimilarityService()
        service.client = mock_client.return_value
        service.client.delete_collection = Mock()
        service.client.create_collection = Mock(return_value=Mock())
        
        result = service.clear_all()
        assert "cleared" in result["message"]
        service.client.delete_collection.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])