import json
from openai import OpenAI

from tools.weather import tool_functions as weather_tool_functions
from tools.calendar import tool_functions as calendar_tool_functions
from tools.search import tool_functions as search_tool_functions
from tools.system_control import tool_functions as system_tool_functions
from tools.file_ops import tool_functions as file_tool_functions
from tools.clipboard import tool_functions as clipboard_tool_functions
from tools.screen import tool_functions as screen_tool_functions
from tools.notes import tool_functions as notes_tool_functions

import os

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")

# All tools in OpenAI function-calling format
_TOOLS = [
    # --- Weather ---
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Gets the current weather for a given location (city, state, or country).",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city, state, or country, e.g. San Francisco, CA, London, or India.",
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit. Defaults to 'celsius'.",
                    },
                },
                "required": ["location"],
            },
        },
    },
    # --- Date / Time ---
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Gets the current date, time, day of the week, month, and year.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # --- Web Search ---
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": (
                "Performs a Google search to find information on the internet. "
                "Use this for general knowledge questions, current events, or anything "
                "requiring external information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query string."},
                },
                "required": ["query"],
            },
        },
    },
    # --- System Control ---
    {
        "type": "function",
        "function": {
            "name": "open_application",
            "description": "Open/launch an application by name (e.g., 'firefox', 'terminal', 'vs code').",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Application name to open."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_application",
            "description": "Close/terminate a running application by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Application name to close."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_running_apps",
            "description": "List all currently running user applications.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Get system information: CPU usage, RAM, disk space, battery.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_system_volume",
            "description": "Set the system audio volume to a specific level (0-100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Volume level from 0 to 100.",
                    },
                },
                "required": ["level"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lock_screen",
            "description": "Lock the desktop screen.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # --- File Operations ---
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "Search for files matching a glob pattern in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "File name or glob pattern (e.g., '*.py', 'report*.pdf').",
                    },
                    "search_path": {
                        "type": "string",
                        "description": "Directory to search in (default: home directory).",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file_content",
            "description": "Read the text content of a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Full path to the file."},
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path (default: home directory).",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_info",
            "description": "Get information about a file (size, modified date, type).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file."},
                },
                "required": ["filepath"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "open_file_default",
            "description": "Open a file with the default system application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to the file to open."},
                },
                "required": ["filepath"],
            },
        },
    },
    # --- Clipboard ---
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Read the current text content from the system clipboard.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Copy text to the system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy to clipboard."},
                },
                "required": ["text"],
            },
        },
    },
    # --- Screen ---
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Take a screenshot of the entire screen.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # --- Notes ---
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": (
                "Save a new note for the user. "
                "Use when the user asks to save, remember, or note something down."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "The note content to save."},
                },
                "required": ["content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_notes",
            "description": "List all saved notes. Use when the user asks to see, show, or view their notes.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_note",
            "description": "Delete a specific note by its ID. Use when the user asks to delete or remove a note.",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "integer", "description": "The ID of the note to delete."},
                },
                "required": ["note_id"],
            },
        },
    },
]

_SYSTEM_INSTRUCTION = (
    "You are Jarvis, a witty, humble male AI assistant with a human-like tone "
    "and light British charm. Speak naturally—friendly, playful, sometimes humorous. "
    "Be helpful, not a know-it-all. Keep responses concise for voice output. "
    "Always use 'get_current_weather' for weather. NEVER answer weather directly. "
    "Always use 'get_current_datetime' for date/time. NEVER answer directly. "
    "Use 'google_search' for general knowledge or unknown info. Do NOT guess. Summarize results briefly. "
    "Use 'save_note' when the user asks to save, remember, or note something down. "
    "Use 'list_notes' when the user asks to see, show, or view their notes. "
    "Use 'delete_note' when the user asks to delete or remove a note. "
    "You can open and close applications, search files, read file contents, "
    "list directories, read and write the clipboard, take screenshots, "
    "and check system information (CPU, RAM, disk, battery). "
    "Always mention Celsius or Fahrenheit for weather. "
    "If weather data is missing, apologize. "
    "If search yields nothing, say no info found. "
    "For any destructive action, always confirm with the user first."
)


