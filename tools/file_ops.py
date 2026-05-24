import os
import glob
import subprocess
from datetime import datetime
from typing import Dict, Any
from google.generativeai.types import FunctionDeclaration


def find_files(pattern: str, search_path: str = "") -> Dict[str, Any]:
    """Search for files matching a glob pattern."""
    if not search_path:
        search_path = os.path.expanduser("~")

    search_path = os.path.expanduser(search_path)
    if not os.path.isdir(search_path):
        return {"status": "error", "message": f"Directory not found: {search_path}"}

    full_pattern = os.path.join(search_path, "**", pattern)
    try:
        matches = glob.glob(full_pattern, recursive=True)[:20]
        return {
            "status": "success",
            "files": matches,
            "count": len(matches),
            "search_path": search_path,
            "pattern": pattern,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def read_file_content(filepath: str) -> Dict[str, Any]:
    """Read the text content of a file (limited to 5000 chars)."""
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"File not found: {filepath}"}
    if not os.path.isfile(filepath):
        return {"status": "error", "message": f"Not a file: {filepath}"}

    try:
        with open(filepath, "r", errors="replace") as f:
            content = f.read(5000)
        truncated = os.path.getsize(filepath) > 5000
        return {
            "status": "success",
            "content": content,
            "truncated": truncated,
            "filepath": filepath,
        }
    except Exception as e:
        return {"status": "error", "message": f"Cannot read file: {e}"}


def list_directory(path: str = "") -> Dict[str, Any]:
    """List files and folders in a directory."""
    if not path:
        path = os.path.expanduser("~")

    path = os.path.expanduser(path)
    if not os.path.isdir(path):
        return {"status": "error", "message": f"Directory not found: {path}"}

    try:
        entries = []
        for name in sorted(os.listdir(path))[:50]:
            full = os.path.join(path, name)
            entry_type = "dir" if os.path.isdir(full) else "file"
            entries.append({"name": name, "type": entry_type})
        return {"status": "success", "path": path, "entries": entries, "count": len(entries)}
    except PermissionError:
        return {"status": "error", "message": f"Permission denied: {path}"}


def get_file_info(filepath: str) -> Dict[str, Any]:
    """Get metadata about a file: size, modified date, type."""
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"Not found: {filepath}"}

    try:
        stat = os.stat(filepath)
        return {
            "status": "success",
            "filepath": filepath,
            "size_bytes": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "is_directory": os.path.isdir(filepath),
            "extension": os.path.splitext(filepath)[1] or "(none)",
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def open_file_default(filepath: str) -> Dict[str, Any]:
    """Open a file with the system's default application."""
    filepath = os.path.expanduser(filepath)
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"Not found: {filepath}"}

    try:
        subprocess.Popen(["xdg-open", filepath], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "success", "message": f"Opened {os.path.basename(filepath)}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


file_tool_declarations = [
    FunctionDeclaration(
        name="find_files",
        description="Search for files matching a pattern (glob) in a directory",
        parameters={"type": "object", "properties": {
            "pattern": {"type": "string", "description": "File name or glob pattern (e.g., '*.py', 'report*.pdf')"},
            "search_path": {"type": "string", "description": "Directory to search in (default: home directory)"},
        }, "required": ["pattern"]},
    ),
    FunctionDeclaration(
        name="read_file_content",
        description="Read the text content of a file",
        parameters={"type": "object", "properties": {
            "filepath": {"type": "string", "description": "Full path to the file"},
        }, "required": ["filepath"]},
    ),
    FunctionDeclaration(
        name="list_directory",
        description="List files and folders in a directory",
        parameters={"type": "object", "properties": {
            "path": {"type": "string", "description": "Directory path (default: home directory)"},
        }},
    ),
    FunctionDeclaration(
        name="get_file_info",
        description="Get information about a file (size, modified date, type)",
        parameters={"type": "object", "properties": {
            "filepath": {"type": "string", "description": "Path to the file"},
        }, "required": ["filepath"]},
    ),
    FunctionDeclaration(
        name="open_file_default",
        description="Open a file with the default system application",
        parameters={"type": "object", "properties": {
            "filepath": {"type": "string", "description": "Path to the file to open"},
        }, "required": ["filepath"]},
    ),
]

tool_functions = {
    "find_files": find_files,
    "read_file_content": read_file_content,
    "list_directory": list_directory,
    "get_file_info": get_file_info,
    "open_file_default": open_file_default,
}
