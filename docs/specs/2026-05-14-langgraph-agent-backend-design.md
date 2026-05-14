# LangGraph Agent Backend — Design Specification

**Date:** 2026-05-14  
**Status:** Approved  
**Approach:** B — Custom LangGraph StateGraph + Streaming TTS  
**Model:** `meta/llama-3.3-70b-instruct` via NVIDIA NIM (free tier)  
**Replaces:** `openai_client.py` (manual `while tool_calls` loop)

---

## 1. Problem Statement

The current backend (`openai_client.py`) manually implements an agent loop using a `while message.tool_calls` pattern. This works for simple cases but has several limitations:

- **Sequential tool execution** — tools are called one by one even when independent
- **No streaming** — Jarvis waits for the entire response before speaking, adding unnecessary latency
- **Black-box loop** — no visibility into what the model reasoned, which tools it selected, or why
- **No state machine** — the agent has no formal states; adding new capabilities (memory, multi-agent, checkpointing) requires major rewrites
- **Small model** — `llama-3.1-8b-instruct` struggles with structured agent reasoning prompts

---

## 2. Solution Overview

Replace `openai_client.py` with a proper **LangGraph StateGraph** agent backend. Introduce a **streaming TTS pipeline** that plays sentence-by-sentence audio instead of waiting for a full response.

The rest of the application — voice capture (STT), UI, system tray, notes panel, audio player — remains completely unchanged in behaviour.

---

## 3. Architecture

### 3.1 High-Level Component Map

```
┌─────────────────────────────────────────────────────────────────┐
│                        Jarvis Desktop App                       │
│                                                                 │
│  ┌──────────┐    ┌─────────────┐    ┌──────────────────────┐   │
│  │  STT     │    │ Orchestrator│    │    Main Window (UI)   │   │
│  │ (Whisper)│───▶│ (QObject)   │◀──▶│    PyQt6             │   │
│  └──────────┘    └──────┬──────┘    └──────────────────────┘   │
│                         │                                       │
│              send_to_agent(text)                                │
│                         ▼                                       │
│               ┌─────────────────┐                              │
│               │  AgentWorker    │  ← NEW (replaces GeminiWorker)│
│               │  (QThread)      │                              │
│               │  asyncio.run()  │  ← async/sync bridge         │
│               └────────┬────────┘                              │
│                        │                                        │
│              ┌─────────▼──────────┐                            │
│              │   LangGraph Graph  │  ← NEW (agent/graph.py)    │
│              │                    │                            │
│              │  ┌──────────────┐  │                            │
│              │  │ model_node   │  │  LLM reasons, picks tools  │
│              │  └──────┬───────┘  │                            │
│              │         │          │                            │
│              │  ┌──────▼───────┐  │                            │
│              │  │  tools_node  │  │  Parallel tool execution   │
│              │  └──────┬───────┘  │                            │
│              │         │          │                            │
│              │  (loops back to model_node until done)          │
│              └─────────┬──────────┘                            │
│                        │                                        │
│              token stream (astream_events)                      │
│                        │                                        │
│              ┌─────────▼──────────┐                            │
│              │  SentenceBuffer    │  ← NEW (inside AgentWorker) │
│              │  splits on . ? !   │                            │
│              └─────────┬──────────┘                            │
│                        │                                        │
│               sentence_ready(str) signal                        │
│                        │                                        │
│              ┌─────────▼──────────┐                            │
│              │    TTSWorker       │  ← MODIFIED                │
│              │ (one per sentence) │                            │
│              └─────────┬──────────┘                            │
│                        │                                        │
│              ┌─────────▼──────────┐                            │
│              │   AudioPlayer      │  ← MODIFIED                │
│              │   (queue-based)    │  plays chunks sequentially  │
│              └────────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 LangGraph StateGraph

The agent is a **cyclic graph** with two nodes and conditional routing:

```
        ┌─────────────────────────────┐
        │         START               │
        └──────────────┬──────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │         model_node           │
        │  - Receives: messages list   │
        │  - Calls: LLM (70B)         │
        │  - Returns: AI message with  │
        │    optional tool_calls       │
        └──────────────┬───────────────┘
                       │
            ┌──────────▼──────────┐
            │  has tool_calls?    │
            └──┬──────────────────┘
               │                 │
              YES                NO
               │                 │
               ▼                 ▼
  ┌────────────────────┐       END
  │    tools_node      │
  │  - ToolNode runs   │
  │    all tool calls  │
  │    IN PARALLEL     │
  │  - Returns tool    │
  │    result messages │
  └────────┬───────────┘
           │
           └──────────▶ (back to model_node)
```

**Key insight:** The graph loops automatically. The LLM may call tools multiple times (e.g., search for something, then use the result to call another tool) before producing a final text response. Each loop iteration is a full round-trip to the 70B model.

### 3.3 Agent State

```python
# agent/state.py
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]   # full conversation history
    tools_used: list[str]                      # accumulated tool names for UI
```

`add_messages` is a LangGraph reducer — it merges new messages into the list correctly (handles tool call / tool result pairing automatically).

### 3.4 Streaming Pipeline

```
LangGraph astream_events()
    │
    ├── on_chat_model_stream event
    │        └── chunk.content (token string)
    │                │
    │                ▼
    │        SentenceBuffer.feed(token)
    │                │
    │       ┌────────▼────────┐
    │       │ buffer += token │
    │       │ if ends in .?!  │──▶ emit sentence_ready("Hello sir.")
    │       └─────────────────┘
    │
    ├── on_tool_start event  ──▶ emit tool_started("get_current_weather")
    │
    └── on_chain_end event   ──▶ emit reply_complete(full_text, tools_used)
```

**Sentence boundary detection:** A sentence is considered complete when the buffer ends with `.`, `?`, or `!` followed by a space or end-of-stream. Short fragments (< 3 words) are held and merged with the next sentence to avoid generating very short audio clips.

### 3.5 Async / Sync Bridge

LangGraph is async-native. PyQt6 QThreads are synchronous. The bridge is simple and clean:

```python
class AgentWorker(QThread):
    sentence_ready = pyqtSignal(str)
    reply_complete = pyqtSignal(str, list)

    def run(self):
        asyncio.run(self._stream())          # blocks the QThread

    async def _stream(self):
        async for event in graph.astream_events(input, config):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].content
                sentence = self._buffer.feed(token)
                if sentence:
                    self.sentence_ready.emit(sentence)   # Qt signal, thread-safe
        self.reply_complete.emit(full_text, tools_used)
```

Qt signals emitted from non-main threads are automatically queued and processed safely by Qt's event loop. No `qasync` or `threading.Lock` needed.

### 3.6 Queue-Based Audio Playback

```
sentence_ready("Hello sir.")
        │
        ▼
  TTSWorker(sentence)   ← generates MP3 asynchronously in a QThread
        │
        ▼
  audio_queue.put(filepath)
        │
        ▼
  AudioPlayer (persistent QThread)
    while True:
        filepath = audio_queue.get()  ← blocks until next file available
        pygame.mixer.music.play(filepath)
        wait until done
        # next sentence starts automatically
```

The AudioPlayer becomes a persistent daemon thread that lives for the whole app session, consuming from a `queue.Queue`.

---

## 4. File Structure

### New Files

| File | Responsibility |
|------|---------------|
| `agent/__init__.py` | Package marker, exports `agent_graph`, `AgentWorker` |
| `agent/state.py` | `AgentState` TypedDict — the single source of truth |
| `agent/tools.py` | All 18 tools wrapped as LangChain `@tool` functions — imports from existing `tools/` modules, no logic changes |
| `agent/graph.py` | `build_graph()` — constructs the StateGraph, compiles it with a checkpointer, exports the compiled graph |
| `agent/sentence_buffer.py` | `SentenceBuffer` — stateful token accumulator, emits complete sentences |

### Modified Files

| File | Change |
|------|--------|
| `ui/app.py` | Replace `GeminiWorker` with `AgentWorker`; connect `sentence_ready` and `reply_complete` signals |
| `voice/orchestrator.py` | Replace `on_gemini_response(full_reply)` with `on_sentence_ready(sentence)` handler |
| `voice/tts.py` | `TTSWorker` already handles single strings — minor: remove full-paragraph pre-processing if any |
| `voice/audio_player.py` | Replace single-file play with queue-based persistent player |
| `requirements_desktop.txt` | Add `langgraph`, `langchain`, `langchain-openai` |

### Unchanged Files (0 modifications)

`main.py`, `config.py`, `voice/stt.py`, `ui/main_window.py`, `ui/styles.py`, `ui/notes_panel.py`, `ui/notifications_panel.py`, `ui/session_stats.py`, `ui/settings_panel.py`, `ui/setup_wizard.py`, `ui/system_tray.py`, `ui/camera_widget.py`, `ui/hud_frame.py`, `ui/transcript_widget.py`, `ui/waveform_widget.py`, `ui/system_metrics.py`, `auth/local_user.py`, `tools/weather.py`, `tools/calendar.py`, `tools/search.py`, `tools/system_control.py`, `tools/file_ops.py`, `tools/clipboard.py`, `tools/screen.py`, `tools/notes.py`, `tools/elevenlabs_tts.py`

---

## 5. Data Flow — End to End

### 5.1 Voice Input Path

```
1. User speaks
2. STTWorker (faster-whisper) → transcribes → emits transcription_ready("what's the weather in Mumbai?")
3. Orchestrator._on_transcription() → emits send_to_agent("what's the weather in Mumbai?")
4. JarvisApp._call_agent() → creates AgentWorker(message) → starts QThread
5. AgentWorker.run() → asyncio.run(_stream())
6. _stream() → graph.astream_events({"messages": [HumanMessage(text)]}, config)
7. LangGraph model_node → LLM decides to call get_current_weather("Mumbai", "celsius")
8. LangGraph tools_node → executes get_current_weather → {"temperature": "32°C", ...}
9. LangGraph model_node → LLM generates: "It's currently 32 degrees Celsius in Mumbai, Sir. Quite warm — you might want to carry water."
10. Tokens stream in:
    - "It's currently 32 degrees Celsius in Mumbai, Sir." → SentenceBuffer → sentence_ready signal
    - " Quite warm — you might want to carry water." → SentenceBuffer → sentence_ready signal
11. Each sentence → TTSWorker → ElevenLabs API → MP3 file → AudioPlayer queue
12. AudioPlayer plays sentence 1 (🔊 "It's currently 32 degrees...") while sentence 2 TTS is still generating
13. AgentWorker emits reply_complete(full_text, ["get_current_weather"])
14. UI: transcript updated, notes panel refreshed if notes tools used
```

### 5.2 Text Input Path

Same as above from step 3 onwards. Steps 1-2 are skipped; user message comes from the text input bar directly.

### 5.3 Tool Execution Path (Parallel Example)

User: "What's the weather and what's my CPU usage?"

```
model_node → tool_calls: [
    {"name": "get_current_weather", "args": {"location": "Mumbai"}},
    {"name": "get_system_info", "args": {}}
]
tools_node → runs BOTH simultaneously via asyncio.gather()
→ results returned together → model_node generates unified response
```

---

## 6. Technology Stack

| Component | Library | Version | Purpose |
|-----------|---------|---------|---------|
| Agent framework | `langgraph` | ≥ 0.2 | StateGraph, ToolNode, astream_events |
| LLM integration | `langchain-openai` | ≥ 0.2 | `ChatOpenAI` with NVIDIA base_url |
| Tool decorators | `langchain-core` | ≥ 0.3 | `@tool` decorator, `ToolMessage` |
| LLM model | `meta/llama-3.3-70b-instruct` | — | NVIDIA NIM free tier |
| UI framework | `PyQt6` | 6.10+ | Desktop window, signals/slots |
| STT | `faster-whisper` | — | Unchanged |
| TTS | ElevenLabs → Edge TTS → pyttsx3 | — | Unchanged (3-tier fallback) |
| Audio | `pygame.mixer` | — | Modified for queue-based playback |

---

## 7. Key Design Decisions & Rationale

### Why Custom StateGraph over `create_react_agent`?

`create_react_agent` is a convenience wrapper that calls `StateGraph` internally. Using it means the graph is a black box — adding custom nodes (memory retrieval, multi-agent routing, safety checks) later requires discarding it entirely. Building the graph explicitly takes ~20 extra lines but gives full structural control for the lifetime of the project.

### Why `asyncio.run()` in QThread over `qasync`?

`qasync` integrates the asyncio event loop into Qt's event loop. This is powerful but fragile — signals, timers, and loops can interact unexpectedly. `asyncio.run()` inside a QThread is simpler: the async code runs in its own isolated event loop within the thread, emitting Qt signals (which are thread-safe) to communicate results. No shared state, no loop conflicts.

### Why Sentence-Level TTS over Full-Response TTS?

Full-response TTS: user waits ~3-5 seconds (LLM generation + TTS synthesis) before hearing anything.
Sentence-level TTS: user hears the first sentence ~1-2 seconds after asking (LLM generates first sentence → immediately synthesised while LLM continues generating). For a voice assistant, this latency reduction is significant for perceived responsiveness.

### Why 70B over 8B?

LangGraph's ReAct pattern requires the model to output structured reasoning (`Thought → Action → Observation`) and correctly format tool call arguments as JSON. Smaller models frequently hallucinate tool names, produce malformed JSON arguments, or skip reasoning steps. `llama-3.3-70b-instruct` reliably follows this format.

---

## 8. What This Unlocks (Future Capabilities)

With this architecture in place, the following can be added without structural changes:

| Capability | How |
|-----------|-----|
| **Persistent memory across sessions** | Add `SqliteSaver` checkpointer to the graph |
| **Multi-agent routing** | Add a supervisor node that delegates to specialised sub-graphs |
| **LangSmith observability** | Set `LANGCHAIN_API_KEY` env var — zero code changes |
| **MCP tool servers** | Swap `agent/tools.py` entries for MCP client connections |
| **Wake word ("Hey Jarvis")** | Add Picovoice hotword detection before STT in Orchestrator |
| **Web search with citations** | Upgrade `google_search` tool to return structured `SearchResult` with URLs |
| **Proactive notifications** | Add a scheduler node to the graph that fires on a timer |

---

## 9. Out of Scope (This Implementation)

- LangSmith tracing (can be enabled later with 2 env variables)
- Multi-agent architecture (requires multiple specialised graphs)
- MCP tool servers (local tools don't benefit enough to justify the complexity now)
- Wake word detection (Picovoice integration is separate from agent backend)
- Web UI / API server (desktop-only for now)
