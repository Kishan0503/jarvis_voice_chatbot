from elevenlabs.client import ElevenLabs
from config import app_config
from typing import Iterator

# Configure ElevenLabs with API key
client = ElevenLabs(api_key=app_config.ELEVENLABS_API_KEY)

# Creds: xebakol761@simerm.com - Xebako@098

# Voice IDs for Jarvis and Zara
VOICE_IDS = {
    # "jarvis": "pNInz6obpgDQGcFmaJgB",  # Adam - British male voice
    # "zara": "EXAVITQu4vr4xnSDxMaL"     # Rachel - American female voice
    "jarvis": "TxGEqnHWrfWFTfGW9XjX", # Elli - British male voice
    "zara": "AZnzlk1XvdvUeBnXmlld", # Domi - American female voice
}

def text_to_speech_stream(text: str, agent: str) -> Iterator[bytes]:
    """
    Convert text to speech using ElevenLabs API and stream the audio data.
    
    Args:
        text: The text to convert to speech
        agent: The agent name ('jarvis' or 'zara')
        
    Returns:
        Iterator[bytes]: Stream of audio data
    """
    try:
        # Get the appropriate voice ID
        voice_id = VOICE_IDS.get(agent.lower())
        if not voice_id:
            raise ValueError(f"Unknown agent: {agent}")

        # Generate and stream audio using the API
        audio_stream = client.text_to_speech.stream(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        return audio_stream

    except Exception as e:
        return iter([]) 