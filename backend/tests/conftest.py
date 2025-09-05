import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
from fastapi.testclient import TestClient
from typing import Generator

# Add parent directory to sys.path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models import Course, Lesson, CourseChunk
from vector_store import SearchResults
from config import config

@pytest.fixture
def sample_course():
    """Sample course data for testing"""
    return Course(
        title="Introduction to MCP",
        instructor="Test Instructor", 
        course_link="https://example.com/course",
        lessons=[
            Lesson(lesson_number=1, title="Getting Started", lesson_link="https://example.com/lesson1"),
            Lesson(lesson_number=2, title="Basic Concepts", lesson_link="https://example.com/lesson2")
        ]
    )

@pytest.fixture  
def sample_chunks():
    """Sample course chunks for testing"""
    return [
        CourseChunk(
            content="This is lesson 1 content about MCP basics and introduction.",
            course_title="Introduction to MCP",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="This lesson covers advanced MCP concepts and implementation details.",
            course_title="Introduction to MCP", 
            lesson_number=2,
            chunk_index=1
        )
    ]

@pytest.fixture
def mock_vector_store():
    """Mock vector store for testing"""
    mock = Mock()
    
    # Mock successful search results
    mock.search.return_value = SearchResults(
        documents=["Sample document content about MCP"],
        metadata=[{
            "course_title": "Introduction to MCP",
            "lesson_number": 1,
            "chunk_index": 0
        }],
        distances=[0.1],
        error=None
    )
    
    # Mock course name resolution
    mock._resolve_course_name.return_value = "Introduction to MCP"
    
    # Mock lesson link retrieval
    mock.get_lesson_link.return_value = "https://example.com/lesson1"
    
    return mock

@pytest.fixture  
def mock_empty_vector_store():
    """Mock vector store that returns empty results"""
    mock = Mock()
    
    # Mock empty search results
    mock.search.return_value = SearchResults(
        documents=[],
        metadata=[], 
        distances=[],
        error=None
    )
    
    # Mock failed course name resolution
    mock._resolve_course_name.return_value = None
    
    return mock

