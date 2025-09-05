from typing import Any, Dict, List, Optional

import anthropic


class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""

    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to comprehensive search tools for course information.

Tool Usage Guidelines:
- **Course content search**: Use search_course_content for questions about specific course materials or detailed educational content
- **Course outline queries**: Use get_course_outline for questions about course structure, lesson lists, or course overview
- **Sequential tool usage**: You can make up to 2 tool calls across multiple rounds for complex queries
- **Multi-round scenarios**: First search/query broadly, then use additional tools if initial results need refinement or different information
- **Single-round scenarios**: Use the most appropriate tool directly for straightforward questions
- Synthesize all tool results into accurate, fact-based responses
- If tools yield no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course content questions**: Use search_course_content tool first, then answer
- **Course outline/structure questions**: Use get_course_outline tool first, then answer
- **Complex comparison/multi-part questions**: Use sequential tool calls to gather all necessary information
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool explanations, or question-type analysis
 - Do not mention "based on the search results" or "according to the outline"

For outline queries, ensure you include:
- Course title and instructor (if available)
- Course link (if available)  
- Complete lesson list with lesson numbers and titles
- Total lesson count

All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

        # Pre-build base API parameters
        self.base_params = {"model": self.model, "temperature": 0, "max_tokens": 800}

    def generate_response(
        self,
        query: str,
        conversation_history: Optional[str] = None,
        tools: Optional[List] = None,
        tool_manager=None,
    ) -> str:
        """
        Generate AI response with sequential tool usage support (max 2 rounds).

        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools

        Returns:
            Generated response as string
        """

        # Build system content efficiently
        system_content = self._build_system_content(conversation_history)

        # Initialize round tracking
        round_count = 0
        max_rounds = 2
        messages = [{"role": "user", "content": query}]

        # Sequential round loop
        while round_count < max_rounds:
            round_count += 1

            try:
                # Execute current round
                response, should_continue, updated_messages = self._execute_round(
                    messages, system_content, tools, tool_manager, round_count
                )

                # Check termination conditions
                if not should_continue:
                    return response

                # Update messages for next round
                messages = updated_messages

            except Exception as e:
                # Handle errors gracefully
                return self._handle_error(e, round_count, messages, system_content)

        # Should not reach here, but return last response as fallback
        return response

    def _execute_round(
        self,
        messages: List[Dict],
        system_content: str,
        tools: Optional[List],
        tool_manager,
        round_num: int,
    ) -> tuple[str, bool, List[Dict]]:
        """
        Execute a single round of Claude interaction.

        Args:
            messages: Current message history
            system_content: System prompt content
            tools: Available tools
            tool_manager: Manager to execute tools
            round_num: Current round number

        Returns:
            Tuple of (response_text, should_continue, updated_messages)
        """
        # Prepare API call parameters
        api_params = {
            **self.base_params,
            "messages": messages.copy(),
            "system": system_content,
        }

        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}

        # Get response from Claude
        response = self.client.messages.create(**api_params)

        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use" and tool_manager:
            # Execute tools and update message history
            updated_messages = self._process_tool_calls(
                response, messages, tool_manager
            )

            # Determine if should continue to next round
            should_continue = round_num < 2  # Continue if under max rounds

            if not should_continue:
                # This is the final round - get Claude's final response
                final_response = self._get_final_response(
                    updated_messages, system_content, tools, tool_manager
                )
                return final_response, False, updated_messages

            # Continue to next round with updated context
            return "", True, updated_messages

        # No tool use - return direct response and terminate
        return response.content[0].text, False, messages

    def _build_system_content(self, conversation_history: Optional[str]) -> str:
        """Build system content with optional conversation history."""
        return (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history
            else self.SYSTEM_PROMPT
        )

    def _process_tool_calls(
        self, response, messages: List[Dict], tool_manager
    ) -> List[Dict]:
        """
        Process tool calls from Claude's response and update message history.

        Args:
            response: Claude's response containing tool use requests
            messages: Current message history
            tool_manager: Manager to execute tools

        Returns:
            Updated message history with tool results
        """
        # Start with existing messages
        updated_messages = messages.copy()

        # Add AI's tool use response
        updated_messages.append({"role": "assistant", "content": response.content})

        # Execute all tool calls and collect results
        tool_results = []
        for content_block in response.content:
            if content_block.type == "tool_use":
                try:
                    tool_result = tool_manager.execute_tool(
                        content_block.name, **content_block.input
                    )

                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": tool_result,
                        }
                    )
                except Exception as e:
                    # Handle tool execution errors
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": f"Error executing tool: {str(e)}",
                        }
                    )

        # Add tool results as single message
        if tool_results:
            updated_messages.append({"role": "user", "content": tool_results})

        return updated_messages

    def _get_final_response(
        self,
        messages: List[Dict],
        system_content: str,
        tools: Optional[List],
        tool_manager=None,
    ) -> str:
        """
        Get Claude's final response after tool execution.

        Args:
            messages: Message history including tool results
            system_content: System prompt content
            tools: Available tools (kept for potential final tool use)

        Returns:
            Final response text
        """
        # Prepare final API call with tools still available
        final_params = {
            **self.base_params,
            "messages": messages,
            "system": system_content,
        }

        # Keep tools available for potential final use
        if tools:
            final_params["tools"] = tools
            final_params["tool_choice"] = {"type": "auto"}

        # Get final response
        final_response = self.client.messages.create(**final_params)

        # If Claude still wants to use tools in final response, execute them
        if final_response.stop_reason == "tool_use" and tools and tool_manager:
            # Execute final tool calls
            final_messages = self._process_tool_calls(
                final_response, messages, tool_manager
            )

            # Get response without tools for final synthesis
            synthesis_params = {
                **self.base_params,
                "messages": final_messages,
                "system": system_content,
            }

            synthesis_response = self.client.messages.create(**synthesis_params)
            return synthesis_response.content[0].text

        return final_response.content[0].text

    def _handle_error(
        self,
        error: Exception,
        round_num: int,
        messages: List[Dict],
        system_content: str,
    ) -> str:
        """
        Handle errors gracefully with appropriate fallback responses.

        Args:
            error: The exception that occurred
            round_num: Current round number when error happened
            messages: Current message history
            system_content: System prompt content

        Returns:
            Fallback response text
        """
        import anthropic

        # API-related errors
        if isinstance(error, anthropic.APIError):
            if round_num == 1:
                # First round API failure - return general error message
                return "I encountered a technical issue while processing your request. Please try your question again."
            else:
                # Second round API failure - we may have some context from first round
                return "I found some relevant information but encountered technical issues gathering additional details. Please try rephrasing your question."

        # Tool execution or other errors
        if round_num == 1:
            # First round tool failure - try Claude without tools as fallback
            try:
                fallback_params = {
                    **self.base_params,
                    "messages": messages,
                    "system": system_content,
                }

                fallback_response = self.client.messages.create(**fallback_params)
                return fallback_response.content[0].text

            except Exception:
                # Even fallback failed
                return "I'm experiencing technical difficulties. Please try your question again."
        else:
            # Second round failure - return partial information message
            return "I found some relevant information but encountered issues gathering additional details. Please try rephrasing your question or asking more specific questions."
