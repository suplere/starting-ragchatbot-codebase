"""
API endpoint tests for the RAG system FastAPI application.

Tests the main API endpoints:
- POST /api/query - Process course queries
- GET /api/courses - Get course statistics  
- POST /api/new-chat - Create new chat sessions
- GET / - Root endpoint
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json


@pytest.mark.api
class TestQueryEndpoint:
    """Test suite for the /api/query endpoint"""
    
    def test_query_with_session_id(self, test_app, sample_query_request, expected_query_response):
        """Test query endpoint with existing session ID"""
        response = test_app.post("/api/query", json=sample_query_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == sample_query_request["session_id"]
        assert isinstance(data["sources"], list)
        assert len(data["sources"]) > 0
    
    def test_query_without_session_id(self, test_app, sample_query_request_no_session):
        """Test query endpoint creates new session when none provided"""
        response = test_app.post("/api/query", json=sample_query_request_no_session)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"  # From mock
    
    def test_query_invalid_json(self, test_app):
        """Test query endpoint with invalid JSON"""
        response = test_app.post("/api/query", data="invalid json")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_query_missing_query_field(self, test_app):
        """Test query endpoint with missing query field"""
        response = test_app.post("/api/query", json={"session_id": "test"})
        
        assert response.status_code == 422  # Validation error
    
    def test_query_empty_query(self, test_app):
        """Test query endpoint with empty query string"""
        response = test_app.post("/api/query", json={"query": ""})
        
        assert response.status_code == 200  # Should still work with empty query
        data = response.json()
        assert "answer" in data
        assert "session_id" in data
    
    def test_query_source_format_legacy(self, test_app, mock_rag_system):
        """Test query endpoint handles legacy string sources"""
        # Mock legacy string sources
        mock_rag_system.query.return_value = (
            "Test answer",
            ["Legacy string source 1", "Legacy string source 2"]
        )
        
        response = test_app.post("/api/query", json={"query": "test query"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["sources"] == ["Legacy string source 1", "Legacy string source 2"]
    
    def test_query_source_format_structured(self, test_app, mock_rag_system):
        """Test query endpoint handles structured dict sources"""
        # Mock structured dict sources
        mock_rag_system.query.return_value = (
            "Test answer",
            [
                {"text": "Structured source 1", "link": "https://example.com/1"},
                {"text": "Structured source 2"}  # No link
            ]
        )
        
        response = test_app.post("/api/query", json={"query": "test query"})
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "Structured source 1"
        assert data["sources"][0]["link"] == "https://example.com/1"
        assert data["sources"][1]["text"] == "Structured source 2"
        assert data["sources"][1]["link"] is None


@pytest.mark.api
class TestCoursesEndpoint:
    """Test suite for the /api/courses endpoint"""
    
    def test_get_course_stats(self, test_app, expected_course_stats):
        """Test courses endpoint returns correct statistics"""
        response = test_app.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_courses" in data
        assert "course_titles" in data
        assert data["total_courses"] == expected_course_stats["total_courses"]
        assert data["course_titles"] == expected_course_stats["course_titles"]
        assert isinstance(data["course_titles"], list)
    
    def test_get_course_stats_empty(self, test_app, mock_rag_system):
        """Test courses endpoint with no courses"""
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }
        
        response = test_app.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []


@pytest.mark.api  
class TestNewChatEndpoint:
    """Test suite for the /api/new-chat endpoint"""
    
    def test_create_new_chat(self, test_app):
        """Test new chat endpoint creates session"""
        response = test_app.post("/api/new-chat")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"
    
    def test_create_multiple_new_chats(self, test_app, mock_rag_system):
        """Test multiple new chat creations return different session IDs"""
        # Mock different session IDs
        session_ids = ["session-1", "session-2", "session-3"]
        mock_rag_system.session_manager.create_session.side_effect = session_ids
        
        responses = []
        for _ in range(3):
            response = test_app.post("/api/new-chat")
            assert response.status_code == 200
            responses.append(response.json()["session_id"])
        
        assert responses == session_ids


@pytest.mark.api
class TestRootEndpoint:
    """Test suite for the root endpoint"""
    
    def test_root_endpoint(self, test_app):
        """Test root endpoint returns expected message"""
        response = test_app.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Course Materials RAG System"


@pytest.mark.api
class TestErrorHandling:
    """Test suite for error handling across endpoints"""
    
    def test_query_rag_system_error(self, test_app, mock_rag_system):
        """Test query endpoint handles RAG system errors"""
        mock_rag_system.query.side_effect = Exception("RAG system error")
        
        response = test_app.post("/api/query", json={"query": "test"})
        
        assert response.status_code == 500
        assert "RAG system error" in response.json()["detail"]
    
    def test_courses_analytics_error(self, test_app, mock_rag_system):
        """Test courses endpoint handles analytics errors"""
        mock_rag_system.get_course_analytics.side_effect = Exception("Analytics error")
        
        response = test_app.get("/api/courses")
        
        assert response.status_code == 500
        assert "Analytics error" in response.json()["detail"]
    
    def test_new_chat_session_error(self, test_app, mock_rag_system):
        """Test new chat endpoint handles session creation errors"""
        mock_rag_system.session_manager.create_session.side_effect = Exception("Session error")
        
        response = test_app.post("/api/new-chat")
        
        assert response.status_code == 500
        assert "Session error" in response.json()["detail"]


@pytest.mark.api
class TestRequestValidation:
    """Test suite for request validation"""
    
    def test_query_request_schema_validation(self, test_app):
        """Test query request validates against schema"""
        # Test with extra fields (should be ignored)
        request_with_extra = {
            "query": "test query",
            "session_id": "test-session",
            "extra_field": "should be ignored"
        }
        
        response = test_app.post("/api/query", json=request_with_extra)
        assert response.status_code == 200
    
    def test_query_request_type_validation(self, test_app):
        """Test query request validates field types"""
        # Test with wrong types
        invalid_requests = [
            {"query": 123},  # query should be string
            {"query": "test", "session_id": 123},  # session_id should be string
            {"query": None},  # query cannot be null
        ]
        
        for invalid_request in invalid_requests:
            response = test_app.post("/api/query", json=invalid_request)
            assert response.status_code == 422


@pytest.mark.api
class TestResponseFormat:
    """Test suite for response format validation"""
    
    def test_query_response_format(self, test_app):
        """Test query response matches expected format"""
        response = test_app.post("/api/query", json={"query": "test"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["answer", "sources", "session_id"]
        for field in required_fields:
            assert field in data
        
        # Check field types
        assert isinstance(data["answer"], str)
        assert isinstance(data["sources"], list) 
        assert isinstance(data["session_id"], str)
    
    def test_courses_response_format(self, test_app):
        """Test courses response matches expected format"""
        response = test_app.get("/api/courses")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_courses" in data
        assert "course_titles" in data
        
        # Check field types
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["course_titles"], list)
        
        # Check all course titles are strings
        for title in data["course_titles"]:
            assert isinstance(title, str)
    
    def test_new_chat_response_format(self, test_app):
        """Test new chat response matches expected format"""
        response = test_app.post("/api/new-chat")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "session_id" in data
        
        # Check field types
        assert isinstance(data["session_id"], str)
        assert len(data["session_id"]) > 0


@pytest.mark.integration
class TestEndpointIntegration:
    """Integration tests across multiple endpoints"""
    
    def test_new_chat_to_query_flow(self, test_app, mock_rag_system):
        """Test creating new chat then using it for query"""
        # Mock different session IDs for clear test
        mock_rag_system.session_manager.create_session.return_value = "integration-test-session"
        
        # Create new chat
        chat_response = test_app.post("/api/new-chat")
        assert chat_response.status_code == 200
        session_id = chat_response.json()["session_id"]
        
        # Use session for query
        query_response = test_app.post("/api/query", json={
            "query": "test integration",
            "session_id": session_id
        })
        assert query_response.status_code == 200
        assert query_response.json()["session_id"] == session_id
    
    def test_courses_and_query_consistency(self, test_app, mock_rag_system):
        """Test that courses endpoint and query results are consistent"""
        # Get course stats
        courses_response = test_app.get("/api/courses")
        courses_data = courses_response.json()
        
        # Query should work when courses exist
        query_response = test_app.post("/api/query", json={"query": "test"})
        
        if courses_data["total_courses"] > 0:
            assert query_response.status_code == 200
            # Should have sources when courses exist
            assert len(query_response.json()["sources"]) > 0
        else:
            # Even with no courses, query should still work (general knowledge)
            assert query_response.status_code == 200