# Gemini API Key Rotation — Implementation Plan

## Problem

The free tier of Google Gemini API has strict daily rate limits (e.g., 20 requests/day for `gemini-2.5-flash`). When the quota is exhausted, Jarvis becomes completely non-functional until the next day. This is unacceptable for a daily-use AI assistant.

## Solution

Implement an automatic API key rotation system that cycles through multiple Gemini API keys from different Google accounts. When one key hits its rate limit (HTTP 429), the system seamlessly switches to the next available key — invisible to the user.

## Architecture

```
User message
  → GeminiClient.send_message_to_gemini()
    → Try Key 1 → Success → return response
    → 429 Error → mark Key 1 as exhausted (with cooldown timestamp)
      → Try Key 2 → Success → return response
      → 429 Error → mark Key 2 as exhausted
        → Try Key 3 → Success → return response
        → All keys exhausted → return "All API keys exhausted, please try later"
```

On the next request, keys are tried starting from the last successful one (not from the beginning), to avoid wasting time on known-exhausted keys. Exhausted keys are retried after their cooldown period expires.

## Files to Change

### 1. `.env` — Store multiple API keys

**Current:**

```
GEMINI_API_KEY = AIzaSyCkb0Q-xxxxxxxxxxxxxxxxxxxx
```

**New format:**

```
GEMINI_API_KEYS = AIzaSyCkb0Q-key1xxx,AIzaSyBxxx-key2xxx,AIzaSyCxxx-key3xxx
```

The old `GEMINI_API_KEY` (singular) is kept as a fallback for backward compatibility. If `GEMINI_API_KEYS` (plural) is not set, the system falls back to the single key.

### 2. `config.py` — Parse multiple keys

**Changes:**

- Add `GEMINI_API_KEYS` property that reads the comma-separated env var
- Parse into a Python list of strings, stripping whitespace
- Fallback: if `GEMINI_API_KEYS` is not set, use `[GEMINI_API_KEY]` (single key in a list)
- Validation: raise error if no keys are provided at all

**Code outline:**

```python
_raw_keys = os.getenv("GEMINI_API_KEYS", "")
if _raw_keys.strip():
    GEMINI_API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]
else:
    single = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_KEYS = [single] if single else []

if not GEMINI_API_KEYS:
    raise ValueError("No Gemini API keys configured. Set GEMINI_API_KEYS or GEMINI_API_KEY in .env")
```

### 3. `gemini_client.py` — Core rotation logic

This is the main change. The `GeminiClient` class needs to:

**a) Manage multiple keys with state tracking:**

```python
self._api_keys = app_config.GEMINI_API_KEYS
self._current_key_index = 0
self._key_states = {}  # {key_index: {"exhausted_at": timestamp, "cooldown_seconds": 60}}
```

**b) Create a model per key (lazy initialization):**

Each API key needs its own `genai.configure()` + `GenerativeModel` instance because the API key is set globally in `google.generativeai`. To handle this properly, we re-configure before each call with the active key.

```python
def _configure_key(self, key_index: int):
    """Switch the active API key."""
    genai.configure(api_key=self._api_keys[key_index])
    self._current_key_index = key_index
    self._session = None  # Reset session since the model config changed
```

**c) Detect 429 errors and rotate:**

In `send_message_to_gemini()`, wrap the API call in a retry loop:

```python
def send_message_to_gemini(self, user_message: str) -> str:
    for attempt in range(len(self._api_keys)):
        key_index = self._find_next_available_key()
        if key_index is None:
            return "All API keys have been rate-limited. Please try again later."

        self._configure_key(key_index)
        session = self._get_session()

        try:
            session.truncate_history()
            response = session.chat.send_message(user_message)
            # ... process response (existing logic) ...
            return final_reply

        except Exception as e:
            if "429" in str(e):
                # Parse retry delay from error if available
                cooldown = self._parse_retry_delay(e) or 60
                self._mark_key_exhausted(key_index, cooldown)
                print(f"Key {key_index + 1}/{len(self._api_keys)} rate limited. Rotating...")
                continue
            else:
                return self._error_message(str(e))

    return "All API keys have been rate-limited. Please try again later."
```

**d) Key state management methods:**

```python
def _find_next_available_key(self) -> int | None:
    """Find the next key that isn't in cooldown."""
    now = time.time()
    # Start from current key, cycle through all
    for i in range(len(self._api_keys)):
        idx = (self._current_key_index + i) % len(self._api_keys)
        state = self._key_states.get(idx)
        if state is None:
            return idx
        if now - state["exhausted_at"] > state["cooldown_seconds"]:
            del self._key_states[idx]  # Cooldown expired, key is available again
            return idx
    return None  # All keys exhausted

def _mark_key_exhausted(self, key_index: int, cooldown_seconds: int):
    """Mark a key as rate-limited with a cooldown period."""
    self._key_states[key_index] = {
        "exhausted_at": time.time(),
        "cooldown_seconds": cooldown_seconds,
    }

def _parse_retry_delay(self, error) -> int | None:
    """Extract the retry delay from a 429 error message if available."""
    import re
    match = re.search(r"retry in (\d+\.?\d*)", str(error), re.IGNORECASE)
    if match:
        return int(float(match.group(1))) + 5  # Add 5s buffer
    return None
```

### 4. `ui/app.py` — Surface key rotation info to the user (optional)

When a key rotation happens, show a toast notification:

```python
# In the orchestrator or app, when Gemini returns:
"Switched to backup API key (2/3)"
```

This is optional but helpful for the user to know what's happening.

## Step-by-Step Implementation Order

### Step 1: Update `.env`

Add multiple API keys in comma-separated format:

```
GEMINI_API_KEYS = key1_from_account1,key2_from_account2,key3_from_account3
```

### Step 2: Update `config.py`

- Add `GEMINI_API_KEYS` list parsing
- Keep backward compatibility with single `GEMINI_API_KEY`
- Update validation

### Step 3: Rewrite key management in `gemini_client.py`

- Add `_api_keys` list, `_current_key_index`, `_key_states` dict
- Add `_configure_key()`, `_find_next_available_key()`, `_mark_key_exhausted()`, `_parse_retry_delay()`
- Wrap `send_message_to_gemini()` in a rotation retry loop
- Reset session on key switch (since `genai.configure()` is global)

### Step 4: Test

- Test with a single key (backward compatibility)
- Test with multiple keys where the first is intentionally rate-limited
- Verify rotation happens seamlessly and conversation continues

### Step 5: (Optional) Add UI notification for key rotation

- Toast notification when a key switch occurs
- Show active key number in session stats or notifications panel

## Edge Cases to Handle

| Scenario | Behavior |
|---|---|
| Only 1 key configured (old `.env` format) | Works exactly as before — no rotation, single key |
| All keys exhausted | Return friendly message: "All API keys are rate-limited. Please try later." |
| Key 1 exhausted, Key 2 works | Seamless switch, user sees no interruption |
| Key 1 cooldown expires during use | Next request retries Key 1 automatically |
| Invalid key in the list | Treated as a non-429 error, skipped permanently for that session |
| Internet goes down | Existing error handling applies (not a 429, no rotation) |

## Future Enhancement: Ollama Local Fallback

After all API keys are exhausted, a future enhancement can add a local Ollama fallback:

```
All Gemini keys exhausted
  → Try local Ollama (http://localhost:11434/api/chat)
  → If Ollama not running → show "All options exhausted" message
```

This would be a separate implementation that builds on top of the key rotation system.
