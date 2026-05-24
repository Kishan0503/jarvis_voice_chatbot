from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont
from datetime import datetime
from ui.styles import (
    JARVIS_THEME as T, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
    FONT_SIZE_TINY, FONT_HEADING, FONT_BODY,
)

MAX_VISIBLE_MESSAGES = 100


class MessageBubble(QFrame):
    def __init__(self, sender: str, text: str, timestamp: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("messageBubble")

        if is_user:
            bg = T["surface"]
            border_color = T["hud_border"]
            alignment = Qt.AlignmentFlag.AlignRight
        else:
            bg = "#081428"
            border_color = T["cyan"]
            alignment = Qt.AlignmentFlag.AlignLeft

        self.setStyleSheet(f"""
            QFrame#messageBubble {{
                background-color: {bg};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setSpacing(6)

        sender_label = QLabel(sender)
        sender_label.setFont(QFont(FONT_HEADING, FONT_SIZE_TINY, QFont.Weight.Bold))
        color = T["cyan"] if not is_user else T["text_dim"]
        sender_label.setStyleSheet(f"color: {color}; letter-spacing: 1px;")

        time_label = QLabel(timestamp)
        time_label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        time_label.setStyleSheet(f"color: {T['text_dim']};")

        if is_user:
            header.addStretch()
            header.addWidget(time_label)
            header.addWidget(sender_label)
        else:
            header.addWidget(sender_label)
            header.addWidget(time_label)
            header.addStretch()

        layout.addLayout(header)

        content = QLabel(text)
        content.setWordWrap(True)
        content.setTextFormat(Qt.TextFormat.RichText)
        content.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        content.setStyleSheet(f"color: {T['text']};")
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        content.setMinimumWidth(120)
        content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(content)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(150)

        self._alignment = alignment

    @property
    def bubble_alignment(self) -> Qt.AlignmentFlag:
        return self._alignment


class TranscriptWidget(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: transparent; border: none;")

        self._container = QWidget()
        self._container.setStyleSheet("background-color: transparent;")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._layout.setSpacing(6)
        self._layout.addStretch()

        self.setWidget(self._container)
        self._message_count = 0

    @pyqtSlot(str, str)
    def add_user_message(self, text: str, username: str = "You"):
        timestamp = datetime.now().strftime("%I:%M %p")
        bubble = MessageBubble(username, text, timestamp, is_user=True)
        self._insert_bubble(bubble)

    @pyqtSlot(str)
    def add_jarvis_message(self, text: str):
        display_text = text.replace("\n", "<br>")
        timestamp = datetime.now().strftime("%I:%M %p")
        bubble = MessageBubble("Jarvis", display_text, timestamp, is_user=False)
        self._insert_bubble(bubble)

    def add_system_message(self, text: str):
        label = QLabel(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        label.setStyleSheet(f"color: {T['text_dim']}; padding: 2px;")
        label.setWordWrap(True)
        insert_pos = self._layout.count() - 1
        self._layout.insertWidget(insert_pos, label, alignment=Qt.AlignmentFlag.AlignCenter)
        self._message_count += 1
        self._trim_old_messages()
        self._scroll_to_bottom()

    def _insert_bubble(self, bubble: MessageBubble):
        insert_pos = self._layout.count() - 1
        self._layout.insertWidget(insert_pos, bubble, alignment=bubble.bubble_alignment)
        self._message_count += 1
        self._trim_old_messages()
        self._scroll_to_bottom()

    def _trim_old_messages(self):
        while self._message_count > MAX_VISIBLE_MESSAGES:
            item = self._layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
                self._message_count -= 1

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.verticalScrollBar().setValue(
            self.verticalScrollBar().maximum()
        ))

    def clear_transcript(self):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._message_count = 0
