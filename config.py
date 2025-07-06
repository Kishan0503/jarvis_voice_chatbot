import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class to load environment variables.
    """
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
    GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
    GOOGLE_CSE_CX = os.getenv("GOOGLE_CSE_CX")

    # Basic validation (optional but recommended)
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY environment variable not set.")

# Create a single instance of Config to be imported elsewhere
app_config = Config()