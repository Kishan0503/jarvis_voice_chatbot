import google.generativeai as genai
from google.generativeai.types import Tool

from config import app_config

from tools.weather import weather_tool_declaration, tool_functions as weather_tool_functions
from tools.calendar import calendar_tool_declaration, tool_functions as calendar_tool_functions
from tools.search import search_tool_declaration, tool_functions as search_tool_functions
from tools.system_control import system_tool_declarations, tool_functions as system_tool_functions
from tools.file_ops import file_tool_declarations, tool_functions as file_tool_functions
from tools.clipboard import clipboard_tool_declarations, tool_functions as clipboard_tool_functions
from tools.screen import screen_tool_declarations, tool_functions as screen_tool_functions
from tools.notes import notes_tool_declarations, tool_functions as notes_tool_functions


class _UserSession:
    """Conversation state for a single local user."""

    def __init__(self, model, system_instruction: str, max_history_turns: int):
        self.model = model
        self.max_history_turns = max_history_turns
        self.initial_history_content = [
            {"role": "user", "parts": [system_instruction]},
            {"role": "model", "parts": ["Understood. I'm ready to assist you, Sir."]},
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
    Desktop version — single agent (Jarvis), synchronous calls,
    designed to run inside a QThread worker.
    """

    MAX_HISTORY_TURNS = 6

    def __init__(self):
        genai.configure(api_key=app_config.GEMINI_API_KEY)

        self.available_gemini_tools = [
            Tool(function_declarations=[
                weather_tool_declaration,
                calendar_tool_declaration,
                search_tool_declaration,
                *system_tool_declarations,
                *file_tool_declarations,
                *clipboard_tool_declarations,
                *screen_tool_declarations,
                *notes_tool_declarations,
            ])
        ]

        self.model = genai.GenerativeModel(
            model_name=app_config.GEMINI_MODEL,
            tools=self.available_gemini_tools
        )

        self.all_tool_functions = {
            **weather_tool_functions,
            **calendar_tool_functions,
            **search_tool_functions,
            **system_tool_functions,
            **file_tool_functions,
            **clipboard_tool_functions,
            **screen_tool_functions,
            **notes_tool_functions,
        }

        self.system_instruction = (
            "You are Jarvis, a witty, humble male AI assistant with a human-like tone "
            "and light British charm. Speak naturally—friendly, playful, sometimes humorous. "
            "Be helpful, not a know-it-all. Keep responses concise for voice output. "
            "**Always use 'get_current_weather' for weather. NEVER answer weather directly.** "
            "**Always use 'get_current_datetime' for date/time. NEVER answer directly.** "
            "**Use 'google_search' for general knowledge or unknown info. Do NOT guess. Summarize results briefly.** "
            "**Use 'save_note' when the user asks to save, remember, or note something down.** "
            "**Use 'list_notes' when the user asks to see, show, or view their notes.** "
            "**Use 'delete_note' when the user asks to delete or remove a note.** "
            "You can open and close applications, search files, read file contents, "
            "list directories, read and write the clipboard, take screenshots, "
            "and check system information (CPU, RAM, disk, battery). "
            "Always mention Celsius or Fahrenheit for weather. "
            "If weather data is missing, apologize. "
            "If search yields nothing, say no info found. "
            "For any destructive action, always confirm with the user first."
        )

        self._session: _UserSession | None = None

    def _get_session(self) -> _UserSession:
        if self._session is None:
            self._session = _UserSession(
                model=self.model,
                system_instruction=self.system_instruction,
                max_history_turns=self.MAX_HISTORY_TURNS,
            )
        return self._session

    def reset_session(self):
        self._session = None

    def send_message_to_gemini(self, user_message: str) -> dict:
        """
        Sends a user message to Gemini and returns a dict with:
        - "reply": the AI's text reply
        - "tools_used": list of tool names that were called
        """
        session = self._get_session()
        tools_used = []
        try:
            session.truncate_history()
            response = session.chat.send_message(user_message)

            final_reply = ""

            if not response.candidates:
                return {"reply": self._error_message("No candidates"), "tools_used": []}

            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = {k: v for k, v in function_call.args.items()}

                    if function_name in self.all_tool_functions:
                        tool_output = self.all_tool_functions[function_name](**function_args)
                        tools_used.append(function_name)

                        tool_response_message = {
                            "function_response": {
                                "name": function_name,
                                "response": tool_output,
                            }
                        }

                        tool_response = session.chat.send_message(tool_response_message)

                        tool_text = self._extract_text(tool_response)
                        if tool_text:
                            final_reply += tool_text
                        else:
                            status = tool_output.get("message", tool_output.get("status", ""))
                            final_reply += status or "Done."
                    else:
                        final_reply += f"I don't have access to the tool '{function_name}' yet."

                elif hasattr(part, 'text'):
                    final_reply += part.text
                else:
                    final_reply += str(part)

            reply = final_reply if final_reply else self._error_message("Gemini returned an empty reply.")
            return {"reply": reply, "tools_used": tools_used}

        except Exception as e:
            print(f"Error in GeminiClient send_message_to_gemini: {e}")
            return {"reply": self._error_message(str(e)), "tools_used": tools_used}

    @staticmethod
    def _extract_text(response) -> str:
        """Safely extract text from a Gemini response without using the .text shortcut."""
        try:
            if not response or not response.candidates:
                return ""
            parts = response.candidates[0].content.parts
            texts = []
            for part in parts:
                if hasattr(part, 'text') and part.text:
                    texts.append(part.text)
            return " ".join(texts)
        except (AttributeError, IndexError, ValueError):
            return ""

    @staticmethod
    def _error_message(error_details: str = "") -> str:
        return "I do apologize, but I encountered an internal error. Might we try again?"


gemini_client = GeminiClient()
