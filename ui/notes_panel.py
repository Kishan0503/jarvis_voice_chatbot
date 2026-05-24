from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QHBoxLayout, QDialog, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont
import qtawesome as qta
from ui.styles import (
    JARVIS_THEME as T, FONT_SIZE_NORMAL, FONT_SIZE_SMALL,
    FONT_SIZE_TINY, FONT_SIZE_HEADING, FONT_HEADING, FONT_BODY,
)


class NoteCard(QFrame):
    delete_requested = pyqtSignal(int)
    view_requested = pyqtSignal(int, str, str)

    def __init__(self, note_id: int, content: str, created_at: str, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self._content = content
        self._created_at = created_at
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {T['surface']};
                border: 1px solid {T['hud_border']};
                border-radius: 3px;
            }}
            QFrame:hover {{
                border-color: {T['cyan']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        title_text = content[:50] + ("..." if len(content) > 50 else "")
        title_label = QLabel(title_text)
        title_label.setWordWrap(True)
        title_label.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        title_label.setStyleSheet(f"color: {T['text']}; border: none;")
        layout.addWidget(title_label)

        bottom = QHBoxLayout()
        time_label = QLabel(created_at)
        time_label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        time_label.setStyleSheet(f"color: {T['text_dim']}; border: none;")
        bottom.addWidget(time_label)
        bottom.addStretch()

        del_btn = QPushButton()
        del_btn.setIcon(qta.icon("fa5s.trash-alt", color=T["text_dim"]))
        del_btn.setIconSize(QSize(10, 10))
        del_btn.setFixedSize(20, 20)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; border-radius: 10px; }}
            QPushButton:hover {{ background-color: {T['danger']}; }}
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.note_id))
        bottom.addWidget(del_btn)
        layout.addLayout(bottom)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.view_requested.emit(self.note_id, self._content, self._created_at)
        super().mousePressEvent(event)


class NoteViewModal(QDialog):
    delete_requested = pyqtSignal(int)

    def __init__(self, note_id: int, content: str, created_at: str, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        if parent:
            self.setFixedSize(parent.window().size())

        overlay = QFrame(self)
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); border: none;")
        overlay.setGeometry(0, 0, self.width(), self.height())
        overlay.mousePressEvent = lambda e: self.close()

        card = QFrame(self)
        card.setFixedWidth(min(450, self.width() - 60))
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {T['surface']};
                border: 1px solid {T['hud_border']};
                border-radius: 6px;
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(10)

        header = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon("fa5s.sticky-note", color=T["cyan"]).pixmap(16, 16))
        icon_label.setStyleSheet("border: none;")
        header.addWidget(icon_label)
        title = QLabel("NOTE")
        title.setFont(QFont(FONT_HEADING, FONT_SIZE_NORMAL, QFont.Weight.Bold))
        title.setStyleSheet(f"border: none; color: {T['hud_title']}; letter-spacing: 2px;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton()
        close_btn.setIcon(qta.icon("fa5s.times", color=T["text_dim"]))
        close_btn.setIconSize(QSize(12, 12))
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: {T['surface_light']}; border: 1px solid {T['hud_border']}; border-radius: 12px; }}
            QPushButton:hover {{ border-color: {T['cyan']}; }}
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        card_layout.addLayout(header)

        body = QLabel(content)
        body.setWordWrap(True)
        body.setFont(QFont(FONT_BODY, FONT_SIZE_NORMAL))
        body.setStyleSheet(f"color: {T['text']}; border: none;")
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        card_layout.addWidget(body)

        time_label = QLabel(created_at)
        time_label.setFont(QFont(FONT_BODY, FONT_SIZE_TINY))
        time_label.setStyleSheet(f"color: {T['text_dim']}; border: none;")
        card_layout.addWidget(time_label)

        del_btn = QPushButton()
        del_btn.setIcon(qta.icon("fa5s.trash-alt", color=T["danger"]))
        del_btn.setIconSize(QSize(12, 12))
        del_btn.setText("  Delete Note")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(lambda: (self.delete_requested.emit(self.note_id), self.close()))
        card_layout.addWidget(del_btn)

        card.adjustSize()
        card.move((self.width() - card.width()) // 2, max((self.height() - card.height()) // 2, 40))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)


class NotesPanel(QWidget):
    """Inline always-visible notes panel for the right sidebar."""
    note_delete_requested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

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

        self._empty_label = QLabel("No notes yet.\nAsk Jarvis to save a note.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFont(QFont(FONT_BODY, FONT_SIZE_SMALL))
        self._empty_label.setStyleSheet(f"color: {T['text_dim']};")
        self._scroll_layout.insertWidget(0, self._empty_label)

    def load_notes(self, notes: list[dict]):
        while self._scroll_layout.count() > 1:
            item = self._scroll_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        self._empty_label.setVisible(len(notes) == 0)

        for note in notes:
            card = NoteCard(note["id"], note["content"], note["created_at"])
            card.delete_requested.connect(self.note_delete_requested.emit)
            card.view_requested.connect(self._show_note_modal)
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, card)

    def _show_note_modal(self, note_id: int, content: str, created_at: str):
        modal = NoteViewModal(note_id, content, created_at, self.window())
        modal.delete_requested.connect(self.note_delete_requested.emit)
        modal.exec()
