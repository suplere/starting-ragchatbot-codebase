import pytest
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to sys.path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai_generator import AIGenerator
from search_tools import ToolManager, CourseSearchTool


class TestAIGenerator:
    """Test suite for AIGenerator tool calling functionality"""

    def test_initialization(self):
        """Test AIGenerator initialization"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        assert generator.model == "claude-3-haiku-20240307"
        assert generator.base_params["model"] == "claude-3-haiku-20240307"
        assert generator.base_params["temperature"] == 0
        assert generator.base_params["max_tokens"] == 800

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_without_tools(self, mock_anthropic_class, mock_anthropic_client):
        """Test generate_response without tool usage"""
        mock_anthropic_class.return_value = mock_anthropic_client
        
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        response = generator.generate_response("What is Python?")
        
        # Verify client was called correctly
        mock_anthropic_client.messages.create.assert_called_once()
        call_args = mock_anthropic_client.messages.create.call_args[1]
        
        assert call_args["model"] == "claude-3-haiku-20240307"
        assert call_args["messages"][0]["content"] == "What is Python?"
        assert "tools" not in call_args
        assert response == "This is a test response"

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_conversation_history(self, mock_anthropic_class, mock_anthropic_client):
        """Test generate_response with conversation history"""
        mock_anthropic_class.return_value = mock_anthropic_client
        
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        history = "User: Hello\nAssistant: Hi there!"
        
        response = generator.generate_response("What is Python?", conversation_history=history)
        
        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert history in call_args["system"]

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_tools_no_tool_use(self, mock_anthropic_class, mock_anthropic_client):
        """Test generate_response with tools available but no tool use"""
        mock_anthropic_class.return_value = mock_anthropic_client
        
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        # Mock tool definitions
        tools = [{
            "name": "search_course_content",
            "description": "Search course materials",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}
        }]
        
        response = generator.generate_response("What is Python?", tools=tools)
        
        call_args = mock_anthropic_client.messages.create.call_args[1]
        assert "tools" in call_args
        assert call_args["tools"] == tools
        assert call_args["tool_choice"] == {"type": "auto"}

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_tool_use(self, mock_anthropic_class, mock_anthropic_client_with_tools):
        """Test generate_response when AI decides to use tools"""
        mock_anthropic_class.return_value = mock_anthropic_client_with_tools
        
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        # Create mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search results about MCP"
        
        tools = [{
            "name": "search_course_content",
            "description": "Search course materials",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}
        }]
        
        response = generator.generate_response(
            "What is MCP?",
            tools=tools,
            tool_manager=mock_tool_manager
        )
        
        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="test query"
        )
        
        # Verify final response
        assert response == "Based on the search results, here's the answer"
        
        # Verify two API calls were made (initial + after tool execution)
        assert mock_anthropic_client_with_tools.messages.create.call_count == 2

    def test_handle_tool_execution_flow(self):
        """Test _handle_tool_execution method directly"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        # Mock initial response with tool use
        mock_initial_response = Mock()
        mock_tool_content = Mock()
        mock_tool_content.type = "tool_use"
        mock_tool_content.name = "search_course_content"
        mock_tool_content.input = {"query": "test query"}
        mock_tool_content.id = "tool_123"
        
        mock_initial_response.content = [mock_tool_content]
        
        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Tool execution result"
        
        # Mock base parameters
        base_params = {
            "messages": [{"role": "user", "content": "What is MCP?"}],
            "system": "You are a helpful assistant"
        }
        
        # Mock the final API call
        with patch.object(generator.client, 'messages') as mock_messages:
            mock_final_response = Mock()
            mock_final_response.content = [Mock(text="Final response")]
            mock_messages.create.return_value = mock_final_response
            
            result = generator._handle_tool_execution(
                mock_initial_response,
                base_params,
                mock_tool_manager
            )
        
        # Verify tool was executed
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="test query"
        )
        
        # Verify final API call was made
        mock_messages.create.assert_called_once()
        final_call_args = mock_messages.create.call_args[1]
        
        # Verify message structure
        assert len(final_call_args["messages"]) == 3  # original + assistant + tool result
        assert final_call_args["messages"][1]["role"] == "assistant"
        assert final_call_args["messages"][2]["role"] == "user"
        
        assert result == "Final response"

    def test_handle_tool_execution_multiple_tools(self):
        """Test _handle_tool_execution with multiple tool calls"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        # Mock initial response with multiple tool uses
        mock_initial_response = Mock()
        mock_tool_content_1 = Mock()
        mock_tool_content_1.type = "tool_use"
        mock_tool_content_1.name = "search_course_content"
        mock_tool_content_1.input = {"query": "test query 1"}
        mock_tool_content_1.id = "tool_123"
        
        mock_tool_content_2 = Mock()
        mock_tool_content_2.type = "tool_use"  
        mock_tool_content_2.name = "get_course_outline"
        mock_tool_content_2.input = {"course_title": "MCP"}
        mock_tool_content_2.id = "tool_456"
        
        mock_initial_response.content = [mock_tool_content_1, mock_tool_content_2]
        
        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]
        
        base_params = {
            "messages": [{"role": "user", "content": "What is MCP?"}],
            "system": "You are a helpful assistant"
        }
        
        # Mock final API call
        with patch.object(generator.client, 'messages') as mock_messages:
            mock_final_response = Mock()
            mock_final_response.content = [Mock(text="Final response")]
            mock_messages.create.return_value = mock_final_response
            
            result = generator._handle_tool_execution(
                mock_initial_response,
                base_params,
                mock_tool_manager
            )
        
        # Verify both tools were executed
        assert mock_tool_manager.execute_tool.call_count == 2
        
        # Verify tool results are included in final message
        final_call_args = mock_messages.create.call_args[1]
        tool_results = final_call_args["messages"][2]["content"]
        
        assert len(tool_results) == 2
        assert tool_results[0]["tool_use_id"] == "tool_123"
        assert tool_results[0]["content"] == "Result 1"
        assert tool_results[1]["tool_use_id"] == "tool_456"
        assert tool_results[1]["content"] == "Result 2"