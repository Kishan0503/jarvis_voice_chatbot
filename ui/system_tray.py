from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import pyqtSignal, QObject
import os

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _create_default_icon() -> QIcon:
    """Generate a simple 'J' icon if no icon.png is found."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor("#0a0a0a"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#3b82f6"))
    painter.setPen(QColor("#3b82f6"))
    painter.drawEllipse(4, 4, 56, 56)
    painter.setPen(QColor("#ffffff"))
    font = QFont("Rajdhani", 30, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x0084, "J")  # AlignCenter
    painter.end()
    return QIcon(pixmap)


class SystemTray(QObject):
    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    settings_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon_path):
            self._icon = QIcon(icon_path)
        else:
            self._icon = _create_default_icon()

        self._tray = QSystemTrayIcon(self._icon, parent)
        self._tray.setToolTip("Jarvis — Your AI Assistant")
        self._tray.activated.connect(self._on_activated)

        self._menu = QMenu()
        self._menu.setStyleSheet("""
            QMenu {
                background-color: #111111;
                color: #e5e7eb;
                border: 1px solid #1e3a5f;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
            }
        """)

        show_action = QAction("Show Jarvis", self._menu)
        show_action.triggered.connect(self.show_window_requested.emit)
        self._menu.addAction(show_action)

        settings_action = QAction("Settings", self._menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        self._menu.addAction(settings_action)

        self._menu.addSeparator()

        quit_action = QAction("Quit", self._menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self._menu.addAction(quit_action)

        self._tray.setContextMenu(self._menu)

    def show(self):
        self._tray.show()

    def show_message(self, title: str, message: str):
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def set_tooltip(self, text: str):
        self._tray.setToolTip(text)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window_requested.emit()
