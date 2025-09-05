import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

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
def test_config():
    """Test configuration"""
    return config