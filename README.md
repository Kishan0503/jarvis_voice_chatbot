<div align="center">

# 🤖 J.A.R.V.I.S.
### *Just A Rather Very Intelligent System*

**A fully local, voice-first AI desktop assistant that listens, thinks, speaks, and acts.**

---

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52?style=flat-square&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![LangGraph](https://img.shields.io/badge/Agent-LangGraph-FF6B35?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![Model](https://img.shields.io/badge/LLM-Llama%203.3%2070B-76B900?style=flat-square&logo=nvidia&logoColor=white)](https://build.nvidia.com/meta/llama-3_3-70b-instruct)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

</div>

---

## ✨ What is Jarvis?

Jarvis is a **sci-fi inspired AI voice assistant that runs entirely on your desktop**. You speak to it, it speaks back, and it can genuinely *do things* — open your apps, fetch live weather, search the web, manage your files, control your clipboard, take screenshots, and more.

No browser tab. No cloud subscription. No typing commands. Just talk.

> *"Open Chrome, check the weather in London, and save a note about my 3 PM meeting."*
> — Jarvis handles all three, simultaneously, and confirms each one out loud.

The interface is styled like Tony Stark's HUD — dark, glowing, animated — with a live waveform, a chat transcript, real-time system metrics, a notes panel, and an animated avatar that reacts to sound.

---

## 🎬 The Full Pipeline at a Glance

```
🎤  You speak                  Your microphone captures audio in real time
       ↓
📝  Speech → Text              Faster-Whisper converts your voice to text locally
       ↓
🧠  AI Agent thinks            LangGraph agent reasons: answer directly, or use tools?
       ↓
🔧  Tools run (if needed)      Weather API / Google Search / File system / App control…
       ↓
💬  Response streams back      The LLM generates text token by token
       ↓
🔊  Sentence-by-sentence TTS   Each complete sentence is spoken aloud as it arrives
       ↓
📺  UI updates live            Chat transcript, notes panel, and avatar ring all update
```

The whole loop — from your voice to Jarvis's first spoken word — takes **under 2 seconds**.

---

## 🚀 Features

### 🗣️ Natural Voice Interaction
- Talk naturally, get natural replies — no wake word required
- Responses stream in real time; Jarvis starts speaking **before the full answer is ready**
- Three-tier TTS fallback: **ElevenLabs** (premium) → **Edge TTS** (free) → **pyttsx3** (offline)
- Speech recognition runs **100% locally** via Faster Whisper — your voice never leaves your machine

### 🧠 Truly Agentic AI
- Powered by **Meta Llama 3.3 70B** — a 70-billion parameter model via NVIDIA's free API
- Built on **LangGraph** — a structured decision loop that can call multiple tools, read results, and reason across multiple steps in a single response
- Remembers the last **6 exchanges** in context so follow-up questions work naturally
- Knows *when not to use tools* — casual conversation gets a direct reply, no unnecessary API calls

### 🛠️ 18 Built-in Tools

| Category | What Jarvis Can Do |
|---|---|
| 🌤️ **Weather** | Live weather for any city worldwide |
| 🕐 **Date & Time** | Current date, time, day of the week |
| 🔍 **Web Search** | Google Search — summarised and spoken |
| 🖥️ **App Control** | Open, close, and list running applications |
| 🔊 **System** | Set volume, lock screen, get CPU/RAM/disk/battery stats |
| 📁 **Files** | Find, read, browse, inspect, and open files |
| 📋 **Clipboard** | Read and write your clipboard |
| 📸 **Screenshot** | Capture and save your screen |
| 📝 **Notes** | Save, list, and delete personal notes (persisted in local DB) |

### 🎨 Sci-Fi HUD Interface
- Frameless dark window with a glowing avatar ring that pulses while speaking
- Live audio waveform visualiser
- Real-time system health metrics (CPU, RAM, disk, battery, temperature)
- Chat transcript, notes panel, camera feed, and toast notifications
- Custom typefaces (Rajdhani, Exo2) for that HUD aesthetic

---

## 🏗️ Architecture

```
jarvis_voice_chatbot/
│
├── main.py                    # Entry point
├── config.py                  # All API keys and settings (loads from .env)
│
├── agent/                     # 🧠 The AI brain
│   ├── graph.py               # LangGraph StateGraph — the decision loop
│   ├── tools.py               # 18 LangChain @tool wrappers
│   ├── state.py               # AgentState TypedDict (messages + tools_used)
│   ├── sentence_buffer.py     # Splits streaming tokens into complete sentences
│   └── __init__.py
│
├── voice/                     # 🎤 Voice pipeline
│   ├── orchestrator.py        # Coordinates STT → Agent → TTS → Playback
│   ├── stt.py                 # Speech-to-text (Faster Whisper)
│   ├── tts.py                 # Text-to-speech (ElevenLabs / Edge TTS / pyttsx3)
│   └── audio_player.py        # Queue-based audio player (Pygame)
│
├── ui/                        # 🖥️ Desktop interface (PyQt6)
│   ├── app.py                 # Top-level app controller + AgentWorker thread
│   ├── main_window.py         # Main HUD window
│   ├── hud_frame.py           # Avatar + waveform
│   ├── notes_panel.py         # Live notes sidebar
│   ├── system_metrics.py      # CPU/RAM/disk/battery widgets
│   └── ...                    # Other UI components
│
├── tools/                     # 🔧 Tool implementations
│   ├── weather.py             # OpenWeatherMap API
│   ├── search.py              # Google Custom Search API
│   ├── system_control.py      # Open/close apps, volume, lock screen
│   ├── file_ops.py            # File system operations
│   ├── clipboard.py           # Clipboard read/write
│   ├── screen.py              # Screenshot capture
│   ├── notes.py               # SQLite-backed note storage
│   └── calendar.py            # Date & time
│
└── docs/
    ├── PROJECT_OVERVIEW.md    # Non-technical project summary + example use case
    └── specs/                 # Architecture design documents
```

---

## ⚡ Quick Start

### 1. Prerequisites

- Python 3.12+
- Linux desktop (Ubuntu / Fedora / Arch — tested on Ubuntu 24.04)
- A microphone and speakers

### 2. Clone and set up

```bash
git clone https://github.com/yourusername/jarvis_voice_chatbot.git
cd jarvis_voice_chatbot

python3.12 -m venv venv_desktop
source venv_desktop/bin/activate

pip install -r requirements_desktop.txt
```

### 3. Configure API keys

Create a `.env` file in the project root:

```env
# Required
NVIDIA_API_KEY=nvapi-your-key-here
OPENWEATHER_API_KEY=your-openweather-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# Optional (enables Google Search)
GOOGLE_CSE_API_KEY=your-google-cse-key
GOOGLE_CSE_CX=your-search-engine-cx-id
```

| Key | Where to get it | Required? |
|---|---|---|
| `NVIDIA_API_KEY` | [build.nvidia.com](https://build.nvidia.com) — free tier available | ✅ Yes |
| `OPENWEATHER_API_KEY` | [openweathermap.org](https://openweathermap.org/api) — free tier | ✅ Yes |
| `ELEVENLABS_API_KEY` | [elevenlabs.io](https://elevenlabs.io) — free tier | ✅ Yes |
| `GOOGLE_CSE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com) | Optional |
| `GOOGLE_CSE_CX` | [programmablesearchengine.google.com](https://programmablesearchengine.google.com) | Optional |

### 4. Launch

```bash
source venv_desktop/bin/activate
python main.py
```

On first launch, a setup wizard will ask for your name, city, and preferred temperature unit. After that, the main window opens and Jarvis is ready to go.

---

## 🎮 Controls

| Action | How |
|---|---|
| Start speaking | Click the **microphone button** in the bottom bar |
| Stop speaking | Click again, or just pause — Jarvis detects silence |
| Type a message | Use the **input bar** at the bottom and press Enter |
| Stop Jarvis mid-response | Press `Ctrl + Shift + J` |
| Open settings | Click the **gear icon** in the toolbar |
| Minimise to tray | Click the **power button** (bottom right) |

---

## 🧩 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.12 |
| **Desktop UI** | PyQt6 6.10 |
| **AI Model** | Meta Llama 3.3 70B (via NVIDIA NIM) |
| **Agent Framework** | LangGraph 1.2 + LangChain 1.3 |
| **LLM Client** | LangChain-OpenAI (OpenAI-compatible) |
| **Speech to Text** | Faster Whisper 1.2 (runs locally) |
| **Text to Speech** | ElevenLabs 2.3 → Edge TTS 7.2 → pyttsx3 2.99 |
| **Audio Capture** | SoundDevice |
| **Audio Playback** | Pygame 2.6 |
| **Weather** | OpenWeatherMap API |
| **Web Search** | Google Custom Search API |
| **Notes Storage** | SQLite (local, `~/.jarvis/jarvis.db`) |
| **System Info** | psutil |
| **Screenshots** | mss |

---

## 💡 Example Conversation

```
You:     "Hey Jarvis, what's the weather in New York?"

Jarvis:  "It's currently 18 degrees Celsius in New York — partly cloudy
          with a light breeze. Quite pleasant for a walk, Sir."

You:     "Open Spotify and Chrome."

Jarvis:  "Done — Spotify and Chrome are both open."

You:     "Search for the latest news on the iPhone 17."

Jarvis:  "According to recent reports, Apple announced the iPhone 17 series
          with a thinner design and a new camera bar layout. Pre-orders are
          expected to open in mid-September."

You:     "Save a note — buy a new charger cable."

Jarvis:  "Noted, Sir. I've saved that for you."

You:     "How's my system doing?"

Jarvis:  "CPU is at 31%, RAM is 5.8 GB of 16, disk is 44% full,
          and battery is at 82% and charging. All looking good."

You:     "Close Chrome and lock the screen."

Jarvis:  "Chrome closed. Locking your screen now. Have a good one, Sir."
```

---

## 📚 Documentation

- **[Project Overview](docs/PROJECT_OVERVIEW.md)** — Full non-technical summary, how it works end-to-end, and a detailed example use case
- **[LangGraph Backend Design](docs/specs/2026-05-14-langgraph-agent-backend-design.md)** — Architecture spec: StateGraph design, data flow, and key decisions

---

## 🗺️ Roadmap

- [ ] Wake-word detection ("Hey Jarvis") using Picovoice Porcupine
- [ ] MCP (Model Context Protocol) tool integration
- [ ] Multi-modal support (vision — describe what's on screen)
- [ ] Home automation integration (smart lights, thermostat)
- [ ] Calendar integration (read and write Google Calendar events)
- [ ] Long-term memory (remember facts across sessions)
- [ ] Custom persona and voice configuration via settings

---

## 🤝 Contributing

Pull requests and issues are welcome. If you add a new tool, make sure to:

1. Implement it in `tools/your_tool.py`
2. Wrap it with `@tool` in `agent/tools.py`
3. Add it to the `ALL_TOOLS` list in `agent/tools.py`

The AI will automatically learn to use it from the function name, type annotations, and docstring — no other changes needed.

---

<div align="center">

Built with Python, powered by Llama 3.3 70B, and a lot of ☕

</div>
