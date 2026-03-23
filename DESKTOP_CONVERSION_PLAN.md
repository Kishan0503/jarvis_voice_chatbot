# JARVIS Desktop Application — Implementation Roadmap

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Phase 0: Pre-Conversion Setup](#2-phase-0-pre-conversion-setup)
3. [Phase 1: Project Restructuring & Foundation](#3-phase-1-project-restructuring--foundation)
4. [Phase 2: Desktop UI Shell (PyQt6)](#4-phase-2-desktop-ui-shell-pyqt6)
5. [Phase 3: Voice Pipeline Replacement](#5-phase-3-voice-pipeline-replacement)
6. [Phase 4: Backend Integration (Direct Python Calls)](#6-phase-4-backend-integration-direct-python-calls)
7. [Phase 5: System Control Tools](#7-phase-5-system-control-tools)
8. [Phase 6: Wake Word Detection](#8-phase-6-wake-word-detection)
9. [Phase 7: Camera Integration](#9-phase-7-camera-integration)
10. [Phase 8: Long-Term Memory System](#10-phase-8-long-term-memory-system)
11. [Phase 9: Proactive & Autonomous Behavior](#11-phase-9-proactive--autonomous-behavior)
12. [Phase 10: Polish, Packaging & Distribution](#12-phase-10-polish-packaging--distribution)
13. [Recommended Folder Structure](#13-recommended-folder-structure)
14. [UI/UX Design Specification](#14-uiux-design-specification)
15. [Challenge-to-Solution Mapping](#15-challenge-to-solution-mapping)
16. [Dependency Reference](#16-dependency-reference)
17. [Package Compatibility & Contingency Protocol](#17-package-compatibility--contingency-protocol)

---

## 1. Project Overview

### Current State

- **Type:** Web application (FastAPI + Vanilla JS + Tailwind CSS)
- **AI Engine:** Google Gemini (`gemini-2.5-flash`) with function-calling
- **TTS:** ElevenLabs streaming API with browser TTS fallback
- **STT:** Browser `webkitSpeechRecognition` (Chrome-only)
- **Auth:** JWT + bcrypt + SQLite (multi-user web auth)
- **Agents:** Dual-agent (Jarvis + Zara)
- **Tools:** Weather (OpenWeatherMap), Calendar (local datetime), Search (Google CSE)
- **Environment:** Python 3.12, Ubuntu 24.04

### Target State

- **Type:** Native desktop application (PyQt6) — full-screen HUD dashboard
- **AI Engine:** Google Gemini (unchanged) — called directly as Python functions
- **TTS:** ElevenLabs streaming + `edge-tts` fallback (+ `pyttsx3` offline last resort)
- **STT:** Local Whisper (faster-whisper) + `sounddevice` microphone
- **Auth:** None — single local user with first-run setup (no login/register)
- **Agent:** Jarvis only (Zara removed entirely)
- **Tools:** All existing + system control, file ops, clipboard, screen capture, notes
- **New Capabilities:** Wake word, camera feed, long-term memory, proactive scheduling, notes, notifications

### Architecture Shift

```
BEFORE (Web):
  Browser (JS) ──HTTP──► FastAPI ──► Gemini + Tools (Jarvis/Zara)

AFTER (Desktop):
  PyQt6 UI ──direct Python call──► GeminiClient ──► Gemini + Tools (Jarvis only)
  PyQt6 UI ◄──signals/slots──── Background Threads (STT, TTS, Wake Word, Camera)
```

### Key Design Decisions

| Decision | Choice |
|---|---|
| Agent | Jarvis only (Zara removed) |
| Authentication | None — single local user, first-run setup wizard |
| Window style | Frameless, translucent HUD aesthetic |
| Window launch | Full-screen maximized, resizable, remembers size/position |
| System tray | Yes — minimize to tray, keep running in background |
| Notes | Voice-created via Gemini tool, read-only (deletable), slide-out panel, modal popup to view |
| Notifications | All types, current session only, slide-out panel + live toasts |
| Camera | Toggleable with visible ON/OFF, hidden when off, 10fps, DeepFace deferred to later |
| Waveform | Removed as separate widget — avatar glow ring reacts to audio amplitude instead |
| Location | Auto-detect via IP (`ip-api.com`) + manual override in settings |
| Exit behavior | Confirmation dialog: "Quit completely or minimize to tray?" |

---

## 2. Phase 0: Pre-Conversion Setup

> **Goal:** Install all system-level dependencies and Python packages before writing any code.
> **Estimated Time:** 1-2 hours
> **Challenges Addressed:** Package compatibility, system dependencies

### Step 0.1: System Dependencies (Ubuntu 24.04)

```bash
sudo apt update
sudo apt install -y \
    portaudio19-dev \
    libportaudio2 \
    python3-pyaudio \
    python3-tk \
    python3-dev \
    ffmpeg \
    espeak \
    libespeak-dev \
    xdotool \
    xclip \
    scrot \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libegl1
```

**Why each is needed:**

| Package | Purpose |
|---|---|
| `portaudio19-dev` | Required for PyAudio fallback (microphone access) |
| `libportaudio2` | Runtime library for `sounddevice` (primary mic input) |
| `python3-pyaudio` | System-level PyAudio binding (backup for sounddevice) |
| `python3-tk`, `python3-dev` | Required by `mouseinfo` (dependency of `pyautogui-ng`) |
| `ffmpeg` | Audio format conversion (MP3→WAV for playback, used by `pydub`) |
| `espeak`, `libespeak-dev` | Backend for `pyttsx3` offline TTS last resort |
| `xdotool` | Window management and keyboard simulation on X11 |
| `xclip` | Clipboard operations on Linux |
| `scrot` | Screenshot capture on Linux |
| `libxcb-xinerama0` | Required by PyQt6 on Ubuntu |
| `libxcb-cursor0` | Required by PyQt6 on Ubuntu |
| `libegl1` | OpenGL support for PyQt6 rendering |

### Step 0.2: Create New Virtual Environment

```bash
cd /home/kishan/jarvis_voice_chatbot
python3 -m venv venv_desktop
source venv_desktop/bin/activate
```

### Step 0.3: Install Python Packages — Phase 1 Core

```bash
# Carry over existing essentials
pip install google-generativeai==0.8.5
pip install google-api-python-client==2.175.0
pip install elevenlabs==2.3.0
pip install requests==2.32.4
pip install python-dotenv==1.1.0
pip install pydantic==2.11.7
pip install pillow==11.3.0

# Desktop UI framework
pip install PyQt6

# Audio I/O (sounddevice is primary; pyaudio only as backup)
pip install sounddevice
pip install pygame
pip install pydub

# Speech-to-Text (local)
pip install faster-whisper

# TTS fallbacks (edge-tts is primary fallback, pyttsx3 is offline last resort)
pip install edge-tts
pip install pyttsx3

# System control (PyAutoGUI-ng is the maintained fork of pyautogui)
pip install psutil
pip install pyautogui-ng
pip install pyperclip
pip install mss
```

### Step 0.4: Install Python Packages — Phase 2 Advanced

```bash
# Wake word detection (pvrecorder is Picovoice's own audio recorder for Porcupine)
pip install pvporcupine
pip install pvrecorder

# Camera (DeepFace deferred — install opencv only for now)
pip install opencv-python

# Scheduling
pip install apscheduler
```

**Deferred to later phases (heavy downloads, not needed until then):**

```bash
# Phase 8 — Long-term memory (sentence-transformers pulls PyTorch ~2.5GB)
# Install ONLY when starting Phase 8:
pip install chromadb
pip install sentence-transformers

# Optional — Browser automation (downloads Chromium ~150MB)
# Install ONLY if browser automation is needed:
pip install playwright
playwright install chromium
```

### Step 0.5: Freeze New Requirements

```bash
pip freeze > requirements_desktop.txt
```

---

## 3. Phase 1: Project Restructuring & Foundation

> **Goal:** Reorganize the folder structure, remove Zara, decouple from FastAPI, set up local user config.
> **Estimated Time:** 3-4 hours
> **Challenges Addressed:** Challenge 4 (FastAPI role change), Challenge 5 (Auth removal), Zara removal

### Step 1.1: Create New Directory Structure

```bash
mkdir -p ui voice tools memory assets assets/sounds
```

### Step 1.2: Move Assets

```bash
cp frontend/jarvis2.gif assets/
```

Create a simple `assets/icon.png` (64x64 Jarvis-themed icon for system tray).

### Step 1.3: Remove Zara from `gemini_client.py`

**Changes:**

1. Remove the `"zara"` entry from `self.agent_instructions` — only keep `"jarvis"`
2. Remove the `agent` parameter from `send_message_to_gemini` — always use `"jarvis"`
3. Simplify `_get_session` — key by `user_email` only (no agent suffix)
4. Remove the `async` keyword from `send_message_to_gemini` so it can be called from a `QThread`

**Before:**
```python
async def send_message_to_gemini(self, user_message: str, agent: str, user_email: str) -> str:
```

**After:**
```python
def send_message_to_gemini(self, user_message: str, user_id: str = "local") -> str:
```

The `agent` parameter is gone — Jarvis is always the agent. The `user_email` becomes `user_id` with a default of `"local"` since there's no login system.

### Step 1.4: Remove Zara from `tools/elevenlabs_tts.py`

**Changes:**

- Remove the `"zara"` entry from `VOICE_IDS` — only keep `"jarvis"`
- Simplify `text_to_speech_stream` — remove the `agent` parameter, always use Jarvis voice

### Step 1.5: Set Up Local User Config

**Create `auth/local_user.py`** (replaces entire JWT auth system):

```python
import json
from pathlib import Path

USER_CONFIG_PATH = Path.home() / ".jarvis" / "user_config.json"

DEFAULT_CONFIG = {
    "username": "",
    "location": "",
    "preferences": {
        "temp_unit": "celsius",
        "language": "en",
        "wake_word_enabled": True,
        "camera_enabled": False,
        "tts_engine": "elevenlabs",
        "window_opacity": 0.92,
    },
    "first_run": True,
}

class LocalUser:
    def __init__(self):
        self.config_path = USER_CONFIG_PATH
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return json.load(f)
        return dict(DEFAULT_CONFIG)

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.data, f, indent=2)

    @property
    def is_first_run(self) -> bool:
        return self.data.get("first_run", True)

    @property
    def username(self) -> str:
        return self.data.get("username", "User")

    @property
    def location(self) -> str:
        return self.data.get("location", "")
```

**What this replaces:** All 4 files in `auth/` (auth_models.py, auth_routes.py, auth_utils.py, user_db.py) + JWT tokens + bcrypt + OAuth2.

### Step 1.6: Create `__init__.py` Files

```bash
touch ui/__init__.py voice/__init__.py memory/__init__.py
```

### Step 1.7: First-Run Setup Wizard

On first launch (`local_user.is_first_run == True`), show a simple dialog:

```
┌────────────────────────────────────────────────┐
│  Welcome to Jarvis                              │
│                                                  │
│  What should I call you?                        │
│  ┌──────────────────────────────────┐           │
│  │ Kishan                           │           │
│  └──────────────────────────────────┘           │
│                                                  │
│  Your city (for weather & time):                │
│  ┌──────────────────────────────────┐           │
│  │ Mumbai, India    [Auto-detect]   │           │
│  └──────────────────────────────────┘           │
│                                                  │
│  Temperature unit:  (●) Celsius  ( ) Fahrenheit │
│                                                  │
│              [Get Started]                       │
└────────────────────────────────────────────────┘
```

After submission: save to `~/.jarvis/user_config.json`, set `first_run = False`, proceed to main window.

---

## 4. Phase 2: Desktop UI Shell (PyQt6)

> **Goal:** Build the complete full-screen HUD dashboard with all panels.
> **Estimated Time:** 2-3 days
> **Challenges Addressed:** Challenge 1 (Frontend replacement), Challenge 8 (GIF animations)

### Step 2.1: Define Theme & Styles (`ui/styles.py`)

```python
JARVIS_THEME = {
    "primary": "#3b82f6",      # blue-500
    "accent": "#60a5fa",       # blue-400
    "glow": "rgba(59, 130, 246, 0.3)",
    "bg": "#0a0a0a",
    "surface": "#111111",
    "text": "#e5e7eb",
    "text_dim": "#9ca3af",
    "border": "#1e3a5f",
}

FONT_FAMILY = "Inter"
FONT_SIZE_NORMAL = 14
FONT_SIZE_HEADING = 24
FONT_SIZE_STATUS = 18
WINDOW_OPACITY = 0.92
BORDER_RADIUS = 16
```

### Step 2.2: System Tray Icon (`ui/system_tray.py`)

**Purpose:** Always-running tray icon that manages the main window.

**Functionality:**

- Left-click: Toggle main window visibility (show/hide)
- Right-click: Context menu (Show, Settings, Quit)
- Tooltip: "Jarvis — [username]'s Assistant" + current status
- Icon changes based on state (idle vs. active vs. speaking)

**Implementation:**

- Use `QSystemTrayIcon` with `QMenu`
- Connect `activated` signal to toggle window
- Use `showMessage()` for OS-native notification fallback

### Step 2.3: Main Application Entry (`ui/app.py`)

**Purpose:** Sets up the `QApplication`, system tray, and window lifecycle.

**Key responsibilities:**

- Initialize `QApplication` with dark theme palette
- Load the Inter font (bundled or system)
- Create system tray icon
- Check `local_user.is_first_run` — if true, show setup wizard; otherwise, show main window
- Launch main window as full-screen maximized
- Set up global hotkey (`Ctrl+Shift+J`) as kill switch
- Handle graceful shutdown (stop all threads)

### Step 2.4: Main HUD Window (`ui/main_window.py`)

**Purpose:** The primary full-screen dashboard — frameless, translucent, all-in-one interface.

**Window properties:**

- Frameless (`Qt.FramelessWindowHint`) — no OS title bar
- Translucent background (`Qt.WA_TranslucentBackground`) — HUD feel
- Launches maximized (full-screen)
- Resizable with minimum size of 900 x 600 px
- Remembers window size and position between sessions (saved to `~/.jarvis/window_state.json`)
- Custom drag handling on the top info bar area
- Custom resize handles on window edges
- Rounded corners (painted via `QPainter`)

**Full layout:**

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  Good afternoon, Kishan              Sat, Mar 14, 2026 • 3:45 PM  │
│                                      Mumbai, India • 28°C Cloudy   │
│                                                                    │
│                     ┌──────────────┐                               │
│                     │              │                               │
│                     │   JARVIS     │  ← Animated GIF avatar        │
│                     │  (animated)  │    with reactive glow ring    │
│                     │              │    (pulses with audio)        │
│                     └──────────────┘                               │
│                                                                    │
│                   "Jarvis is listening..."                          │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  You (3:40 PM): What's the weather?                         │  │
│  │  Jarvis (3:40 PM): It's 28°C and partly cloudy in Mumbai.  │  │
│  │  You (3:42 PM): Save a note to buy groceries tomorrow       │  │
│  │  Jarvis (3:42 PM): ✅ Note saved: "Buy groceries tomorrow"  │  │
│  │  You (3:44 PM): Open VS Code                                │  │
│  │  Jarvis (3:44 PM): ✅ Done, Sir. VS Code is open.          │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────┐  ┌─────────────────────────┐ ┌────┐ ┌──┐ ┌──┐ ┌──┐ ┌───┐│
│  │ 📷 │  │ Type a message...       │ │Send│ │🎤│ │📝│ │🔔│ │⚙ ││
│  │cam │  └─────────────────────────┘ └────┘ └──┘ └──┘ └──┘ └───┘│
│  └────┘                                                    ┌─────┐│
│                                                            │Exit ││
│                                                            └─────┘│
└────────────────────────────────────────────────────────────────────┘
```

**Layout sections (top to bottom):**

1. **Top Info Bar** (custom draggable area):
   - Left: Time-of-day greeting ("Good morning/afternoon/evening, [username]")
   - Right: Live date & time (updates every second) + location + mini weather
   - This area doubles as the drag handle for moving the window

2. **Center — Avatar Area:**
   - Jarvis animated GIF loaded via `QMovie` → `QLabel` (circular mask)
   - Surrounded by a glowing blue ring that reacts to audio amplitude:
     - When **listening**: glow pulses with microphone input intensity
     - When **speaking**: glow pulses with TTS audio output
     - When **idle**: gentle subtle ambient pulse
   - This replaces the separate waveform visualizer — cleaner, less clutter

3. **Status Text:**
   - "Jarvis is listening..." / "Jarvis is thinking..." / "Jarvis is speaking..."
   - Blue (#60a5fa) medium weight text, centered below avatar

4. **Conversation Transcript:**
   - Scrollable chat area taking the majority of vertical space
   - User messages: right-aligned, darker surface background
   - Jarvis messages: left-aligned, blue border accent
   - Action confirmations: shown with ✅ checkmark prefix
   - Auto-scroll to bottom on new messages
   - Timestamps in dim gray text
   - Limited to last 100 messages in UI (full history persisted in DB)

5. **Bottom Action Bar:**
   - 📷 Camera toggle (bottom-left): Shows live webcam feed when ON, hidden entirely when OFF
   - Text input field: For typing messages (hybrid voice + text)
   - Send button: Submit typed message
   - 🎤 Mic button: Start/stop voice input manually
   - 📝 Notes button: Opens slide-out notes panel from left
   - 🔔 Notifications button: Opens slide-out notifications panel from right (shows badge count for unread)
   - ⚙ Settings button: Opens settings modal
   - Exit button (red): Shows confirmation dialog — "Quit completely or minimize to tray?"

### Step 2.5: Slide-Out Notes Panel (`ui/notes_panel.py`)

**Purpose:** Displays a list of user-created notes with ability to view and delete.

**Behavior:**

- Hidden by default — main screen uses full width
- Triggered by: clicking the 📝 Notes icon in the bottom bar, OR voice command ("Jarvis, show my notes")
- Slides in from the left as an overlay panel (does not push main content)
- Dimmed overlay behind the panel (click outside to close)
- Slides back out on close

**Panel content:**

```
┌──────────────┐
│  📝 Notes    │
│  ──────────  │
│              │
│  Buy groceri │
│  es tomorrow │
│  Mar 14, 3PM │
│  [🗑 Delete] │
│              │
│  ──────────  │
│              │
│  Call Mom on │
│  Monday      │
│  Mar 14, 2PM │
│  [🗑 Delete] │
│              │
│  ──────────  │
│              │
│  (empty if   │
│   no notes)  │
│              │
└──────────────┘
```

**Clicking a note:** Opens a modal popup over the main window showing the full note content, timestamp, and a delete button. Dismissible by clicking outside, pressing Escape, or clicking the close button.

**How notes are created:** Via voice command only. User says something like "Jarvis, save a note that I have to buy groceries tomorrow." Gemini calls the `save_note` tool (see Phase 5). Jarvis confirms: "Note saved: Buy groceries tomorrow."

**Notes are:**
- Read-only (no editing after creation)
- Deletable (via the delete button in the panel or modal)
- Flat list (no categories or tags) sorted by newest first
- Stored in SQLite (`jarvis.db`)

### Step 2.6: Slide-Out Notifications Panel (`ui/notifications_panel.py`)

**Purpose:** Shows current session's notification history.

**Behavior:**

- Hidden by default
- Triggered by: clicking the 🔔 icon in the bottom bar, OR voice command ("Jarvis, show notifications")
- Slides in from the right as an overlay panel
- Badge count on the 🔔 icon shows number of unread notifications
- Clicking a notification marks it as read (badge count decreases)

**What generates notifications:**

- Scheduled reminders ("Call Mom at 6 PM")
- Proactive alerts (battery low, calendar event approaching)
- System actions completed ("VS Code opened successfully")
- Weather alerts
- All generated during the current session only (not persisted across restarts)

**Live toast behavior:** When a new notification arrives, a toast popup briefly appears at the top-right of the screen (auto-dismiss after 5 seconds), regardless of whether the panel is open.

```
┌──────────────────────────────────────┐
│  🔵 Jarvis                           │
│  "Your standup starts in 15 min."    │
│              [Dismiss]  [Snooze 5m]  │
└──────────────────────────────────────┘
```

### Step 2.7: Conversation Transcript Widget (`ui/transcript_widget.py`)

**Purpose:** Scrolling chat history — the core interaction display.

**Implementation details:**

- Use `QScrollArea` containing custom `QFrame` message bubbles
- User messages: right-aligned, darker surface background (#111111)
- Jarvis messages: left-aligned, blue (#1e3a5f) border
- Action confirmations: shown with a ✅ checkmark prefix
- Auto-scroll to bottom on new messages
- Timestamps in dim text (#9ca3af)
- Support for markdown rendering in Jarvis responses (use `QTextBrowser` with HTML)
- Limit to last 100 messages in UI for performance

### Step 2.8: Settings Panel (`ui/settings_panel.py`)

**Purpose:** User-accessible configuration modal.

**Sections:**

```
┌─────────────────────────────────────────────────────┐
│  Settings                                            │
│                                                      │
│  ── Profile ──                                      │
│  Name: [Kishan                    ]                 │
│  Location: [Mumbai, India   ] [Auto-detect]         │
│  Temp Unit: (●) Celsius  ( ) Fahrenheit             │
│                                                      │
│  ── Voice ──                                        │
│  TTS Engine: [ElevenLabs ▾]  Fallback: [System ▾]  │
│  STT Engine: [Whisper Local ▾]                      │
│  Wake Word: [✓ Enabled]                             │
│                                                      │
│  ── Permissions ──                                  │
│  [✓] Allow app control                              │
│  [✓] Allow file access                              │
│  [ ] Allow command execution (requires confirmation) │
│  [ ] Camera access                                  │
│                                                      │
│  ── Appearance ──                                   │
│  Window Opacity: [━━━━━━●━━] 80%                    │
│                                                      │
│  ── Memory ──                                       │
│  [View Stored Memories]  [Clear All Memory]         │
│                                                      │
│  [Save]                               [Reset]       │
└─────────────────────────────────────────────────────┘
```

**Implementation:** `QDialog` as a modal. All settings persist to `~/.jarvis/user_config.json` via `LocalUser`.

### Step 2.9: Rewrite `main.py` Entry Point

**Current `main.py`:** FastAPI app creation, CORS, routes, endpoints.

**New `main.py`:** PyQt6 application launcher.

```python
import sys
from PyQt6.QtWidgets import QApplication
from ui.app import JarvisApp

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    jarvis = JarvisApp()
    jarvis.start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

---

## 5. Phase 3: Voice Pipeline Replacement

> **Goal:** Replace browser-based STT and audio playback with native Python implementations.
> **Estimated Time:** 1.5-2 days
> **Challenges Addressed:** Challenge 2 (STT replacement), Challenge 3 (Audio playback replacement)

### Step 3.1: Microphone Manager (`voice/stt.py`)

**Purpose:** Captures audio from microphone and transcribes using Whisper.

**Architecture:**

```
Microphone (sounddevice) → Voice Activity Detection → Audio Buffer
    → faster-whisper transcription → text result
    → Emit signal to UI thread
```

**Implementation approach:**

- Run in a `QThread` to never block the UI
- Use `sounddevice` to open a 16kHz mono audio stream (preferred over PyAudio — actively maintained, pure-pip install, no compilation needed)
- Implement simple VAD (Voice Activity Detection):
  - Monitor RMS amplitude of audio chunks
  - When amplitude exceeds threshold → start recording
  - When amplitude drops below threshold for 1.5s → stop recording
  - Feed the recorded audio buffer to `faster-whisper`
- Emit `transcription_ready(str)` signal when text is available
- Emit `amplitude_changed(float)` signal to drive the avatar glow ring animation

**faster-whisper model selection:**

| Model | Size | Speed | Accuracy | Recommendation |
|---|---|---|---|---|
| `tiny` | 75MB | ~10x realtime | Good for clear speech | Development/testing |
| `base` | 140MB | ~7x realtime | Good | Default for most users |
| `small` | 460MB | ~4x realtime | Very good | Recommended for production |
| `medium` | 1.5GB | ~2x realtime | Excellent | If you have the RAM |

**Default:** `base` model — good balance of speed and accuracy.

### Step 3.2: TTS & Audio Playback (`voice/tts.py` and `voice/audio_player.py`)

**Purpose:** Convert Gemini's text response to speech and play it.

**`voice/tts.py` architecture:**

```
Text response from Gemini
  → Try ElevenLabs API (from existing tools/elevenlabs_tts.py, Jarvis voice only)
    → Stream MP3 bytes
    → Save to temp file
    → Play via audio_player
  → On failure: fallback to edge-tts (Microsoft Edge online TTS, free, natural voices)
  → If no internet: last resort pyttsx3 (offline system TTS via espeak)
```

**Key difference from web app:** ElevenLabs is called directly as a Python function (reuse `tools/elevenlabs_tts.py`), the audio bytes are saved to a temp file, and `pygame.mixer` plays them. No HTTP round-trip.

**`voice/audio_player.py`:**

- Initialize `pygame.mixer` at startup
- `play(filepath)` — plays MP3/WAV file
- `stop()` — stops current playback
- `is_playing()` — returns True if audio is active
- Emit `playback_finished` signal when audio ends
- Emit `amplitude_changed(float)` to drive avatar glow ring during speech
- Run playback monitoring in a `QThread`

**Fallback chain:**

1. ElevenLabs API → MP3 → pygame playback (best quality, requires API key + internet)
2. If ElevenLabs fails → `edge-tts` (free Microsoft Edge TTS, near-natural voices, requires internet)
3. If no internet → `pyttsx3` via `espeak` (offline last resort, robotic but functional)

### Step 3.3: Conversation Orchestrator

**Purpose:** Manages the listen → think → speak → listen cycle.

This replaces the state machine that was in `app.js` (the `isConversationActive`, `isSpeaking`, `startVoiceInput`, `speakResponse`, `finalizeSpeechCycle` functions).

**State machine:**

```
IDLE → (wake word or mic click) → LISTENING → (speech detected) → PROCESSING
  → (Gemini responds) → SPEAKING → (audio finished) → LISTENING
  → (user clicks stop or says "stop") → IDLE
```

**Implementation:**

- A single orchestrator class that owns the STT thread, TTS thread, and Gemini client
- Uses Qt signals/slots to move between states
- Updates UI (status text, avatar glow animation) via signals
- Never blocks the UI thread

---

## 6. Phase 4: Backend Integration (Direct Python Calls)

> **Goal:** Wire the UI to Gemini and tools via direct function calls instead of HTTP.
> **Estimated Time:** 0.5-1 day
> **Challenges Addressed:** Challenge 4 (FastAPI role change), Challenge 6 (Threading)

### Step 4.1: Create Gemini Worker Thread

**Purpose:** Run Gemini API calls in a background thread to avoid freezing the UI.

**Architecture:**

```python
class GeminiWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, gemini_client, message):
        super().__init__()
        self.client = gemini_client
        self.message = message

    def run(self):
        try:
            reply = self.client.send_message_to_gemini(self.message)
            self.response_ready.emit(reply)
        except Exception as e:
            self.error_occurred.emit(str(e))
```

**Key simplification from original plan:** No `agent` or `user_email` parameters needed — always Jarvis, always local user.

### Step 4.2: Wire Signals Through the Pipeline

```
STT.transcription_ready(text)
  → Orchestrator.on_transcription(text)
    → GeminiWorker.start(text)
      → GeminiWorker.response_ready(reply)
        → Orchestrator.on_gemini_response(reply)
          → TTS.speak(reply)
            → AudioPlayer.playback_finished()
              → Orchestrator.on_speech_complete()
                → STT.start_listening()
```

All communication between threads happens via Qt's signal/slot mechanism, which is thread-safe.

### Step 4.3: Preserve Existing Tool Architecture

Your existing tools (`tools/weather.py`, `tools/calendar.py`, `tools/search.py`) are already pure Python with no FastAPI dependency. They work exactly as-is:

- `gemini_client.py` registers them as `all_tool_functions`
- Gemini calls them via function-calling
- Results flow back through the same `send_message_to_gemini` method

**Zero changes needed to any existing tool file.**

---

## 7. Phase 5: System Control Tools + Notes

> **Goal:** Add tools that give Jarvis real OS-level capabilities and note-taking.
> **Estimated Time:** 1.5-2 days
> **Challenges Addressed:** Enables the "real JARVIS" functionality, notes feature

### Step 5.1: Application Control (`tools/system_control.py`)

**Functions to implement:**

| Function | Description | Gemini Tool Name |
|---|---|---|
| `open_application(name)` | Launch an app by name | `open_application` |
| `close_application(name)` | Terminate an app by name | `close_application` |
| `list_running_apps()` | List all running processes | `list_running_apps` |
| `get_system_info()` | CPU, RAM, disk, battery status | `get_system_info` |
| `set_system_volume(level)` | Set audio volume (0-100) | `set_volume` |
| `lock_screen()` | Lock the desktop session | `lock_screen` |

**Safety guardrails:**

- `close_application`: Only closes user-space apps, never system processes
- `lock_screen`: Always requires confirmation
- All destructive actions return `{"status": "requires_confirmation", "action": "..."}` so the orchestrator can ask the user before proceeding

### Step 5.2: File Operations (`tools/file_ops.py`)

| Function | Description |
|---|---|
| `find_files(pattern, search_path)` | Search for files by name/glob |
| `read_file_content(filepath)` | Read text file contents |
| `list_directory(path)` | List files in a directory |
| `get_file_info(filepath)` | Size, modified date, type |
| `open_file_default(filepath)` | Open with default OS app |

### Step 5.3: Clipboard & Screen (`tools/clipboard.py`, `tools/screen.py`)

**Clipboard:**

| Function | Description |
|---|---|
| `get_clipboard()` | Read current clipboard text |
| `set_clipboard(text)` | Write text to clipboard |

**Screen:**

| Function | Description |
|---|---|
| `take_screenshot()` | Capture screen, save to temp file |
| `analyze_screenshot()` | Take screenshot → send to Gemini Vision for description |

### Step 5.4: Notes Tool (`tools/notes.py`)

**Purpose:** Gemini tool for saving and managing notes via voice commands.

| Function | Description | Gemini Tool Name |
|---|---|---|
| `save_note(content)` | Save a new note with timestamp | `save_note` |
| `list_notes()` | Return all saved notes | `list_notes` |
| `delete_note(note_id)` | Delete a note by ID | `delete_note` |

**Storage:** SQLite table in `jarvis.db`:

```sql
CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Usage flow:**
- User: "Jarvis, save a note that I have to buy groceries tomorrow"
- Gemini calls `save_note("Buy groceries tomorrow")`
- Jarvis responds: "Note saved: Buy groceries tomorrow"
- User: "Jarvis, show my notes" → triggers the slide-out notes panel in the UI
- User: "Jarvis, delete my first note" → Gemini calls `delete_note(1)`

### Step 5.5: Register All New Tools with Gemini

**Update `gemini_client.py`** to include the new tool declarations:

```python
from tools.system_control import system_tool_declarations, tool_functions as system_tool_functions
from tools.file_ops import file_tool_declarations, tool_functions as file_tool_functions
from tools.clipboard import clipboard_tool_declarations, tool_functions as clipboard_tool_functions
from tools.screen import screen_tool_declarations, tool_functions as screen_tool_functions
from tools.notes import notes_tool_declarations, tool_functions as notes_tool_functions

self.available_gemini_tools = [
    Tool(function_declarations=[
        weather_tool_declaration,
        calendar_tool_declaration,
        search_tool_declaration,
        *system_tool_declarations,
        *file_tool_declarations,
        *clipboard_tool_declarations,
        *screen_tool_declarations,
        *notes_tool_declarations,
    ])
]
```

### Step 5.6: Update Jarvis System Prompt

Since Zara is removed, there's only one system prompt to maintain:

```python
"jarvis": (
    "You are Jarvis, a witty, humble male AI assistant with a human-like tone "
    "and light British charm. Speak naturally—friendly, playful, sometimes humorous. "
    "Be helpful, not a know-it-all. "
    "**Always use 'get_current_weather' for weather. NEVER answer weather directly.** "
    "**Always use 'get_current_datetime' for date/time. NEVER answer directly.** "
    "**Use 'google_search' for general knowledge or unknown info. Do NOT guess.** "
    "**Use 'save_note' when the user asks to save/remember/note something.** "
    "**Use 'list_notes' when the user asks to see/show their notes.** "
    "**Use 'delete_note' when the user asks to delete/remove a note.** "
    "You can open/close applications, search files, read/write clipboard, "
    "take screenshots, and check system info. "
    "For any destructive action, always confirm with the user first."
)
```

---

## 8. Phase 6: Wake Word Detection

> **Goal:** Enable hands-free "Hey Jarvis" activation.
> **Estimated Time:** 1 day
> **Challenges Addressed:** Always-on listening without clicking

### Step 6.1: Implement Wake Word Listener (`voice/wake_word.py`)

**Architecture:**

```
Microphone (always open) → Porcupine processes each frame
  → Wake word detected → Emit signal → Orchestrator activates STT
```

**Implementation details:**

- Run in a dedicated `QThread` (separate from STT thread)
- Uses `pvporcupine` with a pre-built "Jarvis" wake word, or train a custom one via Picovoice Console
- Processes audio frames continuously with minimal CPU (~3-5%)
- On detection: play a short chime (`assets/sounds/wake.wav`), emit `wake_word_detected` signal
- Automatically pauses during TTS playback (to avoid self-triggering)

### Step 6.2: Porcupine API Key Setup

```bash
# Sign up at https://console.picovoice.ai/ for a free access key
# Add to .env:
PICOVOICE_ACCESS_KEY=your_access_key_here
```

Update `config.py` to load this key.

### Step 6.3: Integration with Orchestrator

```
Wake Word Thread (always running)
  → wake_word_detected signal
    → Orchestrator pauses wake word listener
    → Orchestrator starts STT listener
    → ... conversation cycle ...
    → Orchestrator stops STT listener
    → Orchestrator resumes wake word listener
```

---

## 9. Phase 7: Camera Integration

> **Goal:** Live camera feed with toggleable display. DeepFace emotion detection deferred to later.
> **Estimated Time:** 1 day
> **Challenges Addressed:** Visual awareness (Phase 1 — feed display only)

### Step 7.1: Camera Feed Widget

**Purpose:** Show a live webcam feed in the bottom-left of the main window.

**Implementation:**

- Run camera capture in a `QThread` using `cv2.VideoCapture(0)`
- Render at 10fps (performance-friendly)
- Display via `QLabel` with `QImage` conversion
- ON/OFF toggle button directly on the camera area (clearly visible)
- When camera is OFF: the entire camera widget is hidden (space reclaimed by the layout)
- When camera is ON: small feed (~160x120px) shown at bottom-left with a green "LIVE" indicator

### Step 7.2: Visual Question Answering (Camera Tool)

**New tool: `analyze_camera_view`**

```python
def analyze_camera_view(question: str = "What do you see?"):
    """Capture current camera frame and send to Gemini Vision API"""
    ret, frame = cap.read()
    # Convert to PIL Image → send to Gemini's multimodal endpoint
    # Return Gemini's description
```

User: "Jarvis, what am I holding?" → Camera captures frame → Gemini Vision analyzes → Jarvis responds.

### Step 7.3: DeepFace Emotion Detection (Deferred)

This feature is **intentionally deferred** to after the core app is stable. When implemented later:

- Install `deepface` and `mediapipe`
- Add emotion sampling every 3 seconds from the camera feed
- Inject detected emotion into Gemini's context for adaptive responses
- Add presence detection (face absent for 5+ min → dormant mode)

---

## 10. Phase 8: Long-Term Memory System

> **Goal:** Give Jarvis persistent memory across conversations.
> **Estimated Time:** 1.5-2 days
> **Challenges Addressed:** Making the assistant truly personal

### Step 8.1: Vector Store Setup (`memory/vector_store.py`)

**Technology:** ChromaDB (local, embedded, no server needed)

**Two collections:**

1. **Episodic Memory** — What happened in conversations:
   ```
   Collection: "conversations"
   Each entry: { text: "User asked about weather in Mumbai", timestamp }
   ```

2. **Semantic Memory** — Facts about the user:
   ```
   Collection: "user_facts"
   Each entry: { text: "User's name is Kishan", category: "identity", source: "conversation" }
   ```

### Step 8.2: Memory Extraction Pipeline

After each conversation turn:

1. Save the user message + Jarvis response as an episodic memory
2. Ask Gemini (via a lightweight side-call): "Extract any personal facts about the user from this conversation. Return as JSON."
3. Store extracted facts in semantic memory

### Step 8.3: Memory Retrieval (RAG)

Before each new message to Gemini:

1. Query `vector_store.similarity_search(user_message, k=5)` for relevant past conversations
2. Query `user_facts` for relevant personal facts
3. Inject as context:

```
[MEMORY CONTEXT]
- You previously told me your favorite food is biryani (March 10, 2026)
- Last time you asked about Mumbai weather, it was 31°C (March 14, 2026)
[END MEMORY CONTEXT]
```

### Step 8.4: User Profile (`memory/user_profile.py`)

**Structured data beyond vector search:**

```python
profile = {
    "name": "Kishan",
    "location": "India",
    "timezone": "Asia/Kolkata",
    "wake_time": "07:00",
    "work_hours": "09:00-18:00",
    "interests": ["coding", "AI", "music"],
    "preferred_temp_unit": "celsius",
    "communication_style": "casual",
}
```

Stored in SQLite (`jarvis.db`).

---

## 11. Phase 9: Proactive & Autonomous Behavior

> **Goal:** Jarvis acts on its own — reminders, briefings, alerts.
> **Estimated Time:** 1-2 days
> **Challenges Addressed:** Moving from reactive chatbot to proactive assistant

### Step 9.1: Scheduler Setup

**Technology:** APScheduler with `BackgroundScheduler`

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
scheduler.start()

# Morning briefing
scheduler.add_job(morning_briefing, 'cron', hour=7, minute=0)

# Calendar reminder check every 15 minutes
scheduler.add_job(check_reminders, 'interval', minutes=15)

# Evening summary
scheduler.add_job(evening_summary, 'cron', hour=22, minute=0)

# System health check every hour
scheduler.add_job(system_health_check, 'interval', hours=1)
```

### Step 9.2: Proactive Actions

| Action | Trigger | What Jarvis Does | Notification? |
|---|---|---|---|
| Morning Briefing | 7:00 AM daily | Weather + calendar + top news → speaks summary | Yes |
| Calendar Reminder | 15 min before event | Toast notification + voice alert | Yes |
| Battery Warning | Battery < 20% | "Sir, battery at 18%. Plug in soon." | Yes |
| System Overload | CPU > 90% for 5 min | "You have 47 Chrome tabs. Want me to close some?" | Yes |
| Idle Check-in | No interaction for 2 hours | "Everything alright, Sir? Need anything?" | No (voice only) |
| Evening Summary | 10:00 PM daily | Recap of tasks done, tomorrow's schedule | Yes |

All notifications are added to the notifications panel (current session history) and trigger a live toast popup.

### Step 9.3: User-Defined Reminders

**New tool: `set_reminder`**

```python
def set_reminder(message: str, time: str):
    """Schedule a reminder. Time can be relative ('in 30 minutes') or absolute ('at 3:00 PM')"""
    # Parse time → add APScheduler job → confirm to user
```

User: "Jarvis, remind me to call Mom at 6 PM"
→ Gemini calls `set_reminder("Call Mom", "18:00")`
→ At 6 PM: toast notification + voice "Sir, you wanted to call your mother."
→ Added to notification history panel

---

## 12. Phase 10: Polish, Packaging & Distribution

> **Goal:** Make the app production-ready, installable, and distributable.
> **Estimated Time:** 2-3 days
> **Challenges Addressed:** Challenge 7 (Packaging & distribution)

### Step 10.1: Error Handling & Resilience

- Wrap every thread's `run()` in try/except → emit error signal → show toast notification
- Auto-restart crashed threads (STT, wake word, camera) with exponential backoff
- Graceful degradation: if ElevenLabs is down → try edge-tts → last resort pyttsx3; if Whisper fails → show text input
- Log all errors to `~/.jarvis/logs/jarvis.log` with rotation (use Python `logging` module)

### Step 10.2: Kill Switch & Safety

- Global hotkey `Ctrl+Shift+J`: immediately stops all threads, cancels all actions, returns to idle
- All system control actions log to `~/.jarvis/logs/actions.log` (audit trail)
- Confirmation dialog for destructive operations (delete files, close apps, execute commands)
- Camera privacy: visible green "LIVE" indicator when camera is active, clear ON/OFF toggle

### Step 10.3: Performance Optimization

- Lazy-load heavy modules (Whisper model, ChromaDB) only when first needed
- Cache Whisper model in `~/.jarvis/models/` instead of re-downloading
- Use `faster-whisper` with `int8` quantization for reduced memory
- Limit conversation transcript to last 100 messages in UI (full history in DB)
- Camera feed at 10fps (not 30fps)
- Debounce weather/location updates in the top info bar (update every 15 minutes, not every second)

### Step 10.4: Packaging with PyInstaller

```bash
pip install pyinstaller

pyinstaller --name "Jarvis" \
    --icon assets/icon.png \
    --add-data "assets:assets" \
    --add-data ".env:.env" \
    --hidden-import PyQt6 \
    --hidden-import faster_whisper \
    --noconsole \
    --onedir \
    main.py
```

This creates a `dist/Jarvis/` folder with a self-contained executable.

### Step 10.5: Linux Desktop Integration

Create `jarvis.desktop` file:

```ini
[Desktop Entry]
Name=Jarvis AI Assistant
Comment=Your personal AI companion
Exec=/path/to/Jarvis
Icon=/path/to/icon.png
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
```

```bash
cp jarvis.desktop ~/.local/share/applications/
```

### Step 10.6: Auto-Start on Login (Optional)

```bash
mkdir -p ~/.config/autostart
cp jarvis.desktop ~/.config/autostart/
```

---

## 13. Recommended Folder Structure

Final complete structure after all phases:

```
jarvis_voice_chatbot/
│
├── main.py                          ← Entry point: launches PyQt6 app
├── config.py                        ← Environment variable loader (unchanged)
├── gemini_client.py                 ← Gemini API + tool orchestration (Jarvis only)
│
├── ui/                              ← All GUI components
│   ├── __init__.py
│   ├── app.py                       ← QApplication setup, lifecycle management
│   ├── main_window.py               ← Frameless full-screen HUD dashboard
│   ├── setup_wizard.py              ← First-run setup dialog
│   ├── settings_panel.py            ← Settings modal
│   ├── transcript_widget.py         ← Scrollable chat history
│   ├── notes_panel.py               ← Slide-out notes panel + note modal
│   ├── notifications_panel.py       ← Slide-out notifications panel + toasts
│   ├── camera_widget.py             ← Toggleable live webcam feed
│   ├── system_tray.py               ← Tray icon + context menu
│   └── styles.py                    ← Theme colors, fonts, dimensions
│
├── voice/                           ← All audio/voice components
│   ├── __init__.py
│   ├── stt.py                       ← Whisper STT + microphone capture
│   ├── tts.py                       ← ElevenLabs (Jarvis voice) + edge-tts + pyttsx3 fallback
│   ├── wake_word.py                 ← Porcupine "Hey Jarvis" detection
│   └── audio_player.py             ← pygame MP3/WAV playback
│
├── tools/                           ← Gemini function-calling tools
│   ├── __init__.py
│   ├── weather.py                   ← OpenWeatherMap (unchanged)
│   ├── calendar.py                  ← Date/time (unchanged)
│   ├── search.py                    ← Google Custom Search (unchanged)
│   ├── elevenlabs_tts.py            ← ElevenLabs streaming (Jarvis voice only)
│   ├── notes.py                     ← Save, list, delete notes
│   ├── system_control.py            ← App management, volume, lock
│   ├── file_ops.py                  ← File search, read, move, open
│   ├── clipboard.py                 ← Clipboard read/write
│   └── screen.py                    ← Screenshot + Gemini Vision
│
├── memory/                          ← Persistent memory system
│   ├── __init__.py
│   ├── vector_store.py              ← ChromaDB episodic + semantic memory
│   └── user_profile.py             ← Structured user facts + preferences
│
├── auth/                            ← Local user config
│   ├── __init__.py
│   └── local_user.py               ← JSON-based local user config
│
├── assets/                          ← Static resources
│   ├── jarvis2.gif                  ← Jarvis avatar animation
│   ├── icon.png                     ← System tray icon (64x64)
│   └── sounds/
│       ├── wake.wav                 ← Wake word acknowledgment chime
│       └── notification.wav         ← Reminder/alert sound
│
├── frontend/                        ← ARCHIVED — original web app (reference only)
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── .env                             ← API keys (unchanged)
├── jarvis.db                        ← SQLite database (notes, memories, preferences)
├── requirements.txt                 ← Original web deps (archived)
├── requirements_desktop.txt         ← Desktop app dependencies
├── jarvis.desktop                   ← Linux desktop entry file
└── README.md                        ← Updated documentation
```

---

## 14. UI/UX Design Specification

### 14.1 Design Philosophy

**Full-screen HUD dashboard.** The interface fills the screen with a frameless, translucent, JARVIS-inspired aesthetic. Clean, uncluttered by default — notes and notifications slide in only when needed.

### 14.2 Color System (Jarvis Theme Only)

| Token | Value | Usage |
|---|---|---|
| `primary` | `#3b82f6` | Borders, active elements, Jarvis name, buttons |
| `accent` | `#60a5fa` | Hover states, highlights, status text |
| `glow` | `rgba(59,130,246,0.3)` | Avatar glow ring, button hover shadow |
| `bg` | `#0a0a0a` | Window background |
| `surface` | `#111111` | Cards, input fields, message bubbles, panels |
| `text` | `#e5e7eb` | Primary text |
| `text_dim` | `#9ca3af` | Timestamps, secondary text, labels |
| `border` | `#1e3a5f` | Subtle borders, message bubble outlines |
| `danger` | `#ef4444` | Exit button, delete actions |
| `success` | `#22c55e` | Action confirmations (✅), camera LIVE indicator |

### 14.3 Typography

| Element | Font | Size | Weight |
|---|---|---|---|
| Greeting ("Good afternoon, Kishan") | Inter | 20px | Semi-Bold (600) |
| Date/Time/Weather info | Inter | 14px | Regular (400) |
| Status Text ("Jarvis is listening...") | Inter | 18px | Medium (500) |
| Chat Messages | Inter | 14px | Regular (400) |
| Timestamps | Inter | 11px | Regular (400) |
| Input Field | Inter | 14px | Regular (400) |
| Panel Headings (Notes, Notifications) | Inter | 18px | Semi-Bold (600) |
| Button Labels | Inter | 13px | Medium (500) |

### 14.4 Window Properties

| Property | Value |
|---|---|
| Launch State | Full-screen maximized |
| Minimum Size | 900 x 600 px |
| Border Radius | 16px |
| Background Opacity | 92% (configurable 60-100% in settings) |
| Window Flags | Frameless, Translucent Background |
| Position Persistence | Saves size/position to `~/.jarvis/window_state.json` |
| Custom Drag Area | Top info bar (greeting + date/time row) |
| Custom Resize | Edge handles on all 4 sides + 4 corners |

### 14.5 Animation Specifications

| Animation | Duration | Easing | Trigger |
|---|---|---|---|
| Window show/hide | 300ms | ease-in-out | Tray click / wake word |
| Avatar glow ring pulse (speaking) | 800ms loop | ease-in-out | While TTS is playing |
| Avatar glow ring pulse (listening) | 600ms loop | ease-in-out | While STT is active |
| Avatar glow ring pulse (idle) | 3000ms loop | ease-in-out | When idle |
| Message bubble appear | 200ms | ease-out | New message added |
| Notes panel slide-in | 300ms | ease-out | Click 📝 button |
| Notes panel slide-out | 200ms | ease-in | Click outside / close |
| Notifications panel slide-in | 300ms | ease-out | Click 🔔 button |
| Notifications panel slide-out | 200ms | ease-in | Click outside / close |
| Toast notification slide-in | 300ms | ease-out | Proactive alert |
| Toast notification slide-out | 200ms | ease-in | Dismiss / timeout 5s |

### 14.6 Display Modes

**Mode 1: Main Dashboard (default)**

Full-screen HUD with all elements visible as per the layout in Step 2.4. This is the primary mode.

**Mode 2: Minimized to Tray**

- Window is hidden
- System tray icon remains active
- Wake word listener stays active in background
- Proactive notifications still fire as OS-native tray notifications
- Click tray icon or say "Hey Jarvis" to restore the dashboard

### 14.7 Slide-Out Panels

Both panels overlay on top of the main content (main content is dimmed slightly). They do NOT take permanent screen space.

**Notes Panel (from left):**
- Width: ~300px
- Contains: flat list of notes, sorted newest first, each with content preview, timestamp, and delete button
- Click a note → opens a modal popup with full content
- Panel only appears when user has notes AND activates it

**Notifications Panel (from right):**
- Width: ~350px
- Contains: chronological list of session notifications, each with icon, message, and timestamp
- Unread badge count on the 🔔 button
- Panel only appears when user activates it

### 14.8 Notification Toasts

Slide in from top-right corner, independent of the notifications panel:

```
┌──────────────────────────────────────┐
│  🔵 Jarvis                           │
│  "Your standup starts in 15 min."    │
│              [Dismiss]  [Snooze 5m]  │
└──────────────────────────────────────┘
```

- Auto-dismiss after 5 seconds
- Click to open notifications panel
- Use `QSystemTrayIcon.showMessage()` as fallback when window is minimized to tray

### 14.9 Camera Feed Area

- Position: bottom-left, below the chat transcript, left of the bottom action bar
- Size: ~160x120px
- Shows a live webcam feed at 10fps when camera is ON
- Green "LIVE" indicator in the top-left corner of the feed
- Clear ON/OFF toggle button overlaid on the feed area
- When OFF: the entire widget is hidden, the layout reclaims the space
- When ON: appears with a subtle fade-in animation

### 14.10 First-Run Setup Wizard

Shown only once, on the very first launch:

```
┌────────────────────────────────────────────────┐
│                                                  │
│            Welcome to Jarvis                     │
│                                                  │
│  What should I call you?                        │
│  ┌──────────────────────────────────┐           │
│  │                                  │           │
│  └──────────────────────────────────┘           │
│                                                  │
│  Your city (for weather & time):                │
│  ┌──────────────────────────────────┐           │
│  │                     [Auto-detect]│           │
│  └──────────────────────────────────┘           │
│                                                  │
│  Temperature unit:  (●) Celsius  ( ) Fahrenheit │
│                                                  │
│              [Get Started]                       │
│                                                  │
└────────────────────────────────────────────────┘
```

Centered on screen, dark theme, blue accent on the "Get Started" button.

---

## 15. Challenge-to-Solution Mapping

| # | Challenge | Solution | Phase |
|---|---|---|---|
| 1 | **Entire frontend must be replaced** (735 lines JS + HTML + CSS are browser-only) | Rebuild as PyQt6 full-screen HUD dashboard with 10 widget files in `ui/` | Phase 2 |
| 2 | **STT replacement** (`webkitSpeechRecognition` is Chrome-only) | `faster-whisper` local model + `sounddevice` for mic access | Phase 3, Step 3.1 |
| 3 | **Audio playback replacement** (`new Audio()`, `URL.createObjectURL` are browser APIs) | `pygame.mixer` for MP3 playback + `edge-tts` / `pyttsx3` fallback chain | Phase 3, Step 3.2 |
| 4 | **FastAPI's role changes** (no longer needed as HTTP server) | Remove FastAPI. Call `gemini_client.send_message_to_gemini()` directly. Wrap in `QThread`. | Phase 4 |
| 5 | **Auth unnecessary for desktop** (JWT/bcrypt for multi-user web is overkill) | Replace with `auth/local_user.py` — JSON config at `~/.jarvis/user_config.json` + first-run wizard | Phase 1, Step 1.5 |
| 6 | **Threading & async model changes** (UI must never block) | All heavy work in `QThread` workers. Communication via Qt signals/slots. | Phase 4, Step 4.1 |
| 7 | **Application packaging & distribution** | PyInstaller bundling + `.desktop` file + optional auto-start | Phase 10 |
| 8 | **GIF animations for avatar** | `QMovie` → `QLabel` in PyQt6 (native animated GIF support) | Phase 2, Step 2.4 |
| 9 | **Zara removal simplification** | Remove all dual-agent logic, voice selection, theme switching. Single Jarvis agent throughout. | Phase 1, Steps 1.3-1.4 |
| 10 | **Notes feature (new)** | Gemini `save_note` tool + SQLite storage + slide-out panel + modal view | Phase 5, Step 5.4 |
| 11 | **Notifications system (new)** | Live toasts + session history panel + badge count | Phase 2, Step 2.6 + Phase 9 |

---

## 16. Dependency Reference

### Complete Package List

**Core (carry over from current project):**

```
google-generativeai==0.8.5
google-api-python-client==2.175.0
google-auth==2.40.3
elevenlabs==2.3.0
requests==2.32.4
python-dotenv==1.1.0
pydantic==2.11.7
pillow==11.3.0
```

**Desktop UI:**

```
PyQt6
```

**Audio & TTS Fallback:**

```
sounddevice          # Primary mic input (actively maintained, pure-pip)
pygame               # MP3/WAV audio playback
pydub                # Audio format conversion utilities
edge-tts             # Primary TTS fallback (free, natural Microsoft voices)
pyttsx3              # Offline TTS last resort (via espeak)
```

> **Note:** `pyaudio` is NOT pip-installed. The system package `python3-pyaudio` is kept as a backup
> if `sounddevice` encounters issues on a specific machine. `sounddevice` is preferred because it
> installs cleanly via pip without requiring C compilation.

**Speech-to-Text:**

```
faster-whisper
```

**Wake Word:**

```
pvporcupine          # Wake word engine
pvrecorder           # Picovoice's audio recorder (optimized for Porcupine)
```

**System Control:**

```
psutil               # Process/system info (CPU, RAM, disk, battery)
pyautogui-ng         # Maintained fork of pyautogui (keyboard, mouse, screenshot automation)
pyperclip            # Clipboard read/write
mss                  # Fast cross-platform screenshot capture
```

> **Note:** We use `pyautogui-ng` instead of the original `pyautogui` because the original
> package is semi-abandoned and has known Python 3.12 compatibility issues. `pyautogui-ng` is
> a drop-in replacement with the same API (`import pyautogui` still works).

**Geolocation:**

```
requests             # Already installed — used for direct IP geolocation API call
```

> **Note:** We use a direct `requests.get("http://ip-api.com/json/")` call instead of the
> `geocoder` library, which has been abandoned since 2018. This is simpler and more reliable.

**Camera (Phase 7 — feed only, DeepFace deferred):**

```
opencv-python
```

**Memory (Phase 8):**

```
chromadb
sentence-transformers
```

**Scheduling (Phase 9):**

```
apscheduler
```

**Packaging (Phase 10):**

```
pyinstaller
```

**Browser Automation (Optional):**

```
playwright
```

### System Dependencies (Ubuntu 24.04)

```bash
sudo apt install -y \
    portaudio19-dev \
    libportaudio2 \
    python3-pyaudio \
    python3-tk \
    python3-dev \
    ffmpeg \
    espeak \
    libespeak-dev \
    xdotool \
    xclip \
    scrot \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libegl1
```

---

## 17. Package Compatibility & Contingency Protocol

> This section documents packages that were audited for Python 3.12 compatibility and the
> replacements chosen. It also defines the protocol for handling unexpected package issues
> during implementation.

### Audited Replacements

| Original Package | Issue | Replacement | Migration Notes |
|---|---|---|---|
| `pyautogui` | Semi-abandoned, Python 3.12 `imghdr` removal breaks it | `pyautogui-ng` | Drop-in replacement — same API, `import pyautogui` still works |
| `pyttsx3` (as primary fallback) | Poorly maintained, robotic voice on Linux | `edge-tts` (primary) + `pyttsx3` (offline last resort) | `edge-tts` is async (`await edge_tts.Communicate()`), needs `asyncio.run()` wrapper |
| `pyaudio` (as primary mic input) | Last release 2017, compilation headaches on pip | `sounddevice` (primary) + system `python3-pyaudio` (backup) | `sounddevice` has nearly identical streaming API but installs cleanly |
| `geocoder` | Abandoned since 2018, unreliable | Direct `requests.get("http://ip-api.com/json/")` | No library needed — 3 lines of code replaces entire package |

### Runtime Contingency Protocol

If a package fails at runtime during implementation:

1. **ImportError / ModuleNotFoundError** → Check if the package name differs from the import name (e.g., `pip install pyautogui-ng` but `import pyautogui`). Check virtual environment is activated.
2. **Compilation failure on pip install** → Look for a system package (`apt install python3-<name>`) or a pre-built wheel. For `sounddevice`, ensure `libportaudio2` is installed.
3. **Deprecation warning / API change** → Pin to the last known working version in `requirements_desktop.txt`. Check the package's changelog for migration guides.
4. **Package completely broken on Python 3.12+** → Search PyPI for maintained forks (naming convention: `<package>-ng`, `<package>2`, `py<package>`). If no fork exists, implement the needed functionality directly (most of our package usage is thin wrappers around OS calls).

### Version Pinning Strategy

During development, install packages without version pins to get the latest. Before packaging (Phase 10), freeze all versions:

```bash
pip freeze > requirements_desktop.txt
```

This ensures reproducible builds and protects against future breaking changes.

---

## Implementation Timeline Summary

| Phase | Description | Est. Time | Dependencies |
|---|---|---|---|
| **Phase 0** | System setup, install all packages | 1-2 hours | None |
| **Phase 1** | Restructure folders, remove Zara, set up local user | 3-4 hours | Phase 0 |
| **Phase 2** | Build PyQt6 HUD dashboard (10 widget files) | 2-3 days | Phase 1 |
| **Phase 3** | Voice pipeline (Whisper STT + audio playback) | 1.5-2 days | Phase 2 |
| **Phase 4** | Wire Gemini + tools via QThread workers | 0.5-1 day | Phases 2, 3 |
| **Phase 5** | System control tools + notes tool | 1.5-2 days | Phase 4 |
| **Phase 6** | Wake word detection (Porcupine) | 1 day | Phase 3 |
| **Phase 7** | Camera feed display (DeepFace deferred) | 1 day | Phase 4 |
| **Phase 8** | Long-term memory (ChromaDB + RAG) | 1.5-2 days | Phase 4 |
| **Phase 9** | Proactive scheduling + notifications (APScheduler) | 1-2 days | Phase 8 |
| **Phase 10** | Polish, packaging, distribution | 2-3 days | All phases |
| | **Total estimated time** | **~3-4 weeks** | |

**Critical path:** Phase 0 → 1 → 2 → 3 → 4 (these must be sequential).

**Parallelizable after Phase 4:** Phases 5, 6, 7, 8 can be developed independently.
