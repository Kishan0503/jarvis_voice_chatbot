import pyperclip
from typing import Dict, Any
from google.generativeai.types import FunctionDeclaration


def get_clipboard() -> Dict[str, Any]:
    """Read current clipboard text content."""
    try:
        text = pyperclip.paste()
        if text:
            return {"status": "success", "content": text[:2000]}
        return {"status": "success", "content": "", "message": "Clipboard is empty"}
    except Exception as e:
        return {"status": "error", "message": f"Cannot read clipboard: {e}"}


def set_clipboard(text: str) -> Dict[str, Any]:
    """Write text to the system clipboard."""
    try:
        pyperclip.copy(text)
        return {"status": "success", "message": f"Copied to clipboard ({len(text)} chars)"}
    except Exception as e:
        return {"status": "error", "message": f"Cannot write to clipboard: {e}"}


clipboard_tool_declarations = [
    FunctionDeclaration(
        name="get_clipboard",
        description="Read the current text content from the system clipboard",
        parameters={"type": "object", "properties": {}},
    ),
    FunctionDeclaration(
        name="set_clipboard",
        description="Copy text to the system clipboard",
        parameters={"type": "object", "properties": {
            "text": {"type": "string", "description": "Text to copy to clipboard"},
        }, "required": ["text"]},
    ),
]

tool_functions = {
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
}
