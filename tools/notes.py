import sqlite3
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from google.generativeai.types import FunctionDeclaration

DB_PATH = Path.home() / ".jarvis" / "jarvis.db"


def _get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def save_note(content: str) -> Dict[str, Any]:
    """Save a new note."""
    if not content.strip():
        return {"status": "error", "message": "Note content cannot be empty"}

    try:
        conn = _get_db()
        cursor = conn.execute(
            "INSERT INTO notes (content) VALUES (?)", (content.strip(),)
        )
        conn.commit()
        note_id = cursor.lastrowid
        conn.close()
        return {
            "status": "success",
            "note_id": note_id,
            "message": f"Note saved: {content.strip()[:80]}",
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to save note: {e}"}


def list_notes() -> Dict[str, Any]:
    """List all saved notes, newest first."""
    try:
        conn = _get_db()
        rows = conn.execute(
            "SELECT id, content, created_at FROM notes ORDER BY created_at DESC"
        ).fetchall()
        conn.close()

        notes = []
        for row in rows:
            notes.append({
                "id": row[0],
                "content": row[1],
                "created_at": row[2],
            })

        if not notes:
            return {"status": "success", "notes": [], "message": "No notes found"}
        return {"status": "success", "notes": notes, "count": len(notes)}
    except Exception as e:
        return {"status": "error", "message": f"Failed to list notes: {e}"}


def delete_note(note_id: int) -> Dict[str, Any]:
    """Delete a note by its ID."""
    try:
        conn = _get_db()
        cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()

        if deleted:
            return {"status": "success", "message": f"Note {note_id} deleted"}
        return {"status": "not_found", "message": f"No note with ID {note_id}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete note: {e}"}


notes_tool_declarations = [
    FunctionDeclaration(
        name="save_note",
        description="Save a new note for the user. Use when the user asks to save, remember, or note something down.",
        parameters={"type": "object", "properties": {
            "content": {"type": "string", "description": "The note content to save"},
        }, "required": ["content"]},
    ),
    FunctionDeclaration(
        name="list_notes",
        description="List all saved notes. Use when the user asks to see, show, or view their notes.",
        parameters={"type": "object", "properties": {}},
    ),
    FunctionDeclaration(
        name="delete_note",
        description="Delete a specific note by its ID. Use when the user asks to delete or remove a note.",
        parameters={"type": "object", "properties": {
            "note_id": {"type": "integer", "description": "The ID of the note to delete"},
        }, "required": ["note_id"]},
    ),
]

tool_functions = {
    "save_note": save_note,
    "list_notes": list_notes,
    "delete_note": delete_note,
}
