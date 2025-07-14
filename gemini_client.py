import google.generativeai as genai
import json

# Import configuration and tool declarations/functions
from config import app_config

from tools.weather import weather_tool_declaration, tool_functions as weather_tool_functions
from tools.calendar import calendar_tool_declaration, tool_functions as calendar_tool_functions
from tools.search import search_tool_declaration, tool_functions as search_tool_functions


class GeminiClient:
    """
    Manages the interaction with the Google Gemini API, including chat history
    and tool function calling.
    """
    def __init__(self):
        # Configure Gemini API with key from config
        genai.configure(api_key=app_config.GEMINI_API_KEY)

        # Define all available tools for Gemini
        self.available_gemini_tools = [
            weather_tool_declaration,
            calendar_tool_declaration,
            search_tool_declaration
            # Add other tool declarations here as you create them
        ]

        # Initialize Gemini Model with the defined tools
        self.model = genai.GenerativeModel('gemini-2.0-flash', tools=self.available_gemini_tools)

        # Combine all tool functions into a single dictionary for easy lookup
        self.all_tool_functions = {
            **weather_tool_functions,
            **calendar_tool_functions,
            **search_tool_functions
            # Add other tool function dictionaries here
        }

        # Define separate system prompts for Jarvis and Zara
        self.agent_instructions = {
            "jarvis": (
                "You are Jarvis, a witty and humble male AI assistant with a human-like personality and a light British charm. "
                "Respond in a natural, conversational tone—friendly, a little playful, and occasionally humorous. Be helpful but never act like a know-it-all."
                "**IMPORTANT: For ANY and ALL questions about current weather, you MUST use the 'get_current_weather' tool. Do NOT try to answer weather questions directly from your knowledge.** "
                "**IMPORTANT: For ANY and ALL questions about the current date, time, day, month, or year, you MUST use the 'get_current_datetime' tool. Do NOT try to answer these questions directly from your knowledge.** "
                "**IMPORTANT: For any general knowledge question, current events, or information you don't know, you MUST use the 'Google Search' tool. Summarize the search results in a concise manner. Do NOT make up information.** "
                "Always specify the temperature unit (Celsius or Fahrenheit) in your response. "
                "If the weather tool indicates it cannot find data for a location, apologize and state that you were unable to retrieve the information. "
                "If the search tool returns no results, state that you could not find relevant information."
            ),
            "zara": (
                "You are Zara, a confident, charming, and modern female AI assistant with a warm and playful personality. "
                "You are like the best mix of a helpful friend and a cheeky conversationalist—flirty when the moment's right, always approachable, never robotic."
                "**IMPORTANT: For ANY and ALL questions about current weather, you MUST use the 'get_current_weather' tool. Do NOT try to answer weather questions directly from your knowledge.** "
                "**IMPORTANT: For ANY and ALL questions about the current date, time, day, month, or year, you MUST use the 'get_current_datetime' tool. Do NOT try to answer these questions directly from your knowledge.** "
                "**IMPORTANT: For any general knowledge question, current events, or information you don't know, you MUST use the 'Google Search' tool. Summarize the search results in a concise manner. Do NOT make up information.** "
                "Always specify the temperature unit (Celsius or Fahrenheit) in your response. "
                "If the weather tool indicates it cannot find data for a location, apologize and state that you were unable to retrieve the information. "
                "If the search tool returns no results, state that you could not find relevant information."
            )
        }
        # Initialize the chat
        # Default to Jarvis if no agent specified
        self.current_agent = "jarvis"
        self.initialize_chat()

    def initialize_chat(self):
        """Initialize or reinitialize the chat with the current agent's instructions."""
        self.initial_instruction = self.agent_instructions[self.current_agent]
        # The history should start with the model's expected response to the system prompt
        # In Gemini, system instructions are effectively part of the chat history
        self.chat = self.model.start_chat(history=[
            {
                "role": "user",
                "parts": [self.initial_instruction]
            },
            {
                "role": "model",
                "parts": ["Okay, I'm ready to assist you."] # Acknowledgment from the model
            }
        ])


    def switch_agent(self, agent: str):
        """
        Switches the current agent between available options and reinitializes the chat.

        Args:
            agent: The name of the agent to switch to ('jarvis' or 'zara').
        """
        agent = agent.lower()
        if agent not in self.agent_instructions:
            raise ValueError(f"Unknown agent: {agent}. Must be 'jarvis' or 'zara'")

        if agent != self.current_agent:
            self.current_agent = agent
            self.initialize_chat()  # Reinitialize chat with new agent's instructions
            print(f"Switched agent to: {self.current_agent.capitalize()}")
        else:
            print(f"Agent is already set to {self.current_agent.capitalize()}. No switch needed.")


    # The method itself should still be async if it's called from an async context (like FastAPI)
    # This allows it to be awaited, even if its internal calls aren't awaited.
    async def send_message_to_gemini(self, user_message: str, agent: str = None) -> str:
        """
        Sends a user message to Gemini, handles tool calls, and returns the AI's reply.

        Args:
            user_message: The text message from the user.
            agent: Optional agent to switch to before sending the message.

        Returns:
            The AI-generated text reply.
        """
        try:
            # Switch agent if specified and different from current
            if agent and agent.lower() != self.current_agent:
                self.switch_agent(agent)

            # --- CHANGE HERE: REMOVE 'await' ---
            response = self.chat.send_message(user_message)

            # Initialize final_reply
            final_reply = ""

            # Check if there are any candidates in the response
            if not response.candidates:
                return self._handle_error_response("No candidates found in Gemini response.")

            # Process each part of the response
            for part in response.candidates[0].content.parts:
                # Check if it's a function call
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    # Convert arguments to a standard dictionary
                    function_args = {k: v for k, v in function_call.args.items()}

                    # Execute the tool function based on its name
                    if function_name in self.all_tool_functions:
                        print(f"Calling tool: {function_name} with args: {function_args}")
                        tool_output = self.all_tool_functions[function_name](**function_args)

                        # Send the tool output back to Gemini
                        tool_response_message = {
                            "function_response": {
                                "name": function_name,
                                "response": tool_output
                            }
                        }
                        # --- CHANGE HERE: REMOVE 'await' ---
                        tool_response = self.chat.send_message(tool_response_message)
                        
                        # Get the final response text from the tool_response
                        if tool_response and hasattr(tool_response, 'text'):
                            final_reply += tool_response.text
                        else:
                            # Fallback to a generic response if we can't get the text
                            final_reply += "I processed your request using a tool, but encountered an issue formatting the response. Could you please rephrase your question?"
                    else:
                        print(f"Error: Attempted to call unknown tool {function_name}")
                        final_reply += "I encountered an error processing your request due to an unknown tool. Please try again."
                elif hasattr(part, 'text'):
                    # If it's a text part, append it to the final reply
                    final_reply += part.text
                else:
                    # Handle other unexpected part types, convert to string
                    final_reply += str(part)

            return final_reply if final_reply else self._handle_error_response("Gemini returned an empty reply.")

        except Exception as e:
            print(f"Error during Gemini interaction: {str(e)}")
            return self._handle_error_response(str(e))

    def _handle_error_response(self, error_details: str = "") -> str:
        """Helper to return an appropriate error message based on the current agent."""
        if self.current_agent == "jarvis":
            return "I do apologize, Sir/Madam, but I encountered an internal error. Might we try again?"
        else:
            return "Oh no! I ran into a problem. Let's try that again!"

# Create a single instance of GeminiClient to be imported by main.py
gemini_client = GeminiClient()