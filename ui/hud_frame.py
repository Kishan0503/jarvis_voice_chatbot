from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
import qtawesome as qta
from ui.styles import (
    JARVIS_THEME as T, FONT_HEADING, FONT_SIZE_TINY, FONT_SIZE_SMALL,
    HUD_CORNER_SIZE, HUD_CORNER_THICKNESS, HUD_DOT_SIZE,
)


class HudFrame(QFrame):
    """
    Reusable HUD-style section container with sci-fi corner bracket
    decorations, an uppercase title bar, and optional collapse toggle.
    """
    collapsed_changed = pyqtSignal(bool)

    def __init__(
        self,
        title: str = "",
        collapsible: bool = False,
        show_header: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._title = title.upper()
        self._collapsible = collapsible
        self._collapsed = False
        self._show_header = show_header

        self.setStyleSheet("background: transparent; border: none;")

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._inner_layout = QVBoxLayout(self._inner)
        self._inner_layout.setContentsMargins(10, 6, 10, 8)
        self._inner_layout.setSpacing(6)

        if show_header and title:
            header = QHBoxLayout()
            header.setContentsMargins(0, 0, 0, 0)
            header.setSpacing(6)

            dot = QLabel("●")
            dot.setStyleSheet(f"color: {T['hud_corner']}; font-size: 7px;")
            dot.setFixedWidth(12)
            header.addWidget(dot)

            title_label = QLabel(self._title)
            title_label.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL, QFont.Weight.Bold))
            title_label.setStyleSheet(f"""
                color: {T['hud_title']};
                letter-spacing: 2px;
            """)
            header.addWidget(title_label)

            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet(f"background-color: {T['hud_border']};")
            line.setSizePolicy(line.sizePolicy().horizontalPolicy(), line.sizePolicy().verticalPolicy())
            header.addWidget(line, stretch=1)

            if collapsible:
                self._toggle_btn = QPushButton()
                self._toggle_btn.setIcon(qta.icon("fa5s.chevron-up", color=T["hud_title"]))
                self._toggle_btn.setIconSize(QSize(10, 10))
                self._toggle_btn.setFixedSize(20, 20)
                self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._toggle_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent; border: none; border-radius: 10px;
                    }}
                    QPushButton:hover {{ background: {T['surface_light']}; }}
                """)
                self._toggle_btn.clicked.connect(self._toggle_collapse)
                header.addWidget(self._toggle_btn)

            self._inner_layout.addLayout(header)

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background: transparent;")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(4)
        self._inner_layout.addWidget(self._content_widget, stretch=1)

        self._outer_layout.addWidget(self._inner)

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def add_widget(self, widget, **kwargs):
        self._content_layout.addWidget(widget, **kwargs)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    def add_stretch(self, factor=1):
        self._content_layout.addStretch(factor)

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._content_widget.setVisible(not self._collapsed)
        icon_name = "fa5s.chevron-down" if self._collapsed else "fa5s.chevron-up"
        self._toggle_btn.setIcon(qta.icon(icon_name, color=T["hud_title"]))
        self.collapsed_changed.emit(self._collapsed)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cs = HUD_CORNER_SIZE
        ct = HUD_CORNER_THICKNESS
        margin = 1

        corner_color = QColor(T["hud_corner"])
        border_color = QColor(T["hud_border"])
        bg_color = QColor(6, 11, 24, 220)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRect(margin, margin, w - 2 * margin, h - 2 * margin)

        dim_pen = QPen(border_color, 1)
        painter.setPen(dim_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(cs + margin, margin, w - cs - margin, margin)
        painter.drawLine(cs + margin, h - margin, w - cs - margin, h - margin)
        painter.drawLine(margin, cs + margin, margin, h - cs - margin)
        painter.drawLine(w - margin, cs + margin, w - margin, h - cs - margin)

        corner_pen = QPen(corner_color, ct)
        painter.setPen(corner_pen)

        painter.drawLine(margin, margin, margin + cs, margin)
        painter.drawLine(margin, margin, margin, margin + cs)

        painter.drawLine(w - margin, margin, w - margin - cs, margin)
        painter.drawLine(w - margin, margin, w - margin, margin + cs)

        painter.drawLine(margin, h - margin, margin + cs, h - margin)
        painter.drawLine(margin, h - margin, margin, h - margin - cs)

        painter.drawLine(w - margin, h - margin, w - margin - cs, h - margin)
        painter.drawLine(w - margin, h - margin, w - margin, h - margin - cs)

        dot_color = QColor(T["hud_corner"])
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(dot_color)
        ds = HUD_DOT_SIZE
        painter.drawEllipse(margin - 1, margin - 1, ds, ds)
        painter.drawEllipse(w - margin - ds + 1, margin - 1, ds, ds)
        painter.drawEllipse(margin - 1, h - margin - ds + 1, ds, ds)
        painter.drawEllipse(w - margin - ds + 1, h - margin - ds + 1, ds, ds)

        painter.end()
        super().paintEvent(event)
