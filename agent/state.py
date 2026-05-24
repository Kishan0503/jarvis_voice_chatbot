from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Single source of truth flowing through the LangGraph StateGraph.

    messages:   Full conversation history. The `add_messages` reducer
                automatically appends new messages and handles tool-call /
                tool-result pairing — no manual list management needed.

    tools_used: Names of every tool invoked during this turn, collected
                for the UI panel refresh (notes, session stats, etc.).
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    tools_used: list[str]
