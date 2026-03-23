import os
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from voice.stt import STTWorker
from voice.tts import TTSWorker
from voice.audio_player import AudioPlayer
from auth.local_user import local_user


class State(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class Orchestrator(QObject):
    """
    Manages the listen -> think -> speak -> listen cycle.
    Coordinates STT, TTS, and audio playback threads.

    Guards against echo feedback (mic picking up speaker output) and
    duplicate processing (multiple transcription signals firing).
    """

    state_changed = pyqtSignal(str)
    amplitude_changed = pyqtSignal(float)
    transcription_ready = pyqtSignal(str)
    jarvis_reply_ready = pyqtSignal(str)
    tts_engine_used = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    send_to_gemini = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = State.IDLE
        self._stt_worker: STTWorker | None = None
        self._tts_worker: TTSWorker | None = None
        self._audio_player = AudioPlayer()
        self._tts_preference = local_user.get_preference("tts_engine", "elevenlabs")

        self._processing_lock = False

        self._audio_player.amplitude_changed.connect(self._on_playback_amplitude)
        self._audio_player.playback_finished.connect(self._on_playback_finished)
        self._audio_player.error_occurred.connect(self._on_error)

    @property
    def state(self) -> State:
        return self._state

    def _set_state(self, new_state: State):
        self._state = new_state
        self.state_changed.emit(new_state.value)

    # --- Public controls ---

    def start_listening(self):
        """Start microphone capture and STT. Called by mic button click."""
        if self._state == State.SPEAKING:
            self.stop_speaking()

        if self._state == State.PROCESSING:
            return

        if self._state == State.LISTENING:
            self.stop_listening()
            return

        self._processing_lock = False
        self._set_state(State.LISTENING)
        self._stt_worker = STTWorker(model_size="base")
        self._stt_worker.transcription_ready.connect(self._on_transcription)
        self._stt_worker.amplitude_changed.connect(self._on_mic_amplitude)
        self._stt_worker.error_occurred.connect(self._on_error)
        self._stt_worker.start()

    def stop_listening(self):
        """Stop microphone capture. Disconnects signals first to prevent late emissions."""
        if self._stt_worker:
            try:
                self._stt_worker.transcription_ready.disconnect(self._on_transcription)
                self._stt_worker.amplitude_changed.disconnect(self._on_mic_amplitude)
                self._stt_worker.error_occurred.disconnect(self._on_error)
            except (TypeError, RuntimeError):
                pass
            self._stt_worker.stop()
            self._stt_worker.wait(3000)
            self._stt_worker = None
        self.amplitude_changed.emit(0.0)
        if self._state == State.LISTENING:
            self._set_state(State.IDLE)

    def stop_speaking(self):
        """Stop TTS playback immediately."""
        self._audio_player.stop_playback()
        self.amplitude_changed.emit(0.0)
        self._processing_lock = False
        self._set_state(State.IDLE)

    def stop_all(self):
        """Emergency stop: kill everything, return to idle."""
        self._processing_lock = False
        if self._stt_worker:
            try:
                self._stt_worker.transcription_ready.disconnect()
                self._stt_worker.amplitude_changed.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._stt_worker.stop()
            self._stt_worker.wait(3000)
            self._stt_worker = None

        self._audio_player.stop_playback()

        if self._tts_worker and self._tts_worker.isRunning():
            self._tts_worker.quit()
            self._tts_worker.wait(2000)
            self._tts_worker = None

        self.amplitude_changed.emit(0.0)
        self._set_state(State.IDLE)

    # --- Handle text input (typed messages) ---

    def handle_text_input(self, text: str):
        """Process a typed message (skip STT, go straight to Gemini)."""
        if self._processing_lock:
            return
        if self._state == State.SPEAKING:
            self.stop_speaking()
        self._processing_lock = True
        self._set_state(State.PROCESSING)
        self.send_to_gemini.emit(text)

    # --- Gemini response callback ---

    @pyqtSlot(str)
    def on_gemini_response(self, reply: str):
        """Called by the app when Gemini returns a response."""
        if self._state != State.PROCESSING:
            return
        self.jarvis_reply_ready.emit(reply)
        self._speak(reply)

    # --- Internal handlers ---

    def _on_transcription(self, text: str):
        """
        STT produced text. Immediately disconnect signals and stop mic
        to prevent any further transcriptions (echo guard).
        """
        if self._processing_lock:
            return

        self._processing_lock = True

        if self._stt_worker:
            try:
                self._stt_worker.transcription_ready.disconnect(self._on_transcription)
            except (TypeError, RuntimeError):
                pass

        self.stop_listening()
        self.transcription_ready.emit(text)
        self._set_state(State.PROCESSING)
        self.send_to_gemini.emit(text)

    def _speak(self, text: str):
        """Generate TTS audio and play it. Mic is guaranteed off at this point."""
        self.stop_listening()
        self._set_state(State.SPEAKING)
        self._tts_preference = local_user.get_preference("tts_engine", "elevenlabs")
        self._tts_worker = TTSWorker(text, self._tts_preference)
        self._tts_worker.audio_ready.connect(self._on_tts_audio_ready)
        self._tts_worker.tts_engine_used.connect(self.tts_engine_used.emit)
        self._tts_worker.error_occurred.connect(self._on_tts_error)
        self._tts_worker.start()

    def _on_tts_audio_ready(self, filepath: str):
        self._audio_player.play(filepath)

    def _on_tts_error(self, msg: str):
        self.error_occurred.emit(f"TTS: {msg}")
        self._processing_lock = False
        self._set_state(State.IDLE)

    def _on_mic_amplitude(self, amp: float):
        if self._state == State.LISTENING:
            self.amplitude_changed.emit(amp)

    def _on_playback_amplitude(self, amp: float):
        if self._state == State.SPEAKING:
            self.amplitude_changed.emit(amp)

    def _on_playback_finished(self):
        """Audio finished playing. Release the processing lock."""
        self.amplitude_changed.emit(0.0)
        self._cleanup_temp_audio()
        self._processing_lock = False
        self._set_state(State.IDLE)

    def _on_error(self, msg: str):
        self.error_occurred.emit(msg)
        self._processing_lock = False
        self._set_state(State.IDLE)

    def _cleanup_temp_audio(self):
        import glob
        import tempfile
        temp_dir = tempfile.gettempdir()
        for pattern in ["jarvis_tts_*.mp3", "jarvis_edge_*.mp3", "jarvis_pyttsx3_*.wav"]:
            for f in glob.glob(os.path.join(temp_dir, pattern)):
                try:
                    os.unlink(f)
                except OSError:
                    pass
