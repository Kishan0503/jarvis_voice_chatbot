import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QLinearGradient
from ui.styles import JARVIS_THEME as T


class WaveformVisualizer(QWidget):
    """
    Mini audio waveform visualizer. Shows animated bars that react to
    audio amplitude. Flat-line when idle, animated when active.
    """

    NUM_BARS = 24
    BAR_GAP = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self._amplitude = 0.0
        self._bars = [0.0] * self.NUM_BARS
        self._target_bars = [0.0] * self.NUM_BARS
        self._state = "idle"

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)

        self._phase = 0.0

    def set_amplitude(self, value: float):
        self._amplitude = max(0.0, min(1.0, value))

    def set_state(self, state: str):
        """Set state: 'idle', 'listening', 'speaking', 'thinking'"""
        self._state = state

    def _animate(self):
        self._phase += 0.12
        n = self.NUM_BARS

        if self._state == "idle":
            for i in range(n):
                wave = 0.05 + 0.03 * math.sin(self._phase + i * 0.3)
                self._target_bars[i] = wave
        elif self._state in ("listening", "speaking"):
            amp = max(0.1, self._amplitude)
            for i in range(n):
                center_factor = 1.0 - abs(i - n / 2) / (n / 2) * 0.5
                wave = amp * center_factor * (0.4 + 0.6 * abs(math.sin(self._phase * 1.5 + i * 0.4)))
                noise = random.uniform(-0.05, 0.05) * amp
                self._target_bars[i] = max(0.03, min(1.0, wave + noise))
        elif self._state == "thinking":
            for i in range(n):
                pulse = 0.15 + 0.1 * math.sin(self._phase * 2.0 + i * 0.2)
                self._target_bars[i] = pulse

        smoothing = 0.3
        for i in range(n):
            self._bars[i] += (self._target_bars[i] - self._bars[i]) * smoothing

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        n = self.NUM_BARS
        total_gap = (n - 1) * self.BAR_GAP
        bar_width = max(2, (w - total_gap) / n)
        center_y = h / 2

        if self._state == "idle":
            color_top = QColor(T["hud_border"])
            color_bot = QColor(T["hud_border"])
        elif self._state == "listening":
            color_top = QColor(T["cyan"])
            color_bot = QColor(T["primary"])
        elif self._state == "speaking":
            color_top = QColor(T["accent"])
            color_bot = QColor(T["cyan"])
        else:
            color_top = QColor(T["warning"])
            color_bot = QColor(T["hud_border"])

        for i in range(n):
            bar_h = max(2, self._bars[i] * (h * 0.8))
            x = i * (bar_width + self.BAR_GAP)
            y_top = center_y - bar_h / 2
            y_bot = center_y + bar_h / 2

            gradient = QLinearGradient(x, y_top, x, y_bot)
            gradient.setColorAt(0.0, color_top)
            gradient.setColorAt(0.5, QColor(color_top.red(), color_top.green(), color_top.blue(), 200))
            gradient.setColorAt(1.0, color_bot)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(gradient)
            painter.drawRoundedRect(
                int(x), int(y_top), int(bar_width), int(bar_h),
                1, 1,
            )

        painter.end()
