from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QCheckBox, QRadioButton, QButtonGroup, QSlider, QFrame,
    QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from auth.local_user import local_user
from ui.styles import JARVIS_THEME as T, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_HEADING, FONT_HEADING, FONT_BODY
import requests


class SettingsPanel(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        if parent:
            self.setFixedSize(parent.size())

        overlay = QFrame(self)
        overlay.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); border: none;")
        overlay.setGeometry(0, 0, self.width(), self.height())
        overlay.mousePressEvent = lambda e: self.close()

        card = QFrame(self)
        card_width = min(520, self.width() - 60)
        card_height = min(600, self.height() - 80)
        card.setFixedSize(card_width, card_height)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {T['bg']};
                border: 1px solid {T['border']};
                border-radius: 16px;
            }}
        """)
        card.move((self.width() - card_width) // 2, (self.height() - card_height) // 2)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(0)

        header = QHBoxLayout()
        title = QLabel("⚙  Settings")
        title.setFont(QFont(FONT_HEADING, FONT_SIZE_HEADING, QFont.Weight.Bold))
        title.setStyleSheet(f"border: none; color: {T['text']};")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; font-size: 18px;
                color: {T['text_dim']}; border-radius: 16px;
            }}
            QPushButton:hover {{ color: {T['text']}; background: {T['surface_light']}; }}
        """)
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        card_layout.addLayout(header)
        card_layout.addSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        form = QVBoxLayout(scroll_content)
        form.setContentsMargins(0, 0, 8, 0)
        form.setSpacing(16)

        form.addWidget(self._section_label("Profile"))
        self.name_input = self._input_field("Name", local_user.username)
        form.addLayout(self.name_input["layout"])

        loc_layout = QHBoxLayout()
        self.location_input = QLineEdit(local_user.location)
        self.location_input.setPlaceholderText("City, Country")
        loc_layout.addWidget(self.location_input)
        auto_btn = QPushButton("Auto-detect")
        auto_btn.setFixedHeight(36)
        auto_btn.clicked.connect(self._auto_detect_location)
        loc_layout.addWidget(auto_btn)
        loc_wrapper = QVBoxLayout()
        loc_label = QLabel("Location")
        loc_label.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL))
        loc_label.setStyleSheet(f"color: {T['text_dim']};")
        loc_wrapper.addWidget(loc_label)
        loc_wrapper.addLayout(loc_layout)
        form.addLayout(loc_wrapper)

        temp_layout = QHBoxLayout()
        temp_label = QLabel("Temperature Unit")
        temp_label.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL))
        temp_label.setStyleSheet(f"color: {T['text_dim']};")
        self.celsius_radio = QRadioButton("Celsius")
        self.fahrenheit_radio = QRadioButton("Fahrenheit")
        self._temp_group = QButtonGroup(self)
        self._temp_group.addButton(self.celsius_radio)
        self._temp_group.addButton(self.fahrenheit_radio)
        if local_user.get_preference("temp_unit", "celsius") == "fahrenheit":
            self.fahrenheit_radio.setChecked(True)
        else:
            self.celsius_radio.setChecked(True)
        temp_wrapper = QVBoxLayout()
        temp_wrapper.addWidget(temp_label)
        temp_row = QHBoxLayout()
        temp_row.addWidget(self.celsius_radio)
        temp_row.addWidget(self.fahrenheit_radio)
        temp_row.addStretch()
        temp_wrapper.addLayout(temp_row)
        form.addLayout(temp_wrapper)

        form.addWidget(self._section_label("Voice"))

        tts_layout = QHBoxLayout()
        tts_wrapper = QVBoxLayout()
        tts_label = QLabel("TTS Engine")
        tts_label.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL))
        tts_label.setStyleSheet(f"color: {T['text_dim']};")
        self.tts_combo = QComboBox()
        self.tts_combo.addItems(["ElevenLabs", "Edge TTS", "System (pyttsx3)"])
        current_tts = local_user.get_preference("tts_engine", "elevenlabs")
        tts_map = {"elevenlabs": 0, "edge-tts": 1, "pyttsx3": 2}
        self.tts_combo.setCurrentIndex(tts_map.get(current_tts, 0))
        tts_wrapper.addWidget(tts_label)
        tts_wrapper.addWidget(self.tts_combo)
        tts_layout.addLayout(tts_wrapper)
        form.addLayout(tts_layout)

        self.wake_word_check = QCheckBox("Wake Word Enabled (\"Hey Jarvis\")")
        self.wake_word_check.setChecked(local_user.get_preference("wake_word_enabled", True))
        form.addWidget(self.wake_word_check)

        form.addWidget(self._section_label("Permissions"))
        self.app_control_check = QCheckBox("Allow app control")
        self.app_control_check.setChecked(local_user.get_preference("allow_app_control", True))
        form.addWidget(self.app_control_check)

        self.file_access_check = QCheckBox("Allow file access")
        self.file_access_check.setChecked(local_user.get_preference("allow_file_access", True))
        form.addWidget(self.file_access_check)

        self.camera_check = QCheckBox("Camera access")
        self.camera_check.setChecked(local_user.get_preference("camera_enabled", False))
        form.addWidget(self.camera_check)

        form.addWidget(self._section_label("Appearance"))
        opacity_wrapper = QVBoxLayout()
        self._opacity_value = QLabel(f"Window Opacity: {int(local_user.get_preference('window_opacity', 0.92) * 100)}%")
        self._opacity_value.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL))
        self._opacity_value.setStyleSheet(f"color: {T['text_dim']};")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setValue(int(local_user.get_preference("window_opacity", 0.92) * 100))
        self.opacity_slider.valueChanged.connect(
            lambda v: self._opacity_value.setText(f"Window Opacity: {v}%")
        )
        opacity_wrapper.addWidget(self._opacity_value)
        opacity_wrapper.addWidget(self.opacity_slider)
        form.addLayout(opacity_wrapper)

        form.addStretch()
        scroll.setWidget(scroll_content)
        card_layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save)
        btn_row.addStretch()
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.close)
        btn_row.addWidget(reset_btn)
        btn_row.addWidget(save_btn)
        card_layout.addSpacing(12)
        card_layout.addLayout(btn_row)

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(f"── {text} ──")
        label.setFont(QFont(FONT_HEADING, FONT_SIZE_NORMAL, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {T['accent']}; padding-top: 4px;")
        return label

    def _input_field(self, label_text: str, value: str) -> dict:
        layout = QVBoxLayout()
        label = QLabel(label_text)
        label.setFont(QFont(FONT_HEADING, FONT_SIZE_SMALL))
        label.setStyleSheet(f"color: {T['text_dim']};")
        inp = QLineEdit(value)
        layout.addWidget(label)
        layout.addWidget(inp)
        return {"layout": layout, "input": inp}

    def _auto_detect_location(self):
        try:
            resp = requests.get("http://ip-api.com/json/", timeout=5)
            data = resp.json()
            if data.get("status") == "success":
                city = data.get("city", "")
                country = data.get("country", "")
                self.location_input.setText(f"{city}, {country}")
        except Exception:
            self.location_input.setPlaceholderText("Auto-detect failed. Enter manually.")

    def _save(self):
        local_user.username = self.name_input["input"].text().strip() or "User"
        local_user.location = self.location_input.text().strip()
        local_user.set_preference(
            "temp_unit", "fahrenheit" if self.fahrenheit_radio.isChecked() else "celsius"
        )
        tts_map = {0: "elevenlabs", 1: "edge-tts", 2: "pyttsx3"}
        local_user.set_preference("tts_engine", tts_map.get(self.tts_combo.currentIndex(), "elevenlabs"))
        local_user.set_preference("wake_word_enabled", self.wake_word_check.isChecked())
        local_user.set_preference("allow_app_control", self.app_control_check.isChecked())
        local_user.set_preference("allow_file_access", self.file_access_check.isChecked())
        local_user.set_preference("camera_enabled", self.camera_check.isChecked())
        local_user.set_preference("window_opacity", self.opacity_slider.value() / 100.0)
        local_user.save()
        self.settings_saved.emit()
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        super().keyPressEvent(event)
