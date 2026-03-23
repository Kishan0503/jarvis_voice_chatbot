import psutil
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from ui.styles import JARVIS_THEME as T, FONT_HEADING, FONT_BODY, FONT_SIZE_TINY, FONT_SIZE_SMALL


class MetricBar(QWidget):
    """A single labeled metric with a color-coded progress bar."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)

        self._label = QLabel(label.upper())
        self._label.setFont(QFont(FONT_HEADING, FONT_SIZE_TINY, QFont.Weight.Bold))
        self._label.setStyleSheet(f"color: {T['text_dim']}; letter-spacing: 1px;")
        self._label.setFixedWidth(36)
        layout.addWidget(self._label)

        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._update_bar_style(0)
        layout.addWidget(self._bar, stretch=1)

        self._value_label = QLabel("0%")
        self._value_label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        self._value_label.setStyleSheet(f"color: {T['text']};")
        self._value_label.setFixedWidth(32)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self._value_label)

    def set_value(self, percent: int, suffix: str = "%"):
        percent = max(0, min(100, percent))
        self._bar.setValue(percent)
        self._value_label.setText(f"{percent}{suffix}")
        self._update_bar_style(percent)

    def _update_bar_style(self, percent: int):
        if percent < 60:
            color = T["success"]
        elif percent < 80:
            color = T["warning"]
        else:
            color = T["danger"]

        self._bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {T['bg_darker']};
                border: none;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)


class SystemMetrics(QWidget):
    """Live system resource monitor with color-coded progress bars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._cpu_bar = MetricBar("CPU")
        self._ram_bar = MetricBar("RAM")
        self._disk_bar = MetricBar("DISK")
        self._net_bar = MetricBar("NET")
        self._temp_bar = MetricBar("TEMP")

        layout.addWidget(self._cpu_bar)
        layout.addWidget(self._ram_bar)
        layout.addWidget(self._disk_bar)
        layout.addWidget(self._net_bar)
        layout.addWidget(self._temp_bar)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(2000)

        self._last_net = psutil.net_io_counters()
        self._update()

    def _update(self):
        self._cpu_bar.set_value(int(psutil.cpu_percent(interval=None)))
        self._ram_bar.set_value(int(psutil.virtual_memory().percent))
        self._disk_bar.set_value(int(psutil.disk_usage("/").percent))

        net = psutil.net_io_counters()
        sent_delta = (net.bytes_sent - self._last_net.bytes_sent) / 2
        recv_delta = (net.bytes_recv - self._last_net.bytes_recv) / 2
        self._last_net = net
        total_kbps = int((sent_delta + recv_delta) / 1024)
        net_percent = min(100, total_kbps)
        self._net_bar.set_value(net_percent, suffix=f"k")

        try:
            temps = psutil.sensors_temperatures()
            if temps:
                first_sensor = list(temps.values())[0]
                if first_sensor:
                    temp_c = int(first_sensor[0].current)
                    temp_pct = min(100, max(0, int((temp_c / 100) * 100)))
                    self._temp_bar.set_value(temp_pct, suffix="°C")
                    self._temp_bar._value_label.setText(f"{temp_c}°C")
                    return
        except Exception:
            pass
        self._temp_bar.set_value(0, suffix="°C")
        self._temp_bar._value_label.setText("N/A")
