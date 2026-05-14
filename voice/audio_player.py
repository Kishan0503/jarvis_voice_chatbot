import os
import math
import queue
from PyQt6.QtCore import QThread, pyqtSignal
import pygame


class AudioPlayer(QThread):
    """
    Queue-based audio player for streaming sentence-by-sentence TTS playback.

    Usage
    -----
    Call enqueue(filepath) for each sentence audio file as it becomes ready.
    The player starts automatically on the first enqueue and keeps running
    until the queue drains or stop_all() is called.

    Signals
    -------
    amplitude_changed(float) : 0.0–1.0 simulated speech envelope (drives glow/waveform).
    all_finished()            : Emitted when the queue is empty and playback is done.
    error_occurred(str)       : Emitted on playback errors.
    """

    amplitude_changed = pyqtSignal(float)
    all_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: queue.Queue = queue.Queue()
        self._stop_requested = False

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enqueue(self, filepath: str):
        """Add an audio file to the playback queue. Starts the thread if idle."""
        if not os.path.exists(filepath):
            return
        self._stop_requested = False
        self._queue.put(filepath)
        if not self.isRunning():
            self.start()

    def stop_all(self):
        """Immediately stop playback and discard all queued files."""
        self._stop_requested = True
        self._drain_queue()
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.amplitude_changed.emit(0.0)

    def is_playing(self) -> bool:
        """True while pygame is actively playing audio."""
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False

    def has_queued(self) -> bool:
        """True if there are files waiting in the queue."""
        return not self._queue.empty()

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self):
        """
        Consume files from the queue sequentially.
        Waits up to 0.3 s for the next file before declaring the queue
        drained and emitting all_finished.
        """
        while not self._stop_requested:
            try:
                filepath = self._queue.get(timeout=0.3)
            except queue.Empty:
                # Queue drained naturally — streaming is done
                break

            if self._stop_requested:
                self._try_delete(filepath)
                break

            self._play_file(filepath)

        self.amplitude_changed.emit(0.0)
        if not self._stop_requested:
            self.all_finished.emit()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _play_file(self, filepath: str):
        try:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            self._emit_amplitude_during_playback()
        except Exception as e:
            self.error_occurred.emit(f"Playback error: {e}")
        finally:
            self._try_delete(filepath)

    def _emit_amplitude_during_playback(self):
        """Simulate a natural speech amplitude envelope synced to playback."""
        phase = 0.0
        while pygame.mixer.music.get_busy() and not self._stop_requested:
            phase += 0.15
            base = 0.3 + 0.2 * math.sin(phase * 0.7)
            variation = 0.15 * math.sin(phase * 2.3) + 0.1 * math.sin(phase * 3.7)
            amp = max(0.1, min(1.0, base + variation))
            self.amplitude_changed.emit(amp)
            self.msleep(50)

    def _drain_queue(self):
        """Discard all queued files and delete temp audio."""
        while not self._queue.empty():
            try:
                fp = self._queue.get_nowait()
                self._try_delete(fp)
            except queue.Empty:
                break

    @staticmethod
    def _try_delete(filepath: str):
        try:
            if filepath and os.path.exists(filepath):
                os.unlink(filepath)
        except OSError:
            pass
