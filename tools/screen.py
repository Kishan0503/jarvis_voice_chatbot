import os
import tempfile
from typing import Dict, Any
from google.generativeai.types import FunctionDeclaration
import mss


def take_screenshot() -> Dict[str, Any]:
    """Capture the entire screen and save to a temp PNG file."""
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)

            fd, filepath = tempfile.mkstemp(suffix=".png", prefix="jarvis_screen_")
            os.close(fd)

            from PIL import Image
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.save(filepath)

            return {
                "status": "success",
                "filepath": filepath,
                "resolution": f"{screenshot.width}x{screenshot.height}",
                "message": "Screenshot captured",
            }
    except Exception as e:
        return {"status": "error", "message": f"Screenshot failed: {e}"}


screen_tool_declarations = [
    FunctionDeclaration(
        name="take_screenshot",
        description="Take a screenshot of the entire screen",
        parameters={"type": "object", "properties": {}},
    ),
]

tool_functions = {
    "take_screenshot": take_screenshot,
}
