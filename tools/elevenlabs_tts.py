from elevenlabs.client import ElevenLabs
from config import app_config
from typing import Iterator

client = ElevenLabs(api_key=app_config.ELEVENLABS_API_KEY)

JARVIS_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam - British male voice


def text_to_speech_stream(text: str) -> Iterator[bytes]:
    """
    Convert text to speech using ElevenLabs API and stream the audio data.
    Returns an iterator of MP3 audio bytes.
    """
    try:
        audio_stream = client.text_to_speech.stream(
            text=text,
            voice_id=JARVIS_VOICE_ID,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        return audio_stream

    except Exception as e:
        print(f"ElevenLabs TTS error: {e}")
        return iter([])
