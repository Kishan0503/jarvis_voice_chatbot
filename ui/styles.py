import os
from PyQt6.QtGui import QFontDatabase

JARVIS_THEME = {
    "primary": "#3b82f6",
    "accent": "#60a5fa",
    "glow": "rgba(59, 130, 246, 0.3)",
    "bg": "#060b18",
    "bg_darker": "#040810",
    "surface": "#0c1425",
    "surface_light": "#121e35",
    "text": "#e5e7eb",
    "text_dim": "#7a8ba8",
    "border": "#1e3a5f",
    "danger": "#ef4444",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "hud_border": "#0e4a6e",
    "hud_corner": "#22d3ee",
    "hud_bg": "rgba(6, 11, 24, 0.90)",
    "hud_title": "#22d3ee",
    "cyan": "#06b6d4",
}

FONT_HEADING = "Rajdhani"
FONT_BODY = "Exo 2"
FONT_FALLBACK = "Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif"
FONT_SIZE_TINY = 9
FONT_SIZE_SMALL = 11
FONT_SIZE_NORMAL = 13
FONT_SIZE_MEDIUM = 15
FONT_SIZE_HEADING = 22
FONT_SIZE_STATUS = 16
WINDOW_OPACITY = 0.95
BORDER_RADIUS = 4
MIN_WINDOW_WIDTH = 1100
MIN_WINDOW_HEIGHT = 650

AVATAR_OUTER_SIZE = 200
AVATAR_GIF_SIZE = 160

SIDEBAR_LEFT_WIDTH = 240
SIDEBAR_RIGHT_WIDTH = 270
HUD_CORNER_SIZE = 14
HUD_CORNER_THICKNESS = 2
HUD_DOT_SIZE = 3

T = JARVIS_THEME

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")


def load_fonts():
    if not os.path.isdir(FONTS_DIR):
        return
    for filename in os.listdir(FONTS_DIR):
        if filename.lower().endswith(".ttf"):
            path = os.path.join(FONTS_DIR, filename)
            fid = QFontDatabase.addApplicationFont(path)
            if fid < 0:
                print(f"Warning: failed to load font {filename}")


def global_stylesheet() -> str:
    return f"""
        * {{
            font-family: "{FONT_BODY}", {FONT_FALLBACK};
            color: {T['text']};
            font-size: {FONT_SIZE_NORMAL}px;
        }}

        QMainWindow, QDialog, QWidget {{
            background-color: transparent;
        }}

        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {T['surface']};
            color: {T['text']};
            border: 1px solid {T['hud_border']};
            border-radius: 3px;
            padding: 6px 10px;
            font-family: "{FONT_BODY}", {FONT_FALLBACK};
            font-size: {FONT_SIZE_NORMAL}px;
            selection-background-color: {T['primary']};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {T['cyan']};
        }}

        QPushButton {{
            background-color: {T['surface']};
            color: {T['text']};
            border: 1px solid {T['hud_border']};
            border-radius: 3px;
            padding: 6px 14px;
            font-family: "{FONT_HEADING}", {FONT_FALLBACK};
            font-size: {FONT_SIZE_NORMAL}px;
            min-height: 18px;
        }}
        QPushButton:hover {{
            background-color: {T['surface_light']};
            border-color: {T['cyan']};
        }}
        QPushButton:pressed {{
            background-color: {T['primary']};
        }}

        QPushButton#primaryBtn {{
            background-color: {T['primary']};
            border-color: {T['primary']};
            font-weight: bold;
            letter-spacing: 1px;
        }}
        QPushButton#primaryBtn:hover {{
            background-color: {T['accent']};
        }}

        QPushButton#dangerBtn {{
            background-color: transparent;
            border-color: {T['danger']};
            color: {T['danger']};
        }}
        QPushButton#dangerBtn:hover {{
            background-color: {T['danger']};
            color: white;
        }}

        QPushButton#iconBtn {{
            background-color: transparent;
            border: 1px solid {T['hud_border']};
            border-radius: 20px;
            padding: 5px;
            min-width: 36px;
            max-width: 36px;
            min-height: 36px;
            max-height: 36px;
        }}
        QPushButton#iconBtn:hover {{
            background-color: {T['surface_light']};
            border-color: {T['cyan']};
        }}

        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        QScrollBar:vertical {{
            background: {T['bg_darker']};
            width: 5px;
            border-radius: 2px;
        }}
        QScrollBar::handle:vertical {{
            background: {T['hud_border']};
            border-radius: 2px;
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {T['cyan']};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QLabel {{
            background-color: transparent;
        }}

        QComboBox {{
            background-color: {T['surface']};
            color: {T['text']};
            border: 1px solid {T['hud_border']};
            border-radius: 3px;
            padding: 5px 10px;
            min-height: 18px;
        }}
        QComboBox:hover {{
            border-color: {T['cyan']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {T['surface']};
            color: {T['text']};
            border: 1px solid {T['hud_border']};
            selection-background-color: {T['primary']};
        }}

        QCheckBox {{
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {T['hud_border']};
            border-radius: 3px;
            background-color: {T['surface']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {T['cyan']};
            border-color: {T['cyan']};
        }}

        QRadioButton {{
            spacing: 6px;
        }}
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {T['hud_border']};
            border-radius: 8px;
            background-color: {T['surface']};
        }}
        QRadioButton::indicator:checked {{
            background-color: {T['cyan']};
            border-color: {T['cyan']};
        }}

        QSlider::groove:horizontal {{
            height: 3px;
            background: {T['hud_border']};
            border-radius: 1px;
        }}
        QSlider::handle:horizontal {{
            width: 14px;
            height: 14px;
            margin: -5px 0;
            background: {T['cyan']};
            border-radius: 7px;
        }}
        QSlider::sub-page:horizontal {{
            background: {T['cyan']};
            border-radius: 1px;
        }}

        QToolTip {{
            background-color: {T['surface']};
            color: {T['text']};
            border: 1px solid {T['hud_border']};
            padding: 4px 8px;
            border-radius: 3px;
            font-size: {FONT_SIZE_SMALL}px;
        }}
    """
