from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import QObject, pyqtSlot, QThread

from ui.styles import global_stylesheet, load_fonts
from ui.main_window import MainWindow
from ui.system_tray import SystemTray
from ui.setup_wizard import SetupWizard
from voice.orchestrator import Orchestrator
from gemini_client import gemini_client
from auth.local_user import local_user

STATUS_MAP = {
    "idle": "Awaiting input...",
    "listening": "Listening...",
    "processing": "Processing...",
    "speaking": "Speaking...",
}


class GeminiWorker(QThread):
    """Runs Gemini API call in a background thread."""
    from PyQt6.QtCore import pyqtSignal
    response_ready = pyqtSignal(str)
    tools_used = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self._message = message

    def run(self):
        try:
            result = gemini_client.send_message_to_gemini(self._message)
            self.response_ready.emit(result["reply"])
            if result["tools_used"]:
                self.tools_used.emit(result["tools_used"])
        except Exception as e:
            self.error_occurred.emit(str(e))


class JarvisApp(QObject):
    """Top-level controller: window + tray + orchestrator + Gemini."""

    def __init__(self, qt_app: QApplication):
        super().__init__()
        self._qt_app = qt_app
        load_fonts()
        self._qt_app.setStyleSheet(global_stylesheet())

        self._tray = SystemTray()
        self._tray.show_window_requested.connect(self._show_main)
        self._tray.quit_requested.connect(self._quit)
        self._tray.settings_requested.connect(self._open_settings_from_tray)
        self._tray.show()

        self._orchestrator = Orchestrator()
        self._orchestrator.state_changed.connect(self._on_state_changed)
        self._orchestrator.amplitude_changed.connect(self._on_amplitude)
        self._orchestrator.transcription_ready.connect(self._on_transcription)
        self._orchestrator.jarvis_reply_ready.connect(self._on_jarvis_reply)
        self._orchestrator.send_to_gemini.connect(self._call_gemini)
        self._orchestrator.tts_engine_used.connect(self._on_tts_engine)
        self._orchestrator.error_occurred.connect(self._on_error)

        self._window: MainWindow | None = None
        self._gemini_worker: GeminiWorker | None = None

    def start(self):
        if local_user.is_first_run:
            self._run_setup_wizard()
        else:
            self._show_main()

    def _run_setup_wizard(self):
        wizard = SetupWizard()
        wizard.setup_complete.connect(self._on_setup_complete)
        wizard.exec()
        self._show_main()

    @pyqtSlot(str, str, str)
    def _on_setup_complete(self, name: str, location: str, temp_unit: str):
        local_user.complete_first_run(name, location, temp_unit)

    def _show_main(self):
        if self._window is None:
            self._window = MainWindow()
            self._window.send_message_requested.connect(self._on_user_typed)
            self._window.mic_toggle_requested.connect(self._on_mic_toggle)
            self._setup_kill_switch()

        self._window.showMaximized()
        self._window.activateWindow()
        self._tray.set_tooltip(f"Jarvis — {local_user.username}'s Assistant")
        self._refresh_notes_panel()

    def _setup_kill_switch(self):
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+J"), self._window)
        shortcut.activated.connect(self._kill_switch)

    def _kill_switch(self):
        self._orchestrator.stop_all()

    # --- User input handlers ---

    @pyqtSlot(str)
    def _on_user_typed(self, text: str):
        """User typed a message and pressed Send."""
        self._orchestrator.handle_text_input(text)

    @pyqtSlot()
    def _on_mic_toggle(self):
        """User clicked the mic button."""
        self._orchestrator.start_listening()

    # --- Orchestrator signal handlers ---

    @pyqtSlot(str)
    def _on_state_changed(self, state: str):
        if self._window:
            self._window.set_status(STATUS_MAP.get(state, state))
            self._window.waveform.set_state(state)

            is_listening = state == "listening"
            self._window.set_mic_active(is_listening)

    @pyqtSlot(float)
    def _on_amplitude(self, amp: float):
        if self._window:
            self._window.glow_ring.set_amplitude(amp)
            self._window.waveform.set_amplitude(amp)

    @pyqtSlot(str)
    def _on_transcription(self, text: str):
        if self._window:
            self._window.transcript.add_user_message(text, local_user.username)
            self._window.session_stats.increment_messages()

    @pyqtSlot(str)
    def _on_jarvis_reply(self, reply: str):
        if self._window:
            self._window.transcript.add_jarvis_message(reply)
            self._window.session_stats.increment_messages()

    @pyqtSlot(str)
    def _on_tts_engine(self, engine: str):
        print(f"TTS engine: {engine}")

    @pyqtSlot(str)
    def _on_error(self, msg: str):
        if self._window:
            self._window.show_toast("Error", msg)
            self._window.notifications_panel.add_notification(msg, category="error")

    # --- Gemini worker ---

    @pyqtSlot(str)
    def _call_gemini(self, text: str):
        """Run Gemini API call in a background thread."""
        self._gemini_worker = GeminiWorker(text)
        self._gemini_worker.response_ready.connect(self._orchestrator.on_gemini_response)
        self._gemini_worker.tools_used.connect(self._on_tools_used)
        self._gemini_worker.error_occurred.connect(self._on_gemini_error)
        self._gemini_worker.start()

    @pyqtSlot(list)
    def _on_tools_used(self, tools: list):
        """React to tool calls — refresh UI panels as needed."""
        if self._window:
            notes_tools = {"save_note", "delete_note", "list_notes"}
            if notes_tools.intersection(tools):
                self._refresh_notes_panel()

            if self._window.session_stats:
                for _ in tools:
                    self._window.session_stats.increment_tools()

    def _refresh_notes_panel(self):
        """Reload notes from SQLite and update the notes panel."""
        if not self._window:
            return
        try:
            from tools.notes import list_notes
            result = list_notes()
            if result.get("status") == "success":
                self._window.notes_panel.load_notes(result.get("notes", []))
        except Exception as e:
            print(f"Error refreshing notes: {e}")

    @pyqtSlot(str)
    def _on_gemini_error(self, msg: str):
        self._on_error(f"Gemini: {msg}")
        self._orchestrator.stop_all()

    # --- Tray / quit ---

    def _open_settings_from_tray(self):
        if self._window:
            self._window._open_settings()

    def _quit(self):
        self._orchestrator.stop_all()
        self._qt_app.quit()
