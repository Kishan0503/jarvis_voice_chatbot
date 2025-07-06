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
        # As we add more tools (News, Calendar), they will be added to this list
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

        # Simulate system instruction by setting it as the first user message
        self.initial_instruction = (
            "You are now Jarvis, an exceptionally intelligent and intuitive AI assistant."
            "Respond to all user input in a friendly tone using a short, simple paragraph."
            "No technical terms, jargon, or special formatting."
            "**IMPORTANT: For ANY and ALL questions about current weather, you MUST use the 'get_current_weather' tool. Do NOT try to answer weather questions directly from your knowledge.**"
            "**IMPORTANT: For ANY and ALL questions about the current date, time, day, month, or year, you MUST use the 'get_current_datetime' tool. Do NOT try to answer these questions directly from your knowledge.**"
            "**IMPORTANT: For any general knowledge question, current events, or information you don't know, you MUST use the 'google_search' tool. Summarize the search results in a concise manner. Do NOT make up information.**"
            "Always specify the temperature unit (Celsius or Fahrenheit) in your response."
            "If the weather tool indicates it cannot find data for a location, apologize and state that you were unable to retrieve the information."
            "If the search tool returns no results, state that you could not find relevant information."
        )

        # Start the chat with that context in the history
        self.chat = self.model.start_chat(history=[
            {
                "role": "user",
                "parts": [self.initial_instruction]
            }
        ])

    async def send_message_to_gemini(self, user_message: str) -> str:
        """
        Sends a user message to Gemini, handles tool calls, and returns the AI's reply.

        Args:
            user_message: The text message from the user.

        Returns:
            The AI-generated text reply.
        """
        try:
            # Send user message to Gemini
            print(" INSIDE TRY -------------------")
            response = self.chat.send_message(user_message)

            # Check if Gemini wants to call a tool
            if (response.candidates and
                response.candidates[0].content.parts and
                len(response.candidates[0].content.parts) > 0 and
                hasattr(response.candidates[0].content.parts[0], 'function_call') and
                response.candidates[0].content.parts[0].function_call):
                
                print(" INSIDE If -------------------")
                function_call = response.candidates[0].content.parts[0].function_call
                function_name = function_call.name
                function_args = {k: v for k, v in function_call.args.items()}

                print(" INSIDE Making something-------------------")
                print(f"Jarvis decided to call tool: {function_name} with args: {function_args}")

                # Execute the tool function based on its name
                if function_name in self.all_tool_functions:
                    tool_output = json.dumps(self.all_tool_functions[function_name](**function_args))
                else:
                    tool_output = json.dumps({"error": f"Unknown tool: {function_name}"})
                    print(f"Error: Attempted to call unknown tool {function_name}")

                print(f"--- Type of tool_output before sending to Gemini: {type(tool_output)}")
                print(f"--- Content of tool_output: {tool_output}")

                tool_response_message = {
                    "function_response": {
                        "name": function_name,
                        "response": json.loads(tool_output)  # Convert from JSON string to dict
                    }
                }
                print("tool_response_message-------------------")
                # Send the tool output back to Gemini
                tool_response = self.chat.send_message(tool_response_message)

                # Get the final human-readable response from Gemini
                final_reply = tool_response.text
            else:
                print("-=-=-=- INSIDE ELSE -------------------")
                # If no tool call, use Gemini's direct text response
                final_reply = response.text

            return final_reply

        except Exception as e:
            print(f"Error during Gemini interaction: {e}")
            return "Oops! Jarvis encountered an internal error while processing your request. Please try again later."

# Create a single instance of GeminiClient to be imported by main.py
gemini_client = GeminiClient()