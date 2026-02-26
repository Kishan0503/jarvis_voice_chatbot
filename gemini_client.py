import google.generativeai as genai
from google.generativeai.types import Tool

from config import app_config

from tools.weather import weather_tool_declaration, tool_functions as weather_tool_functions
from tools.calendar import calendar_tool_declaration, tool_functions as calendar_tool_functions
from tools.search import search_tool_declaration, tool_functions as search_tool_functions


class _UserSession:
    """Per-user conversation state for a specific agent."""

    def __init__(self, model, agent: str, agent_instructions: dict, max_history_turns: int):
        self.model = model
        self.agent = agent
        self.max_history_turns = max_history_turns
        self.initial_instruction = agent_instructions[agent]
        self.initial_history_content = [
            {"role": "user", "parts": [self.initial_instruction]},
            {"role": "model", "parts": ["Okay, I'm ready to assist you."]},
        ]
        self.chat = self.model.start_chat(history=list(self.initial_history_content))

    def truncate_history(self):
        current_history = list(self.chat.history)
        retained = list(self.initial_history_content)
        start = len(self.initial_history_content)
        actual_start = max(start, len(current_history) - (self.max_history_turns * 2))
        retained.extend(current_history[actual_start:])
        self.chat = self.model.start_chat(history=retained)


class GeminiClient:
    """
    Manages the interaction with the Google Gemini API.
    Maintains isolated chat sessions per user+agent pair so concurrent users
    never interfere with each other.
    """

    MAX_HISTORY_TURNS = 4

    def __init__(self):
        genai.configure(api_key=app_config.GEMINI_API_KEY)

        self.available_gemini_tools = [
            Tool(function_declarations=[
                weather_tool_declaration,
                calendar_tool_declaration,
                search_tool_declaration,
            ])
        ]

        self.model = genai.GenerativeModel(
            model_name=app_config.GEMINI_MODEL,
            tools=self.available_gemini_tools
        )

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

        # Keyed by "user_email:agent" -> _UserSession
        self._sessions: dict[str, _UserSession] = {}

    def _get_session(self, user_email: str, agent: str) -> _UserSession:
        agent = agent.lower()
        if agent not in self.agent_instructions:
            raise ValueError(f"Unknown agent: {agent}. Must be 'jarvis' or 'zara'")

        key = f"{user_email}:{agent}"
        if key not in self._sessions:
            self._sessions[key] = _UserSession(
                model=self.model,
                agent=agent,
                agent_instructions=self.agent_instructions,
                max_history_turns=self.MAX_HISTORY_TURNS,
            )
        return self._sessions[key]

    async def send_message_to_gemini(self, user_message: str, agent: str, user_email: str) -> str:
        """
        Sends a user message to Gemini using the session for the given user+agent.
        Handles tool calls and returns the AI's text reply.
        """
        session = self._get_session(user_email, agent)
        try:
            session.truncate_history()

            response = session.chat.send_message(user_message)

            final_reply = ""

            if not response.candidates:
                return self._error_message(agent, "No candidates found in Gemini response.")

            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = {k: v for k, v in function_call.args.items()}

                    if function_name in self.all_tool_functions:
                        tool_output = self.all_tool_functions[function_name](**function_args)

                        tool_response_message = {
                            "function_response": {
                                "name": function_name,
                                "response": tool_output
                            }
                        }

                        tool_response = session.chat.send_message(tool_response_message)

                        if tool_response and hasattr(tool_response, 'text'):
                            final_reply += tool_response.text
                        else:
                            final_reply += "I processed your request using a tool, but encountered an issue formatting the response. Could you please rephrase your question?"
                    else:
                        final_reply += "I encountered an error processing your request due to an unknown tool. Please try again."

                elif hasattr(part, 'text'):
                    final_reply += part.text
                else:
                    final_reply += str(part)

            return final_reply if final_reply else self._error_message(agent, "Gemini returned an empty reply.")

        except Exception as e:
            print(f"Error in GeminiClient send_message_to_gemini: {e}")
            return self._error_message(agent, str(e))

    @staticmethod
    def _error_message(agent: str, error_details: str = "") -> str:
        if agent.lower() == "jarvis":
            return "I do apologize, Sir/Madam, but I encountered an internal error. Might we try again?"
        return "Oh no! I ran into a problem. Let's try that again!"


gemini_client = GeminiClient()