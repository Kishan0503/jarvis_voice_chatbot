# Jarvis — AI Voice Assistant Desktop App
### Project Overview & User Guide

---

## What Is Jarvis?

Jarvis is a **personal AI assistant that lives on your desktop** and works exactly like a real assistant — you talk to it, it talks back, and it can actually do things on your computer for you.

Think of it like having Tony Stark's Jarvis from Iron Man, but running on your own machine. You can ask it questions, give it tasks, and have natural back-and-forth conversations. It understands your voice, speaks back with a natural British-accented voice, remembers what you said earlier in the conversation, and can take real actions like opening apps, checking the weather, searching the internet, managing your files, and more.

It looks the part too — the interface is styled like a futuristic sci-fi HUD with a glowing animated avatar, live system stats, a chat log, and a notes panel, all in a sleek dark blue theme.

---

## What Can Jarvis Do?

### Talk and Listen
- You can either **speak to Jarvis using your microphone** or **type a message** in the input bar at the bottom.
- Jarvis listens, understands what you said, and replies in a natural, conversational tone.
- Responses are spoken out loud — and importantly, Jarvis **starts speaking the first sentence almost immediately** while the rest of the response is still being generated. You don't have to wait for the full answer before you hear anything.

### Answer Questions
- Ask anything — current events, general knowledge, how-to questions, definitions, recommendations.
- For topics it's not certain about, it searches Google and summarises the results for you.
- For simple conversation and questions it already knows, it replies directly without searching.

### Check Weather
- Ask "What's the weather in Mumbai?" or "Is it cold in London today?" and it fetches live, real-time weather data and tells you the temperature and conditions.

### Tell You the Date and Time
- Ask "What day is it?" or "What time is it?" and it reads you the exact current date and time.

### Control Your Computer
- **Open apps** — "Open Firefox", "Open Terminal", "Open VS Code"
- **Close apps** — "Close Chrome", "Close Spotify"
- **See what's running** — "What apps are currently open?"
- **Set volume** — "Set volume to 60"
- **Lock the screen** — "Lock my screen"

### Manage Your Files
- **Find files** — "Find all PDF files in my Downloads folder"
- **Read a file** — "Read the contents of my notes.txt"
- **Browse folders** — "What's in my Desktop folder?"
- **Open a file** — "Open my resume"

### Clipboard
- **Read clipboard** — "What's on my clipboard?"
- **Write to clipboard** — "Copy this text to my clipboard: Meeting at 3pm"

### Take Screenshots
- "Take a screenshot" — captures your entire screen and saves it.

### Save and Manage Notes
- "Remember that I have a dentist appointment on Friday" — saves a note.
- "Show me my notes" — lists all saved notes, which also appear in the right panel of the UI.
- "Delete note 2" — removes a specific note.

### Check System Health
- "How's my CPU doing?" or "Check my system" — reports live CPU usage, RAM, disk space, and battery level.

---

## How It Looks

The desktop window is divided into three columns:

| Left Panel | Centre Panel | Right Panel |
|---|---|---|
| Notifications | Animated Jarvis avatar with glowing ring | Notes panel |
| Live system metrics (CPU, RAM, disk, battery, temperature) | Audio waveform visualiser | Camera feed |
| | Chat transcript | |
| | Input bar (type or speak) | |

At the top, it greets you by name, shows the current date and time, and displays your location. The avatar's glowing ring reacts to sound — it pulses while Jarvis is speaking and responds to your microphone while you're talking.

---

## How It Works (Simply Explained)

Here is the full journey from when you speak or type, to when you hear Jarvis respond:

```
You speak or type
       ↓
Your voice is transcribed into text (if you spoke)
       ↓
The text is sent to the AI brain (LangGraph Agent)
       ↓
The AI decides: should I answer directly, or do I need to use a tool?
       ↓
If a tool is needed: it runs the tool (weather API, Google search, etc.)
       ↓
The AI reads the tool result and formulates a response
       ↓
The response streams back word by word
       ↓
As each complete sentence arrives, it's immediately converted to speech
       ↓
The audio plays while the next sentence is still being prepared
       ↓
Jarvis speaks the answer and the text appears in the chat transcript
```

This pipeline means there's almost no waiting — you hear the first sentence within about a second, while Jarvis is still working on the rest.

---

## How It Was Built

### The AI Brain — LangGraph Agent

The intelligence behind Jarvis is powered by a **LangGraph StateGraph** — a structured decision-making loop that works like this:

1. The AI model reads your message and the conversation history.
2. It decides whether to answer directly or call one (or more) tools.
3. If tools are needed, they run — multiple tools can run at the same time.
4. The results come back and the AI reads them to form a reply.
5. The reply streams back sentence by sentence.

This loop can repeat multiple times in a single response — for example, Jarvis might search Google, read the result, then search again for something more specific, all before giving you a final answer.

The AI model used is **Meta's Llama 3.3 70B** (a 70-billion parameter model), hosted on NVIDIA's cloud infrastructure and accessed for free via their API. This is a significantly more capable model than smaller alternatives — it handles multi-step reasoning and tool use very reliably.

### The Voice System

**Listening (Speech-to-Text):**
Your voice is captured through the microphone in real time. A simple energy-based detector figures out when you've started and stopped speaking. Once you go silent for about 2 seconds, the recorded audio is sent to **Faster Whisper** — a fast, accurate speech-to-text model that runs locally on your machine and converts your speech to text.

**Speaking (Text-to-Speech):**
Jarvis speaks using a 3-tier system. It always tries the best option first and falls back automatically:
1. **ElevenLabs** — premium AI voice, British male ("Adam"). Requires internet.
2. **Microsoft Edge TTS** — free, natural-sounding British voice ("Ryan"). Requires internet.
3. **System voice (pyttsx3)** — completely offline fallback.

Because responses stream sentence by sentence, a new audio clip starts generating for each sentence as it arrives. This keeps the response feeling instant and natural.

### The Tools

Jarvis has 18 tools it can use. Each tool is a Python function that does one specific real-world job:

| Category | Tools |
|---|---|
| Information | Weather, date/time, Google search |
| System control | Open app, close app, list apps, set volume, lock screen |
| File management | Find files, read file, browse folder, get file info, open file |
| Clipboard | Read clipboard, write clipboard |
| Notes | Save note, list notes, delete note |
| Screen | Take screenshot |

The AI decides on its own which tools to use and what to pass to them based on what you asked. You don't need to know the tool names or how they work.

### The Desktop Interface

The window is built with **PyQt6**, a framework for building desktop apps with Python. It uses a custom dark theme inspired by sci-fi HUDs. Everything — the glowing avatar ring, the animated waveform, the live system metrics, the toast notifications — is drawn and updated in real time. The window is frameless (no standard title bar) and can be moved and resized by dragging its edges.

### Conversation Memory

Jarvis remembers the last 6 exchanges (12 messages) in the current session. This means follow-up questions work naturally — you can say "What about Delhi?" after asking about Mumbai's weather and Jarvis knows what you mean.

---

## Tech Stack

| What it does | Technology used |
|---|---|
| AI model | Meta Llama 3.3 70B (via NVIDIA NIM API) |
| Agent framework | LangGraph + LangChain |
| LLM connection | LangChain-OpenAI (OpenAI-compatible client) |
| Speech to text | Faster Whisper (runs locally, no internet needed) |
| Text to speech | ElevenLabs → Edge TTS → pyttsx3 (in that priority) |
| Audio capture | SoundDevice |
| Audio playback | Pygame |
| Desktop UI | PyQt6 |
| Weather data | OpenWeatherMap API |
| Web search | Google Custom Search API |
| Notes storage | SQLite (local database at `~/.jarvis/jarvis.db`) |
| User settings | JSON file at `~/.jarvis/user_config.json` |
| Programming language | Python 3.12 |

---

## How to Run It

```bash
# Make sure you're in the project folder with the virtual environment active
cd jarvis_voice_chatbot
source venv_desktop/bin/activate

# Start Jarvis
python main.py
```

On first launch, a setup wizard will ask for your name, city, and preferred temperature unit. After that, the main window opens and Jarvis is ready.

- **Click the microphone button** (bottom bar) to start speaking. Click it again or wait for silence to finish.
- **Type in the input bar** and press Enter or click Send.
- **Press Ctrl+Shift+J** at any time to immediately stop whatever Jarvis is doing.
- **Click the power button** (bottom right) to minimise to the system tray or quit.

---

## Detailed Example Use Case

### Scenario: A Morning Productivity Session with Jarvis

---

**You sit down at your desk at 9:00 AM. You open Jarvis.**

The window opens. The top bar reads: *"Good morning — Friday, May 15, 2026 — 9:00:12 AM"*. The avatar glows gently.

---

**Step 1 — A casual greeting**

> You (speaking): *"Hey Jarvis, good morning."*

Jarvis hears you, transcribes your voice, and responds directly without using any tools:

> Jarvis (speaking): *"Good morning, Sir! Lovely to have you up and about. What can I do for you today?"*

You see the exchange appear in the Chat Transcript. The glow ring pulses while Jarvis speaks.

---

**Step 2 — Check the weather before heading out**

> You: *"What's the weather like in Ahmedabad today?"*

Behind the scenes: Jarvis calls the weather tool with location "Ahmedabad". The tool fetches live data from OpenWeatherMap in under a second and returns the temperature and conditions.

> Jarvis: *"It's currently 38 degrees Celsius in Ahmedabad — sunny with a light breeze. Quite warm, Sir. You might want to carry water if you're heading out."*

---

**Step 3 — Open your work apps**

> You: *"Open VS Code and also open Chrome."*

Jarvis launches both apps simultaneously.

> Jarvis: *"Done, Sir — VS Code and Chrome are both open."*

---

**Step 4 — Search for something while you work**

> You: *"What's the latest news on the India vs England cricket match?"*

Jarvis searches Google, gets the top results back, and summarises them.

> Jarvis: *"According to recent reports, India won the third Test match by 7 wickets in Edgbaston. Virat Kohli scored a century. The series now stands at 2-1 in India's favour."*

---

**Step 5 — Make a note about something important**

> You: *"Remember that I have a team meeting at 3 PM today."*

Jarvis saves a note to the local database. It immediately appears in the Notes panel on the right side of the screen.

> Jarvis: *"Noted, Sir. I've saved that — team meeting at 3 PM today."*

---

**Step 6 — Find a file**

> You: *"Find the project report PDF I worked on last month."*

Jarvis searches your home directory for PDF files.

> Jarvis: *"I found 3 PDF files. The most likely one is 'Project_Report_April_2026.pdf' in your Documents folder."*

> You: *"Open it."*

Jarvis opens the PDF in your system's default viewer.

> Jarvis: *"Opening it now, Sir."*

---

**Step 7 — Check system health mid-day**

> You: *"How's the system doing?"*

Jarvis reads live hardware stats and reports them.

> Jarvis: *"CPU is at 24%, RAM usage is 6.2 GB out of 16, disk is 43% full, and your battery is at 71% and currently charging. All looking healthy, Sir."*

---

**Step 8 — End of session — close apps and lock up**

> You: *"Close Chrome and lock the screen."*

Jarvis closes Chrome and locks the screen.

> Jarvis: *"Chrome closed. Locking your screen now, Sir. Have a good one."*

The screen locks. Jarvis is still running in the system tray, ready when you unlock.

---

**What this example shows:**

In one morning session, Jarvis handled:
- Casual conversation (no tools, instant reply)
- Live weather data (external API)
- Launching two apps simultaneously (system control)
- Real-time web search (Google API)
- Saving a note that appeared live in the UI (local database)
- File search and opening (file system access)
- System health report (live hardware stats)
- Closing an app and locking the screen (system control)

All of this happened through natural speech — no clicking through menus, no typing commands, no switching between apps to find information. Just talking.

---

## What Makes This Project Stand Out

- **It's truly local-first** — speech recognition runs on your machine. Your voice never leaves your computer.
- **It's fast** — streaming TTS means you hear the first sentence almost instantly, not after the full response is generated.
- **It's a real agent** — Jarvis doesn't just answer questions. It takes actions. It can use multiple tools in a single response and chain them together.
- **It's honest** — if it doesn't know something, it searches Google rather than making something up.
- **It's extensible** — adding a new tool is as simple as writing one Python function. The AI automatically learns to use it from the function name and description.
- **It remembers context** — follow-up questions in the same session work naturally, just like talking to a real person.
