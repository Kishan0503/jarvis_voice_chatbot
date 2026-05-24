import os
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox, QSizePolicy, QApplication, QSpacerItem,
)
from PyQt6.QtCore import (
    Qt, QTimer, QSize, pyqtSignal, pyqtSlot, QPoint, QPropertyAnimation,
    QEasingCurve,
)
from PyQt6.QtGui import (
    QFont, QMovie, QPainter, QColor, QPen, QBrush, QRadialGradient,
    QMouseEvent, QResizeEvent, QPixmap, QPainterPath,
)
import qtawesome as qta

from ui.styles import (
    JARVIS_THEME as T, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_TINY,
    FONT_SIZE_HEADING, FONT_SIZE_STATUS, FONT_SIZE_MEDIUM,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    BORDER_RADIUS, WINDOW_OPACITY, FONT_HEADING, FONT_BODY,
    AVATAR_OUTER_SIZE, AVATAR_GIF_SIZE,
    SIDEBAR_LEFT_WIDTH, SIDEBAR_RIGHT_WIDTH,
)
from ui.hud_frame import HudFrame
from ui.transcript_widget import TranscriptWidget
from ui.notes_panel import NotesPanel
from ui.notifications_panel import NotificationsPanel, ToastNotification
from ui.system_metrics import SystemMetrics
from ui.camera_widget import CameraWidget
from ui.waveform_widget import WaveformVisualizer
from ui.session_stats import SessionStats
from ui.settings_panel import SettingsPanel
from auth.local_user import local_user

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
RESIZE_MARGIN = 6

ICON_COLOR = T["text_dim"]
ICON_SIZE = 16


def _icon_btn(icon_name: str, tooltip: str, color: str = ICON_COLOR) -> QPushButton:
    btn = QPushButton()
    btn.setObjectName("iconBtn")
    btn.setIcon(qta.icon(icon_name, color=color))
    btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


class GlowRing(QWidget):
    def __init__(self, size: int = AVATAR_OUTER_SIZE, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._amplitude = 0.0
        self._base_glow = 0.15
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._idle_pulse)
        self._pulse_phase = 0.0
        self._pulse_timer.start(50)

    def set_amplitude(self, value: float):
        self._amplitude = max(0.0, min(1.0, value))
        self.update()

    def _idle_pulse(self):
        import math
        self._pulse_phase += 0.08
        if self._amplitude < 0.05:
            self._base_glow = 0.10 + 0.05 * math.sin(self._pulse_phase)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center = self.rect().center()
        radius = min(self.width(), self.height()) // 2 - 4
        glow_intensity = max(self._base_glow, self._amplitude * 0.8)
        glow_color = QColor(59, 130, 246, int(glow_intensity * 255))
        gradient = QRadialGradient(center.x(), center.y(), radius)
        gradient.setColorAt(0.55, QColor(0, 0, 0, 0))
        gradient.setColorAt(0.80, glow_color)
        gradient.setColorAt(1.0, QColor(59, 130, 246, int(glow_intensity * 80)))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius, radius)
        ring_color = QColor(6, 182, 212, int(60 + glow_intensity * 195))
        painter.setPen(QPen(ring_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius - 2, radius - 2)
        painter.end()


class CircularAvatar(QWidget):
    def __init__(self, size: int, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._movie: QMovie | None = None
        self._fallback_text: str = ""

    def setMovie(self, movie: QMovie):
        self._movie = movie
        self._movie.frameChanged.connect(lambda: self.update())

    def setFallbackText(self, text: str):
        self._fallback_text = text

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        path = QPainterPath()
        path.addEllipse(0.0, 0.0, float(self._size), float(self._size))
        painter.setClipPath(path)
        if self._movie and self._movie.state() == QMovie.MovieState.Running:
            frame = self._movie.currentPixmap()
            if not frame.isNull():
                scaled = frame.scaled(
                    self._size, self._size,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                x = (self._size - scaled.width()) // 2
                y = (self._size - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
        elif self._fallback_text:
            painter.setPen(QColor(T["cyan"]))
            painter.setFont(QFont(FONT_HEADING, 36, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._fallback_text)
        painter.end()


class MainWindow(QMainWindow):
    send_message_requested = pyqtSignal(str)
    mic_toggle_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setWindowOpacity(local_user.get_preference("window_opacity", WINDOW_OPACITY))

        self._drag_pos = None
        self._resizing = False
        self._resize_edge = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._bg_frame = QFrame()
        self._bg_frame.setObjectName("bgFrame")
        self._bg_frame.setStyleSheet(f"""
            QFrame#bgFrame {{
                background-color: {T['bg']};
                border: 1px solid {T['hud_border']};
                border-radius: {BORDER_RADIUS}px;
            }}
        """)

        outer = QVBoxLayout(self._bg_frame)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(4)

        # ===== TOP INFO BAR =====
        top_frame = HudFrame("", show_header=False)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(8, 4, 8, 4)
        top_bar.setSpacing(8)

        self._greeting_label = QLabel()
        self._greeting_label.setFont(QFont(FONT_HEADING, FONT_SIZE_HEADING, QFont.Weight.Bold))
        self._greeting_label.setStyleSheet(f"color: {T['text']};")
        top_bar.addWidget(self._greeting_label)

        top_bar.addStretch()

        jarvis_name = QLabel("J A R V I S")
        jarvis_name.setFont(QFont(FONT_HEADING, FONT_SIZE_HEADING, QFont.Weight.Bold))
        jarvis_name.setStyleSheet(f"color: {T['hud_title']}; letter-spacing: 8px;")
        jarvis_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(jarvis_name)

        top_bar.addStretch()

        right_info = QVBoxLayout()
        right_info.setSpacing(0)
        self._datetime_label = QLabel()
        self._datetime_label.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL))
        self._datetime_label.setStyleSheet(f"color: {T['text']};")
        self._datetime_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_info.addWidget(self._datetime_label)

        self._location_weather_label = QLabel()
        self._location_weather_label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        self._location_weather_label.setStyleSheet(f"color: {T['text_dim']};")
        self._location_weather_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_info.addWidget(self._location_weather_label)

        top_bar.addLayout(right_info)
        top_frame.add_layout(top_bar)
        outer.addWidget(top_frame)

        # ===== 3-COLUMN BODY =====
        columns = QHBoxLayout()
        columns.setSpacing(4)

        # --- LEFT COLUMN ---
        self._left_col = QWidget()
        self._left_col.setFixedWidth(SIDEBAR_LEFT_WIDTH)
        left_layout = QVBoxLayout(self._left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        notif_frame = HudFrame("Notifications", collapsible=True)
        self._notif_panel = NotificationsPanel()
        notif_frame.add_widget(self._notif_panel, stretch=1)
        left_layout.addWidget(notif_frame, stretch=1)

        metrics_frame = HudFrame("System Metrics")
        self._system_metrics = SystemMetrics()
        metrics_frame.add_widget(self._system_metrics)
        left_layout.addWidget(metrics_frame)

        columns.addWidget(self._left_col)

        # --- CENTER COLUMN ---
        center_col = QWidget()
        center_layout = QVBoxLayout(center_col)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)

        ai_core_frame = HudFrame("AI Core")
        ai_inner = QVBoxLayout()
        ai_inner.setSpacing(4)

        avatar_row = QHBoxLayout()
        avatar_row.setSpacing(8)

        self._waveform = WaveformVisualizer()
        self._waveform.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        avatar_row.addWidget(self._waveform, stretch=1)

        avatar_wrapper = QWidget()
        avatar_wrapper.setFixedSize(AVATAR_OUTER_SIZE, AVATAR_OUTER_SIZE)
        avatar_wrapper.setStyleSheet("background: transparent;")
        self._glow_ring = GlowRing(AVATAR_OUTER_SIZE, avatar_wrapper)
        self._glow_ring.move(0, 0)
        gif_size = AVATAR_GIF_SIZE
        self._avatar_widget = CircularAvatar(gif_size, avatar_wrapper)
        offset = (AVATAR_OUTER_SIZE - gif_size) // 2
        self._avatar_widget.move(offset, offset)

        gif_path = os.path.join(ASSETS_DIR, "jarvis2.gif")
        if os.path.exists(gif_path):
            self._avatar_movie = QMovie(gif_path)
            self._avatar_movie.setScaledSize(QSize(gif_size, gif_size))
            self._avatar_widget.setMovie(self._avatar_movie)
            self._avatar_movie.start()
        else:
            self._avatar_widget.setFallbackText("J")

        avatar_row.addWidget(avatar_wrapper)

        self._session_stats = SessionStats()
        self._session_stats.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        avatar_row.addWidget(self._session_stats, stretch=1)

        ai_inner.addLayout(avatar_row)

        self._status_label = QLabel("Awaiting input...")
        self._status_label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        self._status_label.setStyleSheet(f"color: {T['text_dim']};")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ai_inner.addWidget(self._status_label)

        ai_core_frame.add_layout(ai_inner)
        center_layout.addWidget(ai_core_frame)

        chat_frame = HudFrame("Chat Transcript", collapsible=True)
        self._transcript = TranscriptWidget()
        self._transcript.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chat_frame.add_widget(self._transcript, stretch=1)
        center_layout.addWidget(chat_frame, stretch=1)

        # --- BOTTOM INPUT BAR ---
        input_frame = HudFrame("Message Jarvis", show_header=False)
        input_bar = QHBoxLayout()
        input_bar.setContentsMargins(6, 4, 6, 4)
        input_bar.setSpacing(6)

        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Ask Jarvis anything...")
        self._text_input.setMinimumHeight(34)
        self._text_input.setFont(QFont(FONT_BODY, FONT_SIZE_NORMAL))
        self._text_input.returnPressed.connect(self._on_send_text)
        input_bar.addWidget(self._text_input, stretch=1)

        send_btn = QPushButton("Send")
        send_btn.setObjectName("primaryBtn")
        send_btn.setMinimumHeight(34)
        send_btn.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL, QFont.Weight.Bold))
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._on_send_text)
        input_bar.addWidget(send_btn)

        self._mic_btn = _icon_btn("fa5s.microphone", "Voice Input")
        self._mic_btn.clicked.connect(self.mic_toggle_requested.emit)
        input_bar.addWidget(self._mic_btn)

        settings_btn = _icon_btn("fa5s.cog", "Settings")
        settings_btn.clicked.connect(self._open_settings)
        input_bar.addWidget(settings_btn)

        exit_btn = QPushButton()
        exit_btn.setObjectName("dangerBtn")
        exit_btn.setIcon(qta.icon("fa5s.power-off", color=T["danger"]))
        exit_btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
        exit_btn.setMinimumHeight(34)
        exit_btn.setFixedWidth(36)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setToolTip("Exit")
        exit_btn.clicked.connect(self._on_exit)
        input_bar.addWidget(exit_btn)

        input_frame.add_layout(input_bar)
        center_layout.addWidget(input_frame)

        columns.addWidget(center_col, stretch=1)

        # --- RIGHT COLUMN ---
        self._right_col = QWidget()
        self._right_col.setFixedWidth(SIDEBAR_RIGHT_WIDTH)
        right_layout = QVBoxLayout(self._right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        notes_frame = HudFrame("Notes", collapsible=True)
        self._notes_panel = NotesPanel()
        notes_frame.add_widget(self._notes_panel, stretch=1)
        right_layout.addWidget(notes_frame, stretch=1)

        camera_frame = HudFrame("Camera Feed")
        self._camera_widget = CameraWidget()
        camera_frame.add_widget(self._camera_widget)
        right_layout.addWidget(camera_frame)

        columns.addWidget(self._right_col)

        outer.addLayout(columns, stretch=1)
        root.addWidget(self._bg_frame)

        self._notif_panel.unread_count_changed.connect(self._update_badge)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_top_bar)
        self._clock_timer.start(1000)
        self._update_top_bar()

    # --- Public API ---

    @property
    def transcript(self) -> TranscriptWidget:
        return self._transcript

    @property
    def notes_panel(self) -> NotesPanel:
        return self._notes_panel

    @property
    def waveform(self) -> WaveformVisualizer:
        return self._waveform

    @property
    def session_stats(self) -> SessionStats:
        return self._session_stats

    @property
    def notifications_panel(self) -> NotificationsPanel:
        return self._notif_panel

    @property
    def glow_ring(self) -> GlowRing:
        return self._glow_ring

    def set_status(self, text: str):
        self._status_label.setText(text)

    def set_mic_active(self, active: bool):
        if active:
            self._mic_btn.setIcon(qta.icon("fa5s.microphone-slash", color=T["danger"]))
            self._mic_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba(239, 68, 68, 0.15);
                    border: 1px solid {T['danger']};
                    border-radius: 20px; padding: 5px;
                    min-width: 36px; max-width: 36px; min-height: 36px; max-height: 36px;
                }}
            """)
        else:
            self._mic_btn.setIcon(qta.icon("fa5s.microphone", color=ICON_COLOR))
            self._mic_btn.setObjectName("iconBtn")
            self._mic_btn.setStyleSheet("")
            self._mic_btn.style().unpolish(self._mic_btn)
            self._mic_btn.style().polish(self._mic_btn)

    def show_toast(self, title: str, message: str):
        toast = ToastNotification(title, message, self._bg_frame)
        toast.move(self._bg_frame.width() - toast.width() - 20, 60)
        toast.show_toast()

    # --- Top bar ---

    def _update_top_bar(self):
        now = datetime.now()
        hour = now.hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        name = local_user.username
        self._greeting_label.setText(f"{greeting}, {name}")
        self._datetime_label.setText(now.strftime("%A, %b %d, %Y  -  %I:%M:%S %p"))

        loc = local_user.location
        self._location_weather_label.setText(loc if loc else "")

    # --- Actions ---

    def _on_send_text(self):
        text = self._text_input.text().strip()
        if text:
            self._text_input.clear()
            self._transcript.add_user_message(text, local_user.username)
            self._session_stats.increment_messages()
            self.send_message_requested.emit(text)

    def _update_badge(self, count: int):
        pass

    def _open_settings(self):
        dialog = SettingsPanel(self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()

    def _on_settings_saved(self):
        self.setWindowOpacity(local_user.get_preference("window_opacity", WINDOW_OPACITY))
        self._update_top_bar()

    def _on_exit(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Exit Jarvis")
        msg.setText("What would you like to do?")
        msg.setStyleSheet(f"""
            QMessageBox {{ background-color: {T['bg']}; color: {T['text']}; }}
            QPushButton {{ min-width: 80px; padding: 6px 14px; }}
        """)
        quit_btn = msg.addButton("Quit", QMessageBox.ButtonRole.DestructiveRole)
        tray_btn = msg.addButton("Minimize to Tray", QMessageBox.ButtonRole.AcceptRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(cancel_btn)
        msg.exec()

        if msg.clickedButton() == quit_btn:
            if hasattr(self, '_camera_widget'):
                self._camera_widget.cleanup()
            QApplication.instance().quit()
        elif msg.clickedButton() == tray_btn:
            self.hide()

    # --- Frameless drag & resize ---

    def _edge_at(self, pos: QPoint) -> str | None:
        r = self.rect()
        m = RESIZE_MARGIN
        edges = []
        if pos.y() < m:
            edges.append("top")
        if pos.y() > r.height() - m:
            edges.append("bottom")
        if pos.x() < m:
            edges.append("left")
        if pos.x() > r.width() - m:
            edges.append("right")
        return "+".join(edges) if edges else None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._edge_at(event.position().toPoint())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._drag_pos = event.globalPosition().toPoint()
            elif event.position().toPoint().y() < 50:
                self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resizing and self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._drag_pos = event.globalPosition().toPoint()
            geo = self.geometry()
            if "right" in self._resize_edge:
                geo.setRight(geo.right() + delta.x())
            if "bottom" in self._resize_edge:
                geo.setBottom(geo.bottom() + delta.y())
            if "left" in self._resize_edge:
                geo.setLeft(geo.left() + delta.x())
            if "top" in self._resize_edge:
                geo.setTop(geo.top() + delta.y())
            if geo.width() >= MIN_WINDOW_WIDTH and geo.height() >= MIN_WINDOW_HEIGHT:
                self.setGeometry(geo)
        elif self._drag_pos and not self._resizing:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        self._resizing = False
        self._resize_edge = None
        super().mouseReleaseEvent(event)
