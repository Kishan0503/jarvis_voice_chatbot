import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Centralized configuration loaded from environment variables."""

    # --- Legacy Gemini (kept for reference) ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # --- NVIDIA NIM / OpenAI-compatible API ---
    NVIDIA_API_KEY = os.getenv(
        "NVIDIA_API_KEY",
        "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",
    )
    NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
    # llama-3.3-70b handles LangGraph ReAct agent prompting reliably
    NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct")

    # --- External APIs ---
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
    GOOGLE_CSE_CX = os.getenv("GOOGLE_CSE_CX")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "")

    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY environment variable not set.")
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY environment variable not set.")


app_config = Config()
