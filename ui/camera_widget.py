from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QImage, QPixmap
import qtawesome as qta
from ui.styles import JARVIS_THEME as T, FONT_HEADING, FONT_BODY, FONT_SIZE_TINY, FONT_SIZE_SMALL

CAMERA_FPS = 10


class CameraThread(QThread):
    """Captures frames from webcam in a background thread."""
    frame_ready = pyqtSignal(QImage)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._running = False

    def run(self):
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.error.emit("Camera not available")
                return

            self._running = True
            while self._running:
                ret, frame = cap.read()
                if ret:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                    self.frame_ready.emit(img.copy())
                self.msleep(int(1000 / CAMERA_FPS))

            cap.release()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._running = False
        self.quit()
        self.wait(2000)


class CameraWidget(QWidget):
    """Toggleable camera feed widget. Shows live feed when ON, compact off-state when OFF."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._camera_on = False
        self._thread: CameraThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        controls = QHBoxLayout()
        controls.setSpacing(6)

        self._toggle_btn = QPushButton()
        self._toggle_btn.setIcon(qta.icon("fa5s.video-slash", color=T["text_dim"]))
        self._toggle_btn.setIconSize(QSize(12, 12))
        self._toggle_btn.setFixedSize(28, 28)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T['surface']}; border: 1px solid {T['hud_border']};
                border-radius: 14px;
            }}
            QPushButton:hover {{ border-color: {T['cyan']}; }}
        """)
        self._toggle_btn.setToolTip("Toggle Camera")
        self._toggle_btn.clicked.connect(self._toggle)
        controls.addWidget(self._toggle_btn)

        self._status_label = QLabel("OFF")
        self._status_label.setFont(QFont(FONT_HEADING, FONT_SIZE_TINY, QFont.Weight.Bold))
        self._status_label.setStyleSheet(f"color: {T['text_dim']}; letter-spacing: 1px;")
        controls.addWidget(self._status_label)

        controls.addStretch()

        self._live_badge = QLabel("● LIVE")
        self._live_badge.setFont(QFont(FONT_HEADING, FONT_SIZE_TINY, QFont.Weight.Bold))
        self._live_badge.setStyleSheet(f"color: {T['success']}; letter-spacing: 1px;")
        self._live_badge.hide()
        controls.addWidget(self._live_badge)

        layout.addLayout(controls)

        self._feed_label = QLabel()
        self._feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._feed_label.setMinimumHeight(100)
        self._feed_label.setStyleSheet(f"""
            background-color: {T['bg_darker']};
            border: 1px solid {T['hud_border']};
            border-radius: 3px;
        """)

        self._off_text = QLabel("Camera Off")
        self._off_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._off_text.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        self._off_text.setStyleSheet(f"color: {T['text_dim']};")

        off_layout = QVBoxLayout(self._feed_label)
        off_layout.addWidget(self._off_text)

        layout.addWidget(self._feed_label)

    def _toggle(self):
        if self._camera_on:
            self._stop_camera()
        else:
            self._start_camera()

    def _start_camera(self):
        self._camera_on = True
        self._toggle_btn.setIcon(qta.icon("fa5s.video", color=T["success"]))
        self._status_label.setText("ON")
        self._status_label.setStyleSheet(f"color: {T['success']}; letter-spacing: 1px;")
        self._live_badge.show()
        self._off_text.hide()

        self._thread = CameraThread()
        self._thread.frame_ready.connect(self._update_frame)
        self._thread.error.connect(self._on_camera_error)
        self._thread.start()

    def _stop_camera(self):
        self._camera_on = False
        self._toggle_btn.setIcon(qta.icon("fa5s.video-slash", color=T["text_dim"]))
        self._status_label.setText("OFF")
        self._status_label.setStyleSheet(f"color: {T['text_dim']}; letter-spacing: 1px;")
        self._live_badge.hide()
        self._off_text.show()
        self._feed_label.setPixmap(QPixmap())

        if self._thread:
            self._thread.stop()
            self._thread = None

    def _update_frame(self, image: QImage):
        if self._camera_on:
            pixmap = QPixmap.fromImage(image).scaled(
                self._feed_label.width(), self._feed_label.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._feed_label.setPixmap(pixmap)

    def _on_camera_error(self, msg: str):
        self._stop_camera()
        self._off_text.setText(f"Error: {msg}")
        self._off_text.show()

    def cleanup(self):
        if self._thread:
            self._thread.stop()