@pytest.fixture
def mock_failing_vector_store():
    """Mock vector store that returns errors"""
    mock = Mock()
    
    # Mock search with error
    mock.search.return_value = SearchResults(
        documents=[],
        metadata=[],
        distances=[], 
        error="Vector store connection failed"
    )
    
    # Mock failed course name resolution
    mock._resolve_course_name.return_value = None
    
    return mock

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client"""
    mock = Mock()
    
    # Mock successful message creation
    mock_response = Mock()
    mock_response.content = [Mock(text="This is a test response")]
    mock_response.stop_reason = "end_turn"
    
    mock.messages.create.return_value = mock_response
    
    return mock

@pytest.fixture  
def mock_anthropic_client_with_tools():
    """Mock Anthropic API client that uses tools"""
    mock = Mock()
    
    # Mock tool use response
    mock_tool_response = Mock()
    mock_tool_content = Mock()
    mock_tool_content.type = "tool_use"
    mock_tool_content.name = "search_course_content"
    mock_tool_content.input = {"query": "test query"}
    mock_tool_content.id = "tool_call_123"
    
    mock_tool_response.content = [mock_tool_content]
    mock_tool_response.stop_reason = "tool_use"
    
    # Mock final response after tool execution
    mock_final_response = Mock()
    mock_final_response.content = [Mock(text="Based on the search results, here's the answer")]
    mock_final_response.stop_reason = "end_turn"
    
    mock.messages.create.side_effect = [mock_tool_response, mock_final_response]
    
    return mock

@pytest.fixture
def mock_anthropic_client_sequential():
    """Mock Anthropic API client that demonstrates sequential tool calling"""
    mock = Mock()
    
    # Mock first round - tool use
    mock_round1_response = Mock()
    mock_tool_content1 = Mock()
    mock_tool_content1.type = "tool_use"
    mock_tool_content1.name = "get_course_outline"
    mock_tool_content1.input = {"course_title": "MCP Basics"}
    mock_tool_content1.id = "tool_call_round1"
    
    mock_round1_response.content = [mock_tool_content1]
    mock_round1_response.stop_reason = "tool_use"
    
    # Mock second round - another tool use
    mock_round2_response = Mock()
    mock_tool_content2 = Mock()
    mock_tool_content2.type = "tool_use"
    mock_tool_content2.name = "search_course_content"
    mock_tool_content2.input = {"query": "lesson 4 content"}
    mock_tool_content2.id = "tool_call_round2"
    
    mock_round2_response.content = [mock_tool_content2]
    mock_round2_response.stop_reason = "tool_use"
    
    # Mock final response without tool use
    mock_final_response = Mock()
    mock_final_response.content = [Mock(text="Based on both searches, here's the comprehensive answer")]
    mock_final_response.stop_reason = "end_turn"
    
    # Set up side effects for multiple API calls
    mock.messages.create.side_effect = [mock_round1_response, mock_round2_response, mock_final_response]
    
    return mock

@pytest.fixture
def test_config():
    """Test configuration"""
    return config

# API Testing Fixtures

@pytest.fixture
def mock_rag_system():
    """Mock RAG system for API testing"""
    mock = Mock()
    
    # Mock session manager
    mock_session_manager = Mock()
    mock_session_manager.create_session.return_value = "test-session-123"
    mock.session_manager = mock_session_manager
    
    # Mock query method
    mock.query.return_value = (
        "This is a test response about MCP concepts.",
        [{"text": "Sample source content", "link": "https://example.com/lesson1"}]
    )
    
    # Mock course analytics
    mock.get_course_analytics.return_value = {
        "total_courses": 3,
        "course_titles": ["Introduction to MCP", "Advanced MCP", "MCP Best Practices"]
    }
    
    return mock

@pytest.fixture
def test_app(mock_rag_system) -> Generator[TestClient, None, None]:
    """Create test FastAPI app with mocked dependencies"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional, Union
    
    # Create test app (avoiding static file mount issues)
    app = FastAPI(title="Test Course Materials RAG System")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import models from the actual app
    from app import QueryRequest, QueryResponse, CourseStats, NewChatResponse, SourceData
    
    # Add API endpoints with mocked RAG system
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id or mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            
            formatted_sources = []
            for source in sources:
                if isinstance(source, dict) and 'text' in source:
                    formatted_sources.append(SourceData(
                        text=source['text'],
                        link=source.get('link')
                    ))
                else:
                    formatted_sources.append(source)
            
            return QueryResponse(
                answer=answer,
                sources=formatted_sources,
                session_id=session_id
            )
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/new-chat", response_model=NewChatResponse)
    async def create_new_chat():
        try:
            session_id = mock_rag_system.session_manager.create_session()
            return NewChatResponse(session_id=session_id)
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/")
    async def read_root():
        return {"message": "Course Materials RAG System"}
    
    with TestClient(app) as client:
        yield client

@pytest.fixture
def sample_query_request():
    """Sample query request for API testing"""
    return {
        "query": "What is MCP and how does it work?",
        "session_id": "test-session-123"
    }

@pytest.fixture
def sample_query_request_no_session():
    """Sample query request without session ID"""
    return {
        "query": "Explain the basics of MCP implementation"
    }

@pytest.fixture
def expected_query_response():
    """Expected query response structure"""
    return {
        "answer": "This is a test response about MCP concepts.",
        "sources": [
            {
                "text": "Sample source content",
                "link": "https://example.com/lesson1"
            }
        ],
        "session_id": "test-session-123"
    }

@pytest.fixture
def expected_course_stats():
    """Expected course statistics response"""
    return {
        "total_courses": 3,
        "course_titles": ["Introduction to MCP", "Advanced MCP", "MCP Best Practices"]
    }