from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QButtonGroup, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor
from ui.styles import JARVIS_THEME as T, FONT_SIZE_NORMAL, FONT_SIZE_HEADING, BORDER_RADIUS, FONT_HEADING, FONT_BODY
import requests


class SetupWizard(QDialog):
    setup_complete = pyqtSignal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 420)

        card = QFrame(self)
        card.setGeometry(0, 0, 460, 420)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {T['bg']};
                border: 1px solid {T['border']};
                border-radius: {BORDER_RADIUS}px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(20)

        title = QLabel("Welcome to Jarvis")
        title.setFont(QFont(FONT_HEADING, FONT_SIZE_HEADING, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {T['accent']}; border: none;")
        layout.addWidget(title)

        subtitle = QLabel("Let's get you set up in just a moment.")
        subtitle.setFont(QFont(FONT_HEADING, FONT_SIZE_NORMAL))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {T['text_dim']}; border: none;")
        layout.addWidget(subtitle)

        layout.addSpacing(4)

        name_label = QLabel("What should I call you?")
        name_label.setFont(QFont(FONT_HEADING, FONT_SIZE_NORMAL))
        name_label.setStyleSheet(f"color: {T['text']}; border: none;")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name")
        self.name_input.setMinimumHeight(40)
        layout.addWidget(self.name_input)

        loc_label = QLabel("Your city (for weather & time):")
        loc_label.setFont(QFont(FONT_HEADING, FONT_SIZE_NORMAL))
        loc_label.setStyleSheet(f"color: {T['text']}; border: none;")
        layout.addWidget(loc_label)

        loc_row = QHBoxLayout()
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("City, Country")
        self.location_input.setMinimumHeight(40)
        loc_row.addWidget(self.location_input)

        auto_btn = QPushButton("Auto-detect")
        auto_btn.setMinimumHeight(40)
        auto_btn.clicked.connect(self._auto_detect)
        loc_row.addWidget(auto_btn)
        layout.addLayout(loc_row)

        temp_label = QLabel("Temperature unit:")
        temp_label.setFont(QFont(FONT_HEADING, FONT_SIZE_NORMAL))
        temp_label.setStyleSheet(f"color: {T['text']}; border: none;")
        layout.addWidget(temp_label)

        temp_row = QHBoxLayout()
        self.celsius_radio = QRadioButton("Celsius")
        self.celsius_radio.setChecked(True)
        self.fahrenheit_radio = QRadioButton("Fahrenheit")
        self._temp_group = QButtonGroup(self)
        self._temp_group.addButton(self.celsius_radio)
        self._temp_group.addButton(self.fahrenheit_radio)
        temp_row.addWidget(self.celsius_radio)
        temp_row.addWidget(self.fahrenheit_radio)
        temp_row.addStretch()
        layout.addLayout(temp_row)

        layout.addStretch()

        start_btn = QPushButton("Get Started")
        start_btn.setObjectName("primaryBtn")
        start_btn.setMinimumHeight(44)
        start_btn.setFont(QFont(FONT_HEADING, FONT_SIZE_NORMAL, QFont.Weight.Bold))
        start_btn.clicked.connect(self._on_submit)
        layout.addWidget(start_btn)

    def _auto_detect(self):
        try:
            resp = requests.get("http://ip-api.com/json/", timeout=5)
            data = resp.json()
            if data.get("status") == "success":
                city = data.get("city", "")
                country = data.get("country", "")
                self.location_input.setText(f"{city}, {country}")
        except Exception:
            self.location_input.setPlaceholderText("Could not detect. Enter manually.")

    def _on_submit(self):
        name = self.name_input.text().strip() or "User"
        location = self.location_input.text().strip()
        temp_unit = "fahrenheit" if self.fahrenheit_radio.isChecked() else "celsius"
        self.setup_complete.emit(name, location, temp_unit)
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            pass
        else:
            super().keyPressEvent(event)
