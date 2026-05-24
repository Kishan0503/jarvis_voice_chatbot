from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame,
    QHBoxLayout, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont
from datetime import datetime
import qtawesome as qta
from ui.styles import (
    JARVIS_THEME as T, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
    FONT_SIZE_TINY, FONT_HEADING, FONT_BODY,
)

NOTIF_COLORS = {
    "info": T["cyan"],
    "success": T["success"],
    "warning": T["warning"],
    "error": T["danger"],
    "default": T["primary"],
}


class ToastNotification(QFrame):
    """Temporary popup that auto-dismisses after 5 seconds."""

    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {T['surface']};
                border: 1px solid {T['cyan']};
                border-radius: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(3)

        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.bell", color=T["cyan"]).pixmap(12, 12))
        icon_label.setStyleSheet("border: none;")
        header.addWidget(icon_label)
        title_label = QLabel(title.upper())
        title_label.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {T['cyan']}; border: none; letter-spacing: 1px;")
        header.addWidget(title_label)
        header.addStretch()
        dismiss_btn = QPushButton()
        dismiss_btn.setIcon(qta.icon("fa5s.times", color=T["text_dim"]))
        dismiss_btn.setIconSize(QSize(10, 10))
        dismiss_btn.setFixedSize(18, 18)
        dismiss_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
        dismiss_btn.clicked.connect(self._dismiss)
        header.addWidget(dismiss_btn)
        layout.addLayout(header)

        body = QLabel(message)
        body.setWordWrap(True)
        body.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        body.setStyleSheet(f"color: {T['text']}; border: none;")
        layout.addWidget(body)

        self.adjustSize()

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(0.0)

        self._fade_in = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_in.setDuration(200)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)

        self._fade_out = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_out.setDuration(300)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.finished.connect(self.deleteLater)

        QTimer.singleShot(5000, self._dismiss)

    def show_toast(self):
        self.show()
        self.raise_()
        self._fade_in.start()

    def _dismiss(self):
        self._fade_out.start()


class NotificationCard(QFrame):
    """A single notification entry with a colored status dot."""

    def __init__(self, message: str, timestamp: str, category: str = "default",
                 is_read: bool = False, parent=None):
        super().__init__(parent)
        self.is_read = is_read
        self._category = category

        border = T["hud_border"] if is_read else NOTIF_COLORS.get(category, T["primary"])
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {T['surface']};
                border: 1px solid {border};
                border-radius: 3px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(6)

        dot_color = NOTIF_COLORS.get(category, T["primary"])
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {dot_color}; border: none; font-size: 8px;")
        dot.setFixedWidth(12)
        dot.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(dot)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        text_col.setContentsMargins(0, 0, 0, 0)

        body = QLabel(message)
        body.setWordWrap(True)
        body.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        body.setStyleSheet(f"color: {T['text']}; border: none;")
        text_col.addWidget(body)

        time_label = QLabel(timestamp)
        time_label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        time_label.setStyleSheet(f"color: {T['text_dim']}; border: none;")
        text_col.addWidget(time_label)

        layout.addLayout(text_col, stretch=1)

    def mark_read(self):
        self.is_read = True
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {T['surface']};
                border: 1px solid {T['hud_border']};
                border-radius: 3px;
            }}
        """)


class NotificationsPanel(QWidget):
    """Inline always-visible notifications panel for the left sidebar."""
    unread_count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._notifications: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        clear_row = QHBoxLayout()
        clear_row.addStretch()
        clear_btn = QPushButton("Clear All")
        clear_btn.setFont(QFont(FONT_HEADING, FONT_SIZE_TINY))
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; color: {T['text_dim']}; }}
            QPushButton:hover {{ color: {T['cyan']}; }}
        """)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_all)
        clear_row.addWidget(clear_btn)
        layout.addLayout(clear_row)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(4)
        self._scroll_layout.addStretch()
        self._scroll.setWidget(self._scroll_content)
        layout.addWidget(self._scroll)

        self._empty_label = QLabel("No notifications yet.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        self._empty_label.setStyleSheet(f"color: {T['text_dim']};")
        self._scroll_layout.insertWidget(0, self._empty_label)

    def add_notification(self, message: str, category: str = "default") -> dict:
        timestamp = datetime.now().strftime("%I:%M %p")
        notif = {"message": message, "timestamp": timestamp, "read": False, "category": category}
        self._notifications.insert(0, notif)
        self._empty_label.hide()

        card = NotificationCard(message, timestamp, category=category, is_read=False)
        self._scroll_layout.insertWidget(0, card)
        card.mousePressEvent = lambda e: self._mark_card_read(card, notif)

        self.unread_count_changed.emit(self.unread_count)
        return notif

    def _mark_card_read(self, card: NotificationCard, notif: dict):
        if not notif["read"]:
            notif["read"] = True
            card.mark_read()
            self.unread_count_changed.emit(self.unread_count)

    @property
    def unread_count(self) -> int:
        return sum(1 for n in self._notifications if not n["read"])

    def clear_all(self):
        self._notifications.clear()
        while self._scroll_layout.count() > 1:
            item = self._scroll_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._empty_label.show()
        self.unread_count_changed.emit(0)
