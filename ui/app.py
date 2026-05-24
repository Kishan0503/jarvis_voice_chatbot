import asyncio

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread

from ui.styles import global_stylesheet, load_fonts
from ui.main_window import MainWindow
from ui.system_tray import SystemTray
from ui.setup_wizard import SetupWizard
from voice.orchestrator import Orchestrator
from auth.local_user import local_user

STATUS_MAP = {
    "idle": "Awaiting input...",
    "listening": "Listening...",
    "processing": "Processing...",
    "speaking": "Speaking...",
}


# ---------------------------------------------------------------------------
# AgentWorker — async LangGraph ↔ Qt bridge
# ---------------------------------------------------------------------------

class AgentWorker(QThread):
    """
    Runs the LangGraph agent in a background QThread.

    The agent is async-native; we bridge it with a plain `asyncio.run()`
    call inside the thread so Qt's event loop is never blocked.

    Signals
    -------
    sentence_ready(str)       : Emitted for each complete sentence as tokens
                                stream in — feeds the TTS pipeline immediately.
    reply_complete(str, list) : Emitted once when the full response is done.
                                Carries the concatenated reply text and the
                                list of tool names that were called.
    error_occurred(str)       : Emitted on any agent or network error.
    """

    sentence_ready = pyqtSignal(str)
    reply_complete = pyqtSignal(str, list)
    error_occurred = pyqtSignal(str)

    def __init__(self, message: str, parent=None):
        super().__init__(parent)
        self._message = message

    def run(self):
        asyncio.run(self._stream())

    async def _stream(self):
        from langchain_core.messages import HumanMessage
        from agent.graph import compiled_graph, get_thread_config
        from agent.sentence_buffer import SentenceBuffer

        buf = SentenceBuffer()
        full_text = ""
        tools_used: list[str] = []

        try:
            input_state = {
                "messages": [HumanMessage(content=self._message)],
                "tools_used": [],
            }
            config = get_thread_config()

            async for event in compiled_graph.astream_events(
                input_state, config, version="v2"
            ):
                kind = event.get("event", "")

                # --- Stream tokens from the final model response ---
                if kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and chunk.content:
                        token = chunk.content
                        full_text += token
                        sentence = buf.feed(token)
                        if sentence:
                            self.sentence_ready.emit(sentence)

                # --- Track tool calls for UI panels ---
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    if tool_name:
                        tools_used.append(tool_name)

            # Flush any remaining partial sentence
            remainder = buf.flush()
            if remainder:
                self.sentence_ready.emit(remainder)

            self.reply_complete.emit(full_text.strip(), tools_used)

        except Exception as e:
            # print(f"AgentWorker error: {e}")
            self.error_occurred.emit(str(e))


# ---------------------------------------------------------------------------
# JarvisApp — top-level controller
# ---------------------------------------------------------------------------

class JarvisApp(QObject):
    """Top-level controller: window + tray + orchestrator + LangGraph agent."""

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
        self._orchestrator.send_to_agent.connect(self._call_agent)
        self._orchestrator.tts_engine_used.connect(self._on_tts_engine)
        self._orchestrator.error_occurred.connect(self._on_error)

        self._window: MainWindow | None = None
        self._agent_worker: AgentWorker | None = None

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

    # ------------------------------------------------------------------
    # User input handlers
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _on_user_typed(self, text: str):
        self._orchestrator.handle_text_input(text)

    @pyqtSlot()
    def _on_mic_toggle(self):
        self._orchestrator.start_listening()

    # ------------------------------------------------------------------
    # Orchestrator signal handlers
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _on_state_changed(self, state: str):
        if self._window:
            self._window.set_status(STATUS_MAP.get(state, state))
            self._window.waveform.set_state(state)
            self._window.set_mic_active(state == "listening")

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
        """Full reply received — update transcript and session stats."""
        if self._window:
            self._window.transcript.add_jarvis_message(reply)
            self._window.session_stats.increment_messages()

    @pyqtSlot(str)
    def _on_tts_engine(self, engine: str):
        # print(f"TTS engine used: {engine}")
        pass
    
    @pyqtSlot(str)
    def _on_error(self, msg: str):
        if self._window:
            self._window.show_toast("Error", msg)
            self._window.notifications_panel.add_notification(msg, category="error")

    # ------------------------------------------------------------------
    # Agent worker
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _call_agent(self, text: str):
        """Spin up an AgentWorker for this user message."""
        self._agent_worker = AgentWorker(text)
        self._agent_worker.sentence_ready.connect(self._orchestrator.on_sentence_ready)
        self._agent_worker.reply_complete.connect(self._on_reply_complete)
        self._agent_worker.error_occurred.connect(self._on_agent_error)
        self._agent_worker.start()

    @pyqtSlot(str, list)
    def _on_reply_complete(self, full_text: str, tools_used: list):
        """Agent stream finished — hand off to orchestrator and update UI panels."""
        self._orchestrator.on_reply_complete(full_text, tools_used)
        self._on_tools_used(tools_used)

    @pyqtSlot(list)
    def _on_tools_used(self, tools: list):
        if not self._window:
            return
        notes_tools = {"save_note", "delete_note", "list_notes"}
        if notes_tools.intersection(tools):
            self._refresh_notes_panel()
        if self._window.session_stats:
            for _ in tools:
                self._window.session_stats.increment_tools()

    @pyqtSlot(str)
    def _on_agent_error(self, msg: str):
        self._on_error(f"Agent: {msg}")
        self._orchestrator.stop_all()

    def _refresh_notes_panel(self):
        if not self._window:
            return
        try:
            from tools.notes import list_notes
            result = list_notes()
            if result.get("status") == "success":
                self._window.notes_panel.load_notes(result.get("notes", []))
        except Exception as e:
            # print(f"Error refreshing notes: {e}")
            pass

    # ------------------------------------------------------------------
    # Tray / quit
    # ------------------------------------------------------------------

    def _open_settings_from_tray(self):
        if self._window:
            self._window._open_settings()

    def _quit(self):
        self._orchestrator.stop_all()
        self._qt_app.quit()
