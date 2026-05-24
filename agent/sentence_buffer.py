import re


class SentenceBuffer:
    """
    Stateful token accumulator that splits a streaming text into speakable
    sentences for immediate TTS dispatch.

    Design rules
    ------------
    - A sentence boundary is a '.', '?', or '!' optionally followed by a
      closing quote/bracket, then whitespace (or end-of-stream on flush).
    - Fragments shorter than MIN_WORDS words are held and merged with the
      next sentence to avoid very short audio clips (e.g. "Sir." alone).
    - `feed(token)` returns a complete sentence string when one is ready,
      otherwise returns None.
    - `flush()` returns whatever remains in the buffer when the stream ends.
    """

    MIN_WORDS = 3
    # Matches end of sentence: punctuation + optional close-quote + whitespace
    _BOUNDARY = re.compile(r'[.!?]["\']?\s')

    def __init__(self):
        self._buf = ""

    def feed(self, token: str) -> str | None:
        """
        Append token to internal buffer.
        Returns a complete sentence if one is now available, else None.
        """
        self._buf += token
        match = self._BOUNDARY.search(self._buf)
        if match:
            end = match.end()
            candidate = self._buf[:end].strip()
            self._buf = self._buf[end:]
            if len(candidate.split()) >= self.MIN_WORDS:
                return candidate
            # Too short — prepend back so it merges with next sentence
            self._buf = candidate + " " + self._buf
        return None

    def flush(self) -> str | None:
        """
        Called when the token stream ends.
        Returns any remaining text in the buffer, or None if empty.
        """
        remainder = self._buf.strip()
        self._buf = ""
        return remainder if remainder else None

    def reset(self):
        """Clear the buffer for a new conversation turn."""
        self._buf = ""