class OpenAIClient:
    """
    Manages interaction with NVIDIA's OpenAI-compatible API (Llama 3.1 8B).
    Drop-in replacement for GeminiClient — identical public interface.

    Designed to run inside a QThread worker (synchronous, blocking calls).
    """

    MAX_HISTORY_TURNS = 6

    def __init__(self):
        self._client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)
        self._all_tool_functions: dict = {
            **weather_tool_functions,
            **calendar_tool_functions,
            **search_tool_functions,
            **system_tool_functions,
            **file_tool_functions,
            **clipboard_tool_functions,
            **screen_tool_functions,
            **notes_tool_functions,
        }
        self._history: list[dict] = []

    def reset_session(self):
        """Clear conversation history and start fresh."""
        self._history = []

    def send_message_to_gemini(self, user_message: str) -> dict:
        """
        Sends a user message to the model and returns a dict with:
        - "reply"     : the AI's final text reply
        - "tools_used": list of tool names that were called
        """
        # print(f"User message: {user_message}")
        self._truncate_history()
        self._history.append({"role": "user", "content": user_message})

        tools_used: list[str] = []

        try:
            response = self._client.chat.completions.create(
                model=NVIDIA_MODEL,
                messages=self._build_messages(),
                tools=_TOOLS,
                tool_choice="auto",
                temperature=0.6,
                top_p=0.7,
                max_tokens=1024,
            )
            message = response.choices[0].message

            # Agentic loop: keep executing tool calls until the model gives a plain text reply
            while message.tool_calls:
                # Record the assistant's tool-call turn in history
                self._history.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                })

                # Execute every tool call in this turn
                for tool_call in message.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        fn_args = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        fn_args = {}

                    if fn_name in self._all_tool_functions:
                        tool_output = self._all_tool_functions[fn_name](**fn_args)
                        tools_used.append(fn_name)
                    else:
                        tool_output = {"error": f"Unknown tool: {fn_name}"}
                        # print(f"Warning: model requested unknown tool '{fn_name}'")

                    self._history.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_output),
                    })

                # Follow-up call so the model can produce a reply given the tool results
                response = self._client.chat.completions.create(
                    model=NVIDIA_MODEL,
                    messages=self._build_messages(),
                    tools=_TOOLS,
                    tool_choice="auto",
                    temperature=0.6,
                    top_p=0.7,
                    max_tokens=1024,
                )
                message = response.choices[0].message

            # Arrived at a plain text reply
            reply = (message.content or "").strip() or self._error_message()
            self._history.append({"role": "assistant", "content": reply})

            # print(f"AI reply: {reply}")
            return {"reply": reply, "tools_used": tools_used}

        except Exception as e:
            # print(f"Error in OpenAIClient.send_message_to_gemini: {e}")
            # Remove the failed user message so history stays consistent
            if self._history and self._history[-1]["role"] == "user":
                self._history.pop()
            return {"reply": self._error_message(), "tools_used": tools_used}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_messages(self) -> list[dict]:
        """Prepend the system prompt to the current conversation history."""
        return [{"role": "system", "content": _SYSTEM_INSTRUCTION}] + self._history

    def _truncate_history(self):
        """Keep only the most recent MAX_HISTORY_TURNS turn-pairs."""
        max_messages = self.MAX_HISTORY_TURNS * 2
        if len(self._history) > max_messages:
            self._history = self._history[-max_messages:]

    @staticmethod
    def _error_message() -> str:
        return "I do apologize, but I encountered an internal error. Might we try again?"


# Singleton — same name as the Gemini version for a zero-friction drop-in swap
gemini_client = OpenAIClient()
