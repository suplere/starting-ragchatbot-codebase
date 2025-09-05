import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to sys.path to import backend modules  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from search_tools import CourseSearchTool
from vector_store import SearchResults


class TestCourseSearchTool:
    """Test suite for CourseSearchTool"""

    def test_tool_definition_structure(self):
        """Test that tool definition has correct structure"""
        mock_vector_store = Mock()
        tool = CourseSearchTool(mock_vector_store)
        
        definition = tool.get_tool_definition()
        
        assert definition["name"] == "search_course_content"
        assert "description" in definition
        assert "input_schema" in definition
        assert definition["input_schema"]["type"] == "object"
        assert "properties" in definition["input_schema"]
        assert "query" in definition["input_schema"]["properties"]
        assert definition["input_schema"]["required"] == ["query"]

    def test_execute_with_successful_search(self, mock_vector_store):
        """Test execute method with successful search results"""
        tool = CourseSearchTool(mock_vector_store)
        
        result = tool.execute("What is MCP?")
        
        # Verify vector store was called
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?", 
            course_name=None,
            lesson_number=None
        )
        
        # Verify result contains expected content
        assert "[Introduction to MCP - Lesson 1]" in result
        assert "Sample document content about MCP" in result
        assert len(tool.last_sources) == 1
        
        # Verify source structure
        source = tool.last_sources[0]
        assert source["text"] == "Introduction to MCP - Lesson 1"
        assert source["link"] == "https://example.com/lesson1"

    def test_execute_with_course_filter(self, mock_vector_store):
        """Test execute method with course name filter"""
        tool = CourseSearchTool(mock_vector_store)
        
        result = tool.execute("What is MCP?", course_name="MCP")
        
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?",
            course_name="MCP", 
            lesson_number=None
        )

    def test_execute_with_lesson_filter(self, mock_vector_store):
        """Test execute method with lesson number filter"""
        tool = CourseSearchTool(mock_vector_store)
        
        result = tool.execute("What is MCP?", lesson_number=1)
        
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?",
            course_name=None,
            lesson_number=1
        )

    def test_execute_with_both_filters(self, mock_vector_store):
        """Test execute method with both course and lesson filters"""
        tool = CourseSearchTool(mock_vector_store)
        
        result = tool.execute("What is MCP?", course_name="MCP", lesson_number=1)
        
        mock_vector_store.search.assert_called_once_with(
            query="What is MCP?",
            course_name="MCP",
            lesson_number=1
        )

    def test_execute_with_empty_results(self, mock_empty_vector_store):
        """Test execute method when vector store returns empty results"""
        tool = CourseSearchTool(mock_empty_vector_store)
        
        result = tool.execute("What is XYZ?")
        
        assert result == "No relevant content found."
        assert len(tool.last_sources) == 0

    def test_execute_with_empty_results_and_filters(self, mock_empty_vector_store):
        """Test execute method with empty results and filters"""
        tool = CourseSearchTool(mock_empty_vector_store)
        
        result = tool.execute("What is XYZ?", course_name="Test Course", lesson_number=2)
        
        assert result == "No relevant content found in course 'Test Course' in lesson 2."

    def test_execute_with_vector_store_error(self, mock_failing_vector_store):
        """Test execute method when vector store returns error"""
        tool = CourseSearchTool(mock_failing_vector_store)
        
        result = tool.execute("What is MCP?")
        
        assert result == "Vector store connection failed"
        assert len(tool.last_sources) == 0

    def test_format_results_with_multiple_documents(self):
        """Test _format_results with multiple search results"""
        mock_vector_store = Mock()
        mock_vector_store.get_lesson_link.side_effect = lambda course, lesson: f"https://example.com/{course.lower().replace(' ', '-')}/lesson{lesson}"
        
        tool = CourseSearchTool(mock_vector_store)
        
        # Create mock search results with multiple documents
        search_results = SearchResults(
            documents=[
                "First document about MCP basics",
                "Second document about advanced MCP"
            ],
            metadata=[
                {"course_title": "Introduction to MCP", "lesson_number": 1, "chunk_index": 0},
                {"course_title": "Introduction to MCP", "lesson_number": 2, "chunk_index": 1}
            ],
            distances=[0.1, 0.2]
        )
        
        result = tool._format_results(search_results)
        
        # Verify both documents are formatted correctly
        assert "[Introduction to MCP - Lesson 1]" in result
        assert "First document about MCP basics" in result
        assert "[Introduction to MCP - Lesson 2]" in result 
        assert "Second document about advanced MCP" in result
        
        # Verify sources are tracked correctly
        assert len(tool.last_sources) == 2
        assert tool.last_sources[0]["text"] == "Introduction to MCP - Lesson 1"
        assert tool.last_sources[1]["text"] == "Introduction to MCP - Lesson 2"

    def test_format_results_without_lesson_number(self):
        """Test _format_results with documents that don't have lesson numbers"""
        mock_vector_store = Mock()
        tool = CourseSearchTool(mock_vector_store)
        
        # Create mock search results without lesson numbers
        search_results = SearchResults(
            documents=["Course overview content"],
            metadata=[{"course_title": "Introduction to MCP", "chunk_index": 0}],
            distances=[0.1]
        )
        
        result = tool._format_results(search_results)
        
        # Verify formatting without lesson number
        assert "[Introduction to MCP]" in result
        assert "Course overview content" in result
        
        # Verify source doesn't include lesson number
        assert len(tool.last_sources) == 1
        assert tool.last_sources[0]["text"] == "Introduction to MCP"
        assert tool.last_sources[0]["link"] is None

    def test_source_reset_after_new_search(self, mock_vector_store):
        """Test that sources are reset when performing new searches"""
        tool = CourseSearchTool(mock_vector_store)
        
        # First search
        tool.execute("What is MCP?")
        assert len(tool.last_sources) == 1
        
        # Second search should reset sources
        tool.execute("What is API?")
        assert len(tool.last_sources) == 1  # Should still be 1, but different source

    def test_initialization(self):
        """Test CourseSearchTool initialization"""
        mock_vector_store = Mock()
        tool = CourseSearchTool(mock_vector_store)
        
        assert tool.store == mock_vector_store
        assert tool.last_sources == []