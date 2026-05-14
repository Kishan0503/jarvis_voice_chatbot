"""
Jarvis LangGraph agent package.

Public API
----------
compiled_graph   : The compiled LangGraph StateGraph (model ↔ tools loop).
get_thread_config: Returns the LangGraph run config for the current session.
reset_session    : Clears history by switching to a new thread_id.
ALL_TOOLS        : List of all LangChain BaseTool instances.
SentenceBuffer   : Streaming token → sentence splitter for TTS.
"""

from agent.graph import compiled_graph, get_thread_config, reset_session
from agent.tools import ALL_TOOLS
from agent.sentence_buffer import SentenceBuffer

__all__ = [
    "compiled_graph",
    "get_thread_config",
    "reset_session",
    "ALL_TOOLS",
    "SentenceBuffer",
]
