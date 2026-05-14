import os
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
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
    Manages the listen → think → speak → idle cycle.

    Streaming TTS pipeline (new)
    ----------------------------
    Instead of one big TTS call for the full reply, the orchestrator now
    receives individual sentences from the AgentWorker as they stream in:

        AgentWorker.sentence_ready(sentence)
               │
               ▼
        on_sentence_ready()  ← called per sentence, immediately starts TTS
               │
               ▼
        TTSWorker(sentence) → audio file → AudioPlayer.enqueue()
               │
               ▼
        AudioPlayer plays queued files sequentially

    Ordered playback
    ----------------
    TTS workers run concurrently for speed, but audio files are enqueued
    in original sentence order via an indexed dict (_tts_order).

    IDLE detection
    --------------
    A QTimer polls every 250 ms after reply_complete fires.  The system
    returns to IDLE only when all TTS workers are done AND the AudioPlayer
    queue is empty AND nothing is currently playing.
    """

    # Outbound signals (consumed by JarvisApp / MainWindow)
    state_changed = pyqtSignal(str)
    amplitude_changed = pyqtSignal(float)
    transcription_ready = pyqtSignal(str)
    jarvis_reply_ready = pyqtSignal(str)        # full reply → transcript
    tts_engine_used = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    send_to_agent = pyqtSignal(str)             # triggers AgentWorker

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = State.IDLE
        self._stt_worker: STTWorker | None = None
        self._audio_player = AudioPlayer()
        self._tts_preference = local_user.get_preference("tts_engine", "elevenlabs")

        self._processing_lock = False

        # Streaming TTS state
        self._tts_workers: list[TTSWorker] = []
        self._tts_order: dict[int, str] = {}   # {slot_idx: filepath}
        self._tts_counter = 0                   # next slot to allocate
        self._next_to_play = 0                  # next slot to enqueue
        self._streaming_complete = False        # True after reply_complete fires

        # Poll timer for IDLE detection after streaming completes
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(250)
        self._idle_timer.timeout.connect(self._check_idle)

        # Audio player signals
        self._audio_player.amplitude_changed.connect(self._on_playback_amplitude)
        self._audio_player.error_occurred.connect(self._on_error)

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def state(self) -> State:
        return self._state

    def _set_state(self, new_state: State):
        self._state = new_state
        self.state_changed.emit(new_state.value)

    # ------------------------------------------------------------------
    # Public controls
    # ------------------------------------------------------------------

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
        """Stop microphone capture."""
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
        """Interrupt TTS playback and return to IDLE immediately."""
        self._idle_timer.stop()
        self._audio_player.stop_all()
        self._stop_all_tts()
        self.amplitude_changed.emit(0.0)
        self._reset_streaming_state()
        self._processing_lock = False
        self._set_state(State.IDLE)

    def stop_all(self):
        """Emergency stop: kill everything, return to IDLE."""
        self._idle_timer.stop()
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

        self._audio_player.stop_all()
        self._stop_all_tts()
        self.amplitude_changed.emit(0.0)
        self._reset_streaming_state()
        self._set_state(State.IDLE)

    def handle_text_input(self, text: str):
        """Process a typed message — skip STT, go straight to the agent."""
        if self._processing_lock:
            return
        if self._state == State.SPEAKING:
            self.stop_speaking()
        self._processing_lock = True
        self._set_state(State.PROCESSING)
        self.send_to_agent.emit(text)

    # ------------------------------------------------------------------
    # Streaming sentence pipeline (called by AgentWorker signals)
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def on_sentence_ready(self, sentence: str):
        """
        Called for each complete sentence streamed from the agent.
        Immediately dispatches a TTSWorker for this sentence.
        Audio files are enqueued to AudioPlayer in original sentence order.
        """
        if self._state not in (State.PROCESSING, State.SPEAKING):
            return

        self._set_state(State.SPEAKING)

        slot = self._tts_counter
        self._tts_counter += 1

        self._tts_preference = local_user.get_preference("tts_engine", "elevenlabs")
        tts = TTSWorker(sentence, self._tts_preference)
        # Use default argument capture to bind the current slot value
        tts.audio_ready.connect(lambda fp, s=slot: self._on_ordered_audio(s, fp))
        tts.tts_engine_used.connect(self.tts_engine_used.emit)
        tts.error_occurred.connect(self._on_tts_error)
        self._tts_workers.append(tts)
        tts.start()

    def _on_ordered_audio(self, slot: int, filepath: str):
        """
        Receive a TTS-generated audio file and enqueue in sentence order.
        Concurrent TTS workers may finish out of order; this method holds
        early-arriving files until all previous slots are filled.
        """
        self._tts_order[slot] = filepath
        while self._next_to_play in self._tts_order:
            fp = self._tts_order.pop(self._next_to_play)
            self._audio_player.enqueue(fp)
            self._next_to_play += 1

    @pyqtSlot(str, list)
    def on_reply_complete(self, full_text: str, tools_used: list):
        """
        Called when the agent stream ends.  Stores the full reply for the
        transcript and starts the idle-detection poll timer.
        """
        self.jarvis_reply_ready.emit(full_text)
        self._streaming_complete = True
        self._idle_timer.start()

    # ------------------------------------------------------------------
    # IDLE detection
    # ------------------------------------------------------------------

    def _check_idle(self):
        """
        Polled every 250 ms after streaming completes.
        Returns to IDLE when all TTS workers are done and the AudioPlayer
        queue is empty and nothing is playing.
        """
        if not self._streaming_complete:
            return

        # Any TTS still generating audio?
        if any(w.isRunning() for w in self._tts_workers):
            return

        # Any audio still enqueued or playing?
        if self._audio_player.has_queued() or self._audio_player.is_playing():
            return

        # Also wait for the AudioPlayer thread itself to finish
        if self._audio_player.isRunning():
            return

        self._idle_timer.stop()
        self.amplitude_changed.emit(0.0)
        self._reset_streaming_state()
        self._processing_lock = False
        self._set_state(State.IDLE)

    # ------------------------------------------------------------------
    # STT callbacks
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _on_transcription(self, text: str):
        """STT produced text. Lock processing and dispatch to agent."""
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
        self.send_to_agent.emit(text)

    # ------------------------------------------------------------------
    # Amplitude passthrough
    # ------------------------------------------------------------------

    def _on_mic_amplitude(self, amp: float):
        if self._state == State.LISTENING:
            self.amplitude_changed.emit(amp)

    def _on_playback_amplitude(self, amp: float):
        if self._state == State.SPEAKING:
            self.amplitude_changed.emit(amp)

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _on_tts_error(self, msg: str):
        self.error_occurred.emit(f"TTS: {msg}")

    def _on_error(self, msg: str):
        self.error_occurred.emit(msg)
        self._processing_lock = False
        self._set_state(State.IDLE)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _stop_all_tts(self):
        """Gracefully stop all active TTS workers."""
        for w in self._tts_workers:
            try:
                if w.isRunning():
                    w.quit()
                    w.wait(1000)
            except RuntimeError:
                pass
        self._tts_workers.clear()

    def _reset_streaming_state(self):
        """Clear all per-turn streaming bookkeeping."""
        self._tts_order.clear()
        self._tts_counter = 0
        self._next_to_play = 0
        self._streaming_complete = False
        self._tts_workers.clear()
