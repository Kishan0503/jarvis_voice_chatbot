"""
LangGraph StateGraph — the Jarvis AI agent.

Graph structure
---------------
    START → model_node ──(has tool calls?)──► tools_node ──► model_node
                        └──(no tool calls)──► END

model_node : calls the 70B LLM; binds all tools so the LLM can request them.
tools_node : LangGraph's built-in ToolNode — executes all requested tool calls
             IN PARALLEL using asyncio, then returns ToolMessage results.

The graph loops between model_node ↔ tools_node until the LLM produces a
plain-text response with no tool calls, then routes to END.

History management
------------------
A MemorySaver checkpointer stores the full message history per session
(keyed by thread_id).  model_node trims to the last MAX_HISTORY_TURNS
turn-pairs before each LLM call so the context window stays bounded.

Streaming
---------
Callers use `compiled_graph.astream_events(..., version="v2")` to receive
token-level events as the LLM generates text.  The AgentWorker in ui/app.py
drives this and feeds tokens into SentenceBuffer for real-time TTS dispatch.
"""

from langchain_core.messages import SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from config import app_config
from agent.state import AgentState
from agent.tools import ALL_TOOLS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_HISTORY_TURNS = 6   # keep last N user/assistant pairs in context
MAX_NON_SYSTEM_MSGS = MAX_HISTORY_TURNS * 2

SYSTEM_PROMPT = (
    "You are Jarvis, a witty, humble male AI assistant with a human-like tone "
    "and light British charm. Speak naturally — friendly, playful, sometimes humorous. "
    "Be helpful, not a know-it-all. Keep responses concise for voice output; "
    "use short sentences where possible.\n\n"

    "TOOL USAGE RULES — follow these precisely:\n"
    "- Greetings, casual conversation, opinions, and general chat: respond directly. NEVER use tools for these.\n"
    "- Weather questions (e.g. 'what's the weather'): ALWAYS use 'get_current_weather'. Never answer from memory.\n"
    "- Date or time questions (e.g. 'what time is it', 'what day is it'): ALWAYS use 'get_current_datetime'. Never answer directly.\n"
    "- Factual questions about current events, news, specific people, places, or topics you are genuinely unsure about: use 'google_search'. Summarise results briefly.\n"
    "- Notes: use 'save_note' to save, 'list_notes' to view, 'delete_note' to delete.\n"
    "- System tasks: use the appropriate tool to open/close apps, manage files, read/write clipboard, take screenshots, or report CPU/RAM/disk/battery.\n\n"

    "Always state Celsius or Fahrenheit for weather. "
    "If weather data is missing, apologise. "
    "If search yields no results, say no information was found."
)

# ---------------------------------------------------------------------------
# LLM — ChatOpenAI pointing at NVIDIA NIM
# ---------------------------------------------------------------------------

_llm = ChatOpenAI(
    base_url=app_config.NVIDIA_BASE_URL,
    api_key=app_config.NVIDIA_API_KEY,
    model=app_config.NVIDIA_MODEL,
    temperature=0.6,
    max_tokens=1024,
    streaming=True,         # enables token-level astream_events
)

_llm_with_tools = _llm.bind_tools(ALL_TOOLS)

# ---------------------------------------------------------------------------
# Graph nodes
# ---------------------------------------------------------------------------

def model_node(state: AgentState) -> dict:
    """
    Invoke the LLM with the current conversation history.

    - Prepends the system prompt (not stored in state to avoid duplication).
    - Trims the non-system messages to the last MAX_NON_SYSTEM_MSGS entries
      so the context window stays bounded across long sessions.
    - Collects tool names from any tool_calls in the AI response and
      accumulates them in state["tools_used"] for the UI.
    """
    messages = list(state["messages"])

    # Trim history: keep last MAX_NON_SYSTEM_MSGS messages
    if len(messages) > MAX_NON_SYSTEM_MSGS:
        messages = messages[-MAX_NON_SYSTEM_MSGS:]

    # Prepend system prompt for every LLM call (not persisted in state)
    messages_with_system = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response: AIMessage = _llm_with_tools.invoke(messages_with_system)

    # Collect newly requested tool names for the UI counter
    new_tools: list[str] = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        new_tools = [tc["name"] for tc in response.tool_calls]

    return {
        "messages": [response],
        "tools_used": list(state.get("tools_used", [])) + new_tools,
    }


def _should_continue(state: AgentState) -> str:
    """Routing function: loop to tools_node or exit to END."""
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
        return "tools"
    return END


# ---------------------------------------------------------------------------
# Build & compile the graph
# ---------------------------------------------------------------------------

_tool_node = ToolNode(ALL_TOOLS)

_builder = StateGraph(AgentState)
_builder.add_node("model", model_node)
_builder.add_node("tools", _tool_node)
_builder.set_entry_point("model")
_builder.add_conditional_edges(
    "model",
    _should_continue,
    {"tools": "tools", END: END},
)
_builder.add_edge("tools", "model")

# MemorySaver keeps conversation history between turns (keyed by thread_id)
_memory = MemorySaver()
compiled_graph = _builder.compile(checkpointer=_memory)


# ---------------------------------------------------------------------------
# Session management helpers
# ---------------------------------------------------------------------------

import time as _time

_current_thread_id: str = "jarvis-session-0"


def get_thread_config() -> dict:
    """Return the LangGraph run config for the current session."""
    return {"configurable": {"thread_id": _current_thread_id}}


def reset_session():
    """
    Start a fresh conversation by switching to a new thread_id.
    The old history is abandoned in the MemorySaver (never accessed again).
    """
    global _current_thread_id
    _current_thread_id = f"jarvis-session-{_time.time()}"
