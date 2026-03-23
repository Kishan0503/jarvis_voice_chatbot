import os
import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
import pygame


class AudioPlayer(QThread):
    """
    Plays MP3/WAV audio files using pygame.mixer.
    Emits amplitude_changed for driving avatar glow/waveform during playback.
    Emits playback_finished when the audio ends.
    """
    amplitude_changed = pyqtSignal(float)
    playback_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._filepath: str | None = None
        self._stop_requested = False

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)

    def play(self, filepath: str):
        """Queue a file to play. Stops any current playback first."""
        self._stop_requested = False
        self._filepath = filepath
        if not self.isRunning():
            self.start()

    def stop_playback(self):
        self._stop_requested = True
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def is_playing(self) -> bool:
        try:
            return pygame.mixer.music.get_busy()
        except Exception:
            return False

    def run(self):
        if not self._filepath or not os.path.exists(self._filepath):
            self.error_occurred.emit("Audio file not found")
            self.playback_finished.emit()
            return

        try:
            pygame.mixer.music.load(self._filepath)
            pygame.mixer.music.play()

            self._emit_simulated_amplitude()

            if not self._stop_requested:
                self.amplitude_changed.emit(0.0)
                self.playback_finished.emit()

        except Exception as e:
            self.error_occurred.emit(f"Playback error: {e}")
            self.amplitude_changed.emit(0.0)
            self.playback_finished.emit()

    def _emit_simulated_amplitude(self):
        """
        Emit amplitude values during playback. Since pygame.mixer doesn't
        expose raw PCM amplitude in real-time, we simulate a natural speech
        envelope synced to playback duration.
        """
        import math
        phase = 0.0
        while pygame.mixer.music.get_busy() and not self._stop_requested:
            phase += 0.15
            base = 0.3 + 0.2 * math.sin(phase * 0.7)
            variation = 0.15 * math.sin(phase * 2.3) + 0.1 * math.sin(phase * 3.7)
            amp = max(0.1, min(1.0, base + variation))
            self.amplitude_changed.emit(amp)
            self.msleep(50)
