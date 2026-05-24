from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer
from PyQt6.QtGui import QFont
from ui.styles import JARVIS_THEME as T, FONT_HEADING, FONT_BODY, FONT_SIZE_TINY, FONT_SIZE_SMALL


class _StatRow(QWidget):
    """A single stat: label on left, value on right."""

    def __init__(self, label: str, initial_value: str = "0", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(4)

        lbl = QLabel(label.upper())
        lbl.setFont(QFont(FONT_HEADING, FONT_SIZE_TINY, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {T['text_dim']}; letter-spacing: 1px;")
        layout.addWidget(lbl)

        layout.addStretch()

        self._value = QLabel(initial_value)
        self._value.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        self._value.setStyleSheet(f"color: {T['cyan']};")
        self._value.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._value)

    def set_value(self, text: str):
        self._value.setText(text)


class SessionStats(QWidget):
    """Live session stats: uptime, messages, tools used, memory status."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setMinimumHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(2)

        self._uptime_row = _StatRow("Session", "00m 00s")
        self._messages_row = _StatRow("Messages", "0")
        self._tools_row = _StatRow("Tools", "0")
        self._memory_row = _StatRow("Memory", "idle")

        layout.addStretch()
        layout.addWidget(self._uptime_row)
        layout.addWidget(self._messages_row)
        layout.addWidget(self._tools_row)
        layout.addWidget(self._memory_row)
        layout.addStretch()

        self._message_count = 0
        self._tool_count = 0

        self._elapsed = QElapsedTimer()
        self._elapsed.start()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_uptime)
        self._timer.start(1000)

    def _update_uptime(self):
        ms = self._elapsed.elapsed()
        total_secs = ms // 1000
        hours = total_secs // 3600
        mins = (total_secs % 3600) // 60
        secs = total_secs % 60

        if hours > 0:
            self._uptime_row.set_value(f"{hours}h {mins:02d}m")
        else:
            self._uptime_row.set_value(f"{mins:02d}m {secs:02d}s")

    def increment_messages(self):
        self._message_count += 1
        self._messages_row.set_value(str(self._message_count))

    def increment_tools(self):
        self._tool_count += 1
        self._tools_row.set_value(str(self._tool_count))

    def set_memory_status(self, status: str):
        self._memory_row.set_value(status)
