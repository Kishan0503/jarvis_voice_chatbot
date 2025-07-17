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
        genai.configure(api_key=app_config.GEMINI_API_KEY)

        self.available_gemini_tools = [
            weather_tool_declaration,
            calendar_tool_declaration,
            search_tool_declaration
        ]

        # Consider switching to gemini-2.5-flash-lite if available in your region
        # as it has a higher RPD (1000 vs 200 for gemini-2.0-flash)
        # However, it's a preview model and features might change.
        # self.model = genai.GenerativeModel(model_name='gemini-2.5-flash-lite-preview-06-17', tools=self.available_gemini_tools)
        self.model = genai.GenerativeModel(model_name='gemini-2.0-flash', tools=self.available_gemini_tools)


        self.all_tool_functions = {
            **weather_tool_functions,
            **calendar_tool_functions,
            **search_tool_functions
        }

        self.agent_instructions = {
            "jarvis": (
                "You are Jarvis, a witty, humble male AI assistant with a human-like tone and light British charm. "
                "Speak naturally—friendly, playful, sometimes humorous. Be helpful, not a know-it-all. "
                "**Always use 'get_current_weather' for weather. NEVER answer weather directly.** "
                "**Always use 'get_current_datetime' for date/time. NEVER answer directly.** "
                "**Use 'Google Search' for general knowledge or unknown info. Do NOT guess. Summarize results briefly.** "
                "Always mention Celsius or Fahrenheit. "
                "If weather data is missing, apologize. "
                "If search yields nothing, say no info found."
            ),
            "zara": (
                "You are Zara, a confident, modern female AI assistant—warm, playful, charming. "
                "You're a helpful friend with a cheeky side—flirty when fitting, always approachable. "
                "**Always use 'get_current_weather' for weather. NEVER answer weather directly.** "
                "**Always use 'get_current_datetime' for date/time. NEVER answer directly.** "
                "**Use 'Google Search' for general knowledge or unknown info. Do NOT guess. Summarize results briefly.** "
                "Always mention Celsius or Fahrenheit. "
                "If weather data is missing, apologize. "
                "If search yields nothing, say no info found."
            )
        }
        
        self.current_agent = "jarvis"
        self.max_history_turns = 4  # Keep last 4 turns (2 user, 2 model) + initial prompt
                                  # Initial prompt is 2 messages (user instruction + model ack)
                                  # So, total history will be (2 + max_history_turns * 2) messages
                                  # If max_history_turns = 4, total messages = 2 + 8 = 10
                                  # This will keep the conversation somewhat contextual but bounded.
        self.initialize_chat()

    def initialize_chat(self):
        """
        Initialize or reinitialize the chat with the current agent's instructions.
        Logs token count of the initial history.
        """
        self.initial_instruction = self.agent_instructions[self.current_agent]
        
        self.initial_history_content = [
            {
                "role": "user",
                "parts": [self.initial_instruction]
            },
            {
                "role": "model",
                "parts": ["Okay, I'm ready to assist you."]
            }
        ]
        
        # Count tokens for the initial history
        try:
            initial_history_tokens = self.model.count_tokens(self.initial_history_content).total_tokens
            print(f"Initial chat history tokens for {self.current_agent.capitalize()}: {initial_history_tokens}")
        except Exception as e:
            print(f"Could not count tokens for initial history: {e}")

        self.chat = self.model.start_chat(history=self.initial_history_content)


    def switch_agent(self, agent: str):
        """
        Switches the current agent between available options and reinitializes the chat.
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


    async def send_message_to_gemini(self, user_message: str, agent: str = None) -> str:
        """
        Sends a user message to Gemini, handles tool calls, and returns the AI's reply.
        Includes token usage logging and history truncation.
        """
        try:
            if agent and agent.lower() != self.current_agent:
                self.switch_agent(agent)

            # --- History Truncation Logic ---
            # Get the current history from the chat object
            current_history_for_truncation = list(self.chat.history) # Make a copy

            # Preserve the initial agent instructions
            retained_history = list(self.initial_history_content)

            # Add recent turns, excluding the initial prompt messages
            # Each "turn" consists of a user message and a model response.
            # So, we want to keep (max_history_turns * 2) messages from the end of the history.
            # We skip the first 2 messages because they are the initial instructions.
            recent_turns_start_index = len(self.initial_history_content) # Start from after the initial prompt
            
            # Ensure we don't go out of bounds if chat is shorter than desired truncation length
            actual_history_start_index = max(recent_turns_start_index, len(current_history_for_truncation) - (self.max_history_turns * 2))

            retained_history.extend(current_history_for_truncation[actual_history_start_index:])
            
            # Reinitialize the chat with the truncated history
            # This is crucial for controlling the history length passed in each new API call.
            self.chat = self.model.start_chat(history=retained_history)
            print(f"Chat reinitialized with truncated history. Current history length: {len(self.chat.history)} messages.")
            # --- End History Truncation Logic ---


            # Step 1: Send user message
            # Estimate tokens before sending
            # The 'current_history' here reflects the *truncated* history that will be sent.
            current_history_for_token_count = list(self.chat.history) + [{"role": "user", "parts": [user_message]}]
            try:
                prompt_tokens = self.model.count_tokens(current_history_for_token_count).total_tokens
                print(f"Tokens for user message and *truncated* history (before first send): {prompt_tokens}")
            except Exception as e:
                print(f"Could not count tokens for user message with truncated history: {e}")

            response = self.chat.send_message(user_message)
            
            if response.usage_metadata:
                print(f"API Call 1 (User Message) - Prompt Tokens: {response.usage_metadata.prompt_token_count}, "
                             f"Candidates Tokens: {response.usage_metadata.candidates_token_count}, "
                             f"Total Tokens: {response.usage_metadata.total_token_count}")

            final_reply = ""
            
            if not response.candidates:
                return self._handle_error_response("No candidates found in Gemini response.")

            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = {k: v for k, v in function_call.args.items()}

                    if function_name in self.all_tool_functions:
                        print(f"Calling tool: {function_name} with args: {function_args}")
                        tool_output = self.all_tool_functions[function_name](**function_args)

                        tool_response_message = {
                            "function_response": {
                                "name": function_name,
                                "response": tool_output
                            }
                        }
                        
                        # Step 2: Send tool output back to Gemini
                        # The 'current_history' here will automatically include the previous user message
                        # and the model's tool call response because it's part of the `self.chat` object's internal history.
                        current_history_with_tool_output = list(self.chat.history) + [{"role": "user", "parts": [tool_response_message]}] # For token count estimate
                        try:
                            tool_response_prompt_tokens = self.model.count_tokens(current_history_with_tool_output).total_tokens
                            print(f"Tokens for tool response and *current* history (before second send): {tool_response_prompt_tokens}")
                        except Exception as e:
                            print(f"Could not count tokens for tool response message: {e}")

                        tool_response = self.chat.send_message(tool_response_message)

                        if tool_response.usage_metadata:
                            print(f"API Call 2 (Tool Response) - Prompt Tokens: {tool_response.usage_metadata.prompt_token_count}, "
                                         f"Candidates Tokens: {tool_response.usage_metadata.candidates_token_count}, "
                                         f"Total Tokens: {tool_response.usage_metadata.total_token_count}")
                        
                        if tool_response and hasattr(tool_response, 'text'):
                            final_reply += tool_response.text
                        else:
                            final_reply += "I processed your request using a tool, but encountered an issue formatting the response. Could you please rephrase your question?"
                    else:
                        print(f"Error: Attempted to call unknown tool {function_name}")
                        final_reply += "I encountered an error processing your request due to an unknown tool. Please try again."
                elif hasattr(part, 'text'):
                    final_reply += part.text
                else:
                    final_reply += str(part)

            return final_reply if final_reply else self._handle_error_response("Gemini returned an empty reply.")

        except Exception as e:
            print(f"Error during Gemini interaction: {str(e)}", exc_info=True)
            return self._handle_error_response(str(e))

    def _handle_error_response(self, error_details: str = "") -> str:
        """Helper to return an appropriate error message based on the current agent."""
        if self.current_agent == "jarvis":
            return "I do apologize, Sir/Madam, but I encountered an internal error. Might we try again?"
        else:
            return "Oh no! I ran into a problem. Let's try that again!"

# Create a single instance of GeminiClient to be imported by main.py
gemini_client = GeminiClient()