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

    def test_single_round_behavior_unchanged(self):
        """Test that simple queries still work in single round (backward compatibility)"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        # Mock single round without tool use
        with patch.object(generator.client, 'messages') as mock_messages:
            mock_response = Mock()
            mock_response.content = [Mock(text="Python is a programming language")]
            mock_response.stop_reason = "end_turn"
            mock_messages.create.return_value = mock_response
            
            result = generator.generate_response("What is Python?")
            
            # Verify single API call was made
            mock_messages.create.assert_called_once()
            call_args = mock_messages.create.call_args[1]
            
            # Verify message structure is same as before
            assert call_args["messages"][0]["content"] == "What is Python?"
            assert "tools" not in call_args
            assert result == "Python is a programming language"
    
    def test_single_round_tool_use_unchanged(self):
        """Test that single tool use still works as before (backward compatibility)"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Search results about MCP"
        
        tools = [{"name": "search_course_content", "description": "Search course materials"}]
        
        # Mock single round with tool use followed by final response
        with patch.object(generator.client, 'messages') as mock_messages:
            # First response with tool use
            mock_tool_response = Mock()
            mock_tool_content = Mock()
            mock_tool_content.type = "tool_use"
            mock_tool_content.name = "search_course_content"
            mock_tool_content.input = {"query": "MCP basics"}
            mock_tool_content.id = "tool_123"
            mock_tool_response.content = [mock_tool_content]
            mock_tool_response.stop_reason = "tool_use"
            
            # Final response after tool execution
            mock_final_response = Mock()
            mock_final_response.content = [Mock(text="Based on search, MCP is...")]
            mock_final_response.stop_reason = "end_turn"
            
            mock_messages.create.side_effect = [mock_tool_response, mock_final_response]
            
            result = generator.generate_response("What is MCP?", tools=tools, tool_manager=mock_tool_manager)
            
            # Verify tool was executed
            mock_tool_manager.execute_tool.assert_called_once_with("search_course_content", query="MCP basics")
            
            # Verify two API calls were made (same as before)
            assert mock_messages.create.call_count == 2
            assert result == "Based on search, MCP is..."
    
    def test_sequential_tool_calling_two_rounds(self):
        """Test sequential tool calling across two rounds"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        # Mock tool manager
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = [
            "Course outline: Lesson 4 - Authentication Basics",
            "Authentication content details..."
        ]
        
        tools = [
            {"name": "get_course_outline", "description": "Get course outline"},
            {"name": "search_course_content", "description": "Search course content"}
        ]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # Round 1 - get course outline
            mock_round1_response = Mock()
            mock_tool_content1 = Mock()
            mock_tool_content1.type = "tool_use"
            mock_tool_content1.name = "get_course_outline"
            mock_tool_content1.input = {"course_title": "MCP Basics"}
            mock_tool_content1.id = "tool_round1"
            mock_round1_response.content = [mock_tool_content1]
            mock_round1_response.stop_reason = "tool_use"
            
            # Round 2 - search for specific content
            mock_round2_response = Mock()
            mock_tool_content2 = Mock()
            mock_tool_content2.type = "tool_use"
            mock_tool_content2.name = "search_course_content"
            mock_tool_content2.input = {"query": "lesson 4 authentication"}
            mock_tool_content2.id = "tool_round2"
            mock_round2_response.content = [mock_tool_content2]
            mock_round2_response.stop_reason = "tool_use"
            
            # Final response without tools
            mock_final_response = Mock()
            mock_final_response.content = [Mock(text="Combined response from both searches")]
            mock_final_response.stop_reason = "end_turn"
            
            mock_messages.create.side_effect = [mock_round1_response, mock_round2_response, mock_final_response]
            
            result = generator.generate_response(
                "What is in lesson 4 of MCP Basics course?", 
                tools=tools, 
                tool_manager=mock_tool_manager
            )
            
            # Verify both tools were executed
            assert mock_tool_manager.execute_tool.call_count == 2
            mock_tool_manager.execute_tool.assert_any_call("get_course_outline", course_title="MCP Basics")
            mock_tool_manager.execute_tool.assert_any_call("search_course_content", query="lesson 4 authentication")
            
            # Verify three API calls were made (2 rounds + final)
            assert mock_messages.create.call_count == 3
            assert result == "Combined response from both searches"
    
    def test_sequential_calling_stops_when_no_tools_needed(self):
        """Test that sequential calling stops when Claude doesn't need more tools"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "Complete course outline"
        
        tools = [{"name": "get_course_outline", "description": "Get course outline"}]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # Round 1 - tool use
            mock_round1_response = Mock()
            mock_tool_content = Mock()
            mock_tool_content.type = "tool_use"
            mock_tool_content.name = "get_course_outline"
            mock_tool_content.input = {"course_title": "Python Basics"}
            mock_tool_content.id = "tool_round1"
            mock_round1_response.content = [mock_tool_content]
            mock_round1_response.stop_reason = "tool_use"
            
            # Round 2 - no tool use, direct answer
            mock_round2_response = Mock()
            mock_round2_response.content = [Mock(text="Here's the complete course outline")]
            mock_round2_response.stop_reason = "end_turn"
            
            mock_messages.create.side_effect = [mock_round1_response, mock_round2_response]
            
            result = generator.generate_response(
                "Show me the Python Basics course outline",
                tools=tools,
                tool_manager=mock_tool_manager
            )
            
            # Verify only one tool was executed
            mock_tool_manager.execute_tool.assert_called_once_with("get_course_outline", course_title="Python Basics")
            
            # Verify two API calls (round 1 + round 2, no final needed)
            assert mock_messages.create.call_count == 2
            assert result == "Here's the complete course outline"
    
    def test_max_rounds_termination(self):
        """Test that sequential calling stops after 2 rounds maximum"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = ["Result 1", "Result 2"]
        
        tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # Mock responses that always want to use tools
            mock_tool_response1 = Mock()
            mock_tool_content1 = Mock()
            mock_tool_content1.type = "tool_use"
            mock_tool_content1.name = "search_course_content"
            mock_tool_content1.input = {"query": "query 1"}
            mock_tool_content1.id = "tool_1"
            mock_tool_response1.content = [mock_tool_content1]
            mock_tool_response1.stop_reason = "tool_use"
            
            mock_tool_response2 = Mock()
            mock_tool_content2 = Mock()
            mock_tool_content2.type = "tool_use"
            mock_tool_content2.name = "search_course_content"
            mock_tool_content2.input = {"query": "query 2"}
            mock_tool_content2.id = "tool_2"
            mock_tool_response2.content = [mock_tool_content2]
            mock_tool_response2.stop_reason = "tool_use"
            
            # Final synthesis response (forced after 2 rounds)
            mock_final_response = Mock()
            mock_final_response.content = [Mock(text="Final answer after 2 rounds")]
            mock_final_response.stop_reason = "end_turn"
            
            mock_messages.create.side_effect = [mock_tool_response1, mock_tool_response2, mock_final_response]
            
            result = generator.generate_response(
                "Complex query requiring multiple searches",
                tools=tools,
                tool_manager=mock_tool_manager
            )
            
            # Verify exactly 2 tool calls (respecting max rounds)
            assert mock_tool_manager.execute_tool.call_count == 2
            
            # Verify exactly 3 API calls (round 1, round 2, final)
            assert mock_messages.create.call_count == 3
            assert result == "Final answer after 2 rounds"
    
    def test_error_handling_first_round_api_failure(self):
        """Test graceful handling of API failures in first round"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        import anthropic
        
        mock_tool_manager = Mock()
        tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # Mock API failure
            mock_request = Mock()
            mock_messages.create.side_effect = anthropic.APIError("API Error", request=mock_request, body={})
            
            result = generator.generate_response(
                "Search for something",
                tools=tools,
                tool_manager=mock_tool_manager
            )
            
            # Verify error message is returned
            assert "technical issue" in result.lower()
            assert "try your question again" in result.lower()
            
            # Verify no tools were executed
            mock_tool_manager.execute_tool.assert_not_called()
    
    def test_error_handling_second_round_api_failure(self):
        """Test graceful handling of API failures in second round"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        import anthropic
        
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.return_value = "First tool result"
        tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # First round succeeds
            mock_round1_response = Mock()
            mock_tool_content = Mock()
            mock_tool_content.type = "tool_use"
            mock_tool_content.name = "search_course_content"
            mock_tool_content.input = {"query": "test"}
            mock_tool_content.id = "tool_1"
            mock_round1_response.content = [mock_tool_content]
            mock_round1_response.stop_reason = "tool_use"
            
            # Second round fails
            mock_request = Mock()
            mock_messages.create.side_effect = [mock_round1_response, anthropic.APIError("API Error", request=mock_request, body={})]
            
            result = generator.generate_response(
                "Complex search",
                tools=tools,
                tool_manager=mock_tool_manager
            )
            
            # Verify contextual error message
            assert "found some relevant information" in result.lower()
            assert "technical issues" in result.lower()
            
            # Verify first tool was executed but not second
            mock_tool_manager.execute_tool.assert_called_once()
    
    def test_error_handling_tool_execution_failure(self):
        """Test graceful handling of tool execution failures"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        mock_tool_manager = Mock()
        mock_tool_manager.execute_tool.side_effect = Exception("Tool execution failed")
        tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # Mock tool use request
            mock_tool_response = Mock()
            mock_tool_content = Mock()
            mock_tool_content.type = "tool_use"
            mock_tool_content.name = "search_course_content"
            mock_tool_content.input = {"query": "test"}
            mock_tool_content.id = "tool_1"
            mock_tool_response.content = [mock_tool_content]
            mock_tool_response.stop_reason = "tool_use"
            
            # Mock final response after tool error
            mock_final_response = Mock()
            mock_final_response.content = [Mock(text="Response handling tool error gracefully")]
            mock_final_response.stop_reason = "end_turn"
            
            mock_messages.create.side_effect = [mock_tool_response, mock_final_response]
            
            result = generator.generate_response(
                "Search for something",
                tools=tools,
                tool_manager=mock_tool_manager
            )
            
            # Verify response is returned despite tool error
            assert result == "Response handling tool error gracefully"
            
            # Verify tool was attempted
            mock_tool_manager.execute_tool.assert_called_once()
            
            # Verify second API call was made (Claude continues despite tool error)
            assert mock_messages.create.call_count == 2
            
            # Verify tool error was included in conversation context
            final_call_args = mock_messages.create.call_args[1]
            messages = final_call_args["messages"]
            tool_result_message = messages[2]["content"][0]  # First tool result
            assert "Error executing tool" in tool_result_message["content"]
            assert "Tool execution failed" in tool_result_message["content"]
    
    def test_error_handling_no_tool_manager(self):
        """Test behavior when tool manager is not provided but tools are available"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # Mock tool use request
            mock_tool_response = Mock()
            mock_tool_content = Mock()
            mock_tool_content.type = "tool_use"
            mock_tool_content.name = "search_course_content"
            mock_tool_content.input = {"query": "test"}
            mock_tool_content.id = "tool_1"
            mock_tool_response.content = [mock_tool_content]
            mock_tool_response.stop_reason = "tool_use"
            
            mock_messages.create.return_value = mock_tool_response
            
            result = generator.generate_response(
                "Search for something",
                tools=tools,
                tool_manager=None  # No tool manager provided
            )
            
            # Verify Claude's tool use response is returned directly
            assert result == mock_tool_response.content[0].text
            
            # Verify only one API call was made
            mock_messages.create.assert_called_once()
    
    def test_termination_on_no_tool_use_in_first_round(self):
        """Test that process terminates when Claude doesn't use tools in first round"""
        generator = AIGenerator("test_api_key", "claude-3-haiku-20240307")
        
        mock_tool_manager = Mock()
        tools = [{"name": "search_course_content", "description": "Search content"}]
        
        with patch.object(generator.client, 'messages') as mock_messages:
            # Mock direct response without tool use
            mock_response = Mock()
            mock_response.content = [Mock(text="Direct answer without using tools")]
            mock_response.stop_reason = "end_turn"
            
            mock_messages.create.return_value = mock_response
            
            result = generator.generate_response(
                "Simple question",
                tools=tools,
                tool_manager=mock_tool_manager
            )
            
            # Verify direct response
            assert result == "Direct answer without using tools"
            
            # Verify only one API call was made
            mock_messages.create.assert_called_once()
            
            # Verify no tools were executed
            mock_tool_manager.execute_tool.assert_not_called()