import os
import tempfile
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal


class TTSWorker(QThread):
    """
    Converts text to speech audio file using a 3-tier fallback chain:
    1. ElevenLabs (best quality, needs API key + internet)
    2. edge-tts (free, natural voices, needs internet)
    3. pyttsx3 via espeak (offline last resort)

    Emits audio_ready(filepath) on success, or error_occurred(msg) on failure.
    """
    audio_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    tts_engine_used = pyqtSignal(str)

    def __init__(self, text: str, engine_preference: str = "elevenlabs", parent=None):
        super().__init__(parent)
        self._text = text
        self._engine_preference = engine_preference

    def run(self):
        if not self._text.strip():
            self.error_occurred.emit("Empty text")
            return

        engines = self._build_chain()
        for engine_name, engine_fn in engines:
            try:
                filepath = engine_fn(self._text)
                if filepath and os.path.exists(filepath):
                    self.tts_engine_used.emit(engine_name)
                    self.audio_ready.emit(filepath)
                    return
            except Exception as e:
                print(f"TTS {engine_name} failed: {e}")
                continue

        self.error_occurred.emit("All TTS engines failed")

    def _build_chain(self) -> list[tuple[str, callable]]:
        chain = []
        if self._engine_preference == "elevenlabs":
            chain.append(("elevenlabs", _elevenlabs_tts))
            chain.append(("edge-tts", _edge_tts))
            chain.append(("pyttsx3", _pyttsx3_tts))
        elif self._engine_preference == "edge-tts":
            chain.append(("edge-tts", _edge_tts))
            chain.append(("elevenlabs", _elevenlabs_tts))
            chain.append(("pyttsx3", _pyttsx3_tts))
        else:
            chain.append(("pyttsx3", _pyttsx3_tts))
            chain.append(("edge-tts", _edge_tts))
            chain.append(("elevenlabs", _elevenlabs_tts))
        return chain


def _elevenlabs_tts(text: str) -> str:
    """Use ElevenLabs API to generate speech. Returns path to MP3 file."""
    from tools.elevenlabs_tts import text_to_speech_stream

    audio_stream = text_to_speech_stream(text)
    chunks = list(audio_stream)
    if not chunks:
        raise RuntimeError("ElevenLabs returned empty audio stream")

    fd, filepath = tempfile.mkstemp(suffix=".mp3", prefix="jarvis_tts_")
    with os.fdopen(fd, "wb") as f:
        for chunk in chunks:
            f.write(chunk)

    if os.path.getsize(filepath) < 100:
        os.unlink(filepath)
        raise RuntimeError("ElevenLabs audio file too small")

    return filepath


def _edge_tts(text: str) -> str:
    """Use Microsoft Edge TTS (free, natural voices). Returns path to MP3."""
    import edge_tts

    voice = "en-GB-RyanNeural"
    fd, filepath = tempfile.mkstemp(suffix=".mp3", prefix="jarvis_edge_")
    os.close(fd)

    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(filepath)

    asyncio.run(_generate())

    if os.path.getsize(filepath) < 100:
        os.unlink(filepath)
        raise RuntimeError("Edge TTS audio file too small")

    return filepath


def _pyttsx3_tts(text: str) -> str:
    """Use pyttsx3 (offline, espeak backend). Returns path to WAV file."""
    import pyttsx3

    fd, filepath = tempfile.mkstemp(suffix=".wav", prefix="jarvis_pyttsx3_")
    os.close(fd)

    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.setProperty("volume", 0.9)

    voices = engine.getProperty("voices")
    for v in voices:
        if "english" in v.name.lower() and "male" in v.name.lower():
            engine.setProperty("voice", v.id)
            break

    engine.save_to_file(text, filepath)
    engine.runAndWait()

    if not os.path.exists(filepath) or os.path.getsize(filepath) < 100:
        raise RuntimeError("pyttsx3 failed to generate audio")

    return filepath
