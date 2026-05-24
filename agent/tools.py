"""
LangChain @tool wrappers for all 18 Jarvis tools.

Each wrapper delegates 100% to the existing implementation in tools/*.py —
no logic lives here. The @tool decorator:
  - Derives the JSON schema from type annotations
  - Uses the docstring as the tool description shown to the LLM
  - Returns a BaseTool instance compatible with LangGraph's ToolNode
"""

from langchain_core.tools import tool

# --- Existing implementations (unchanged) ---
from tools.weather import get_current_weather as _weather
from tools.calendar import get_current_datetime as _datetime
from tools.search import google_search as _search
from tools.system_control import (
    open_application as _open_app,
    close_application as _close_app,
    list_running_apps as _list_apps,
    get_system_info as _sys_info,
    set_system_volume as _set_volume,
    lock_screen as _lock_screen,
)
from tools.file_ops import (
    find_files as _find_files,
    read_file_content as _read_file,
    list_directory as _list_dir,
    get_file_info as _file_info,
    open_file_default as _open_file,
)
from tools.clipboard import (
    get_clipboard as _get_clip,
    set_clipboard as _set_clip,
)
from tools.screen import take_screenshot as _screenshot
from tools.notes import (
    save_note as _save_note,
    list_notes as _list_notes,
    delete_note as _delete_note,
)


# ===========================================================================
# Weather
# ===========================================================================

@tool
def get_current_weather(location: str, unit: str = "celsius") -> dict:
    """Get the current weather for a given location (city, state, or country).

    Args:
        location: The city, state, or country — e.g. 'Mumbai', 'London', 'India'.
        unit: Temperature unit — 'celsius' or 'fahrenheit'. Defaults to 'celsius'.
    """
    return _weather(location=location, unit=unit)


# ===========================================================================
# Date / Time
# ===========================================================================

@tool
def get_current_datetime() -> dict:
    """Get the current date, time, day of week, month, and year."""
    return _datetime()


# ===========================================================================
# Web Search
# ===========================================================================

@tool
def google_search(query: str) -> dict:
    """Search Google for real-time information, current events, or any topic.

    Use this for any question requiring knowledge beyond your training data.
    Summarise the results briefly in your reply.

    Args:
        query: The search query string.
    """
    return _search(query=query)


# ===========================================================================
# System Control
# ===========================================================================

@tool
def open_application(name: str) -> dict:
    """Open / launch an application by name.

    Args:
        name: Application name — e.g. 'firefox', 'terminal', 'calculator'.
    """
    return _open_app(name=name)


@tool
def close_application(name: str) -> dict:
    """Close / terminate a running application by name.

    Args:
        name: Application name to close — e.g. 'firefox', 'chrome'.
    """
    return _close_app(name=name)


@tool
def list_running_apps() -> dict:
    """List all currently running user-space applications."""
    return _list_apps()


@tool
def get_system_info() -> dict:
    """Get live system stats: CPU usage, RAM, disk space, and battery level."""
    return _sys_info()


@tool
def set_system_volume(level: int) -> dict:
    """Set the system audio volume.

    Args:
        level: Volume level from 0 (mute) to 100 (maximum).
    """
    return _set_volume(level=level)


@tool
def lock_screen() -> dict:
    """Lock the desktop session screen immediately."""
    return _lock_screen()


# ===========================================================================
# File Operations
# ===========================================================================

@tool
def find_files(pattern: str, search_path: str = "") -> dict:
    """Search for files matching a glob pattern.

    Args:
        pattern: File name or glob pattern — e.g. '*.py', 'report*.pdf'.
        search_path: Directory to search (default: user home directory).
    """
    return _find_files(pattern=pattern, search_path=search_path)


@tool
def read_file_content(filepath: str) -> dict:
    """Read the text content of a file (up to 5 000 characters).

    Args:
        filepath: Full absolute path to the file.
    """
    return _read_file(filepath=filepath)


@tool
def list_directory(path: str = "") -> dict:
    """List files and folders inside a directory.

    Args:
        path: Directory path (default: user home directory).
    """
    return _list_dir(path=path)


@tool
def get_file_info(filepath: str) -> dict:
    """Get metadata for a file: size, last-modified date, and type.

    Args:
        filepath: Path to the file.
    """
    return _file_info(filepath=filepath)


@tool
def open_file_default(filepath: str) -> dict:
    """Open a file with the system's default application.

    Args:
        filepath: Path to the file to open.
    """
    return _open_file(filepath=filepath)


# ===========================================================================
# Clipboard
# ===========================================================================

@tool
def get_clipboard() -> dict:
    """Read the current text content from the system clipboard."""
    return _get_clip()


@tool
def set_clipboard(text: str) -> dict:
    """Copy text to the system clipboard.

    Args:
        text: The text to copy.
    """
    return _set_clip(text=text)


# ===========================================================================
# Screen
# ===========================================================================

@tool
def take_screenshot() -> dict:
    """Capture a screenshot of the entire screen and save it to a temp file."""
    return _screenshot()


# ===========================================================================
# Notes (persisted to SQLite at ~/.jarvis/jarvis.db)
# ===========================================================================

@tool
def save_note(content: str) -> dict:
    """Save a new note. Use when the user asks to remember or note something.

    Args:
        content: The note content to save.
    """
    return _save_note(content=content)


@tool
def list_notes() -> dict:
    """List all saved notes, newest first.
    Use when the user asks to see or view their notes.
    """
    return _list_notes()


@tool
def delete_note(note_id: int) -> dict:
    """Delete a specific note by its ID.

    Args:
        note_id: The integer ID of the note to delete.
    """
    return _delete_note(note_id=note_id)


# ===========================================================================
# Exported list — consumed by graph.py
# ===========================================================================

ALL_TOOLS = [
    get_current_weather,
    get_current_datetime,
    google_search,
    open_application,
    close_application,
    list_running_apps,
    get_system_info,
    set_system_volume,
    lock_screen,
    find_files,
    read_file_content,
    list_directory,
    get_file_info,
    open_file_default,
    get_clipboard,
    set_clipboard,
    take_screenshot,
    save_note,
    list_notes,
    delete_note,
]
