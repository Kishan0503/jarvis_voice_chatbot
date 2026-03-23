import numpy as np
import queue
import tempfile
import os
from PyQt6.QtCore import QThread, pyqtSignal

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION_MS = 100
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)

VAD_THRESHOLD = 0.02
SILENCE_TIMEOUT_CHUNKS = int(2000 / CHUNK_DURATION_MS)
MIN_SPEECH_CHUNKS = int(400 / CHUNK_DURATION_MS)


class STTWorker(QThread):
    """
    Captures audio from microphone using sounddevice, detects speech via
    simple RMS-based VAD, and transcribes with faster-whisper.

    Signals:
        transcription_ready(str): Final transcribed text
        amplitude_changed(float): Real-time mic amplitude (0.0-1.0)
        listening_started(): Mic stream opened
        listening_stopped(): Mic stream closed
        error_occurred(str): Error message
    """
    transcription_ready = pyqtSignal(str)
    amplitude_changed = pyqtSignal(float)
    listening_started = pyqtSignal()
    listening_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, model_size: str = "small", parent=None):
        super().__init__(parent)
        self._model_size = model_size
        self._running = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._whisper_model = None

    def run(self):
        try:
            import sounddevice as sd
            self._load_model()
            self._running = True
            self.listening_started.emit()

            def audio_callback(indata, frames, time_info, status):
                if self._running:
                    self._audio_queue.put(indata.copy())

            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=CHUNK_SAMPLES,
                callback=audio_callback,
            ):
                self._process_audio_loop()

        except Exception as e:
            self.error_occurred.emit(f"STT error: {e}")
        finally:
            self._running = False
            self.amplitude_changed.emit(0.0)
            self.listening_stopped.emit()

    def stop(self):
        self._running = False

    def _load_model(self):
        if self._whisper_model is None:
            from faster_whisper import WhisperModel
            self._whisper_model = WhisperModel(
                self._model_size,
                device="cpu",
                compute_type="int8",
            )

    def _process_audio_loop(self):
        speech_buffer: list[np.ndarray] = []
        silence_count = 0
        is_speaking = False

        while self._running:
            try:
                chunk = self._audio_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            rms = float(np.sqrt(np.mean(chunk ** 2)))
            normalized_amp = min(1.0, rms / 0.05)
            self.amplitude_changed.emit(normalized_amp)

            if rms > VAD_THRESHOLD:
                if not is_speaking:
                    is_speaking = True
                    silence_count = 0
                speech_buffer.append(chunk)
                silence_count = 0
            elif is_speaking:
                speech_buffer.append(chunk)
                silence_count += 1

                if silence_count >= SILENCE_TIMEOUT_CHUNKS:
                    if len(speech_buffer) >= MIN_SPEECH_CHUNKS and self._running:
                        self._transcribe(speech_buffer)
                        self._running = False
                        return
                    speech_buffer = []
                    is_speaking = False
                    silence_count = 0

    def _transcribe(self, chunks: list[np.ndarray]):
        if not self._running:
            return

        audio = np.concatenate(chunks, axis=0).flatten()

        fd, filepath = tempfile.mkstemp(suffix=".wav", prefix="jarvis_stt_")
        os.close(fd)

        try:
            import soundfile as sf
            sf.write(filepath, audio, SAMPLE_RATE)
        except ImportError:
            self._write_wav_manual(filepath, audio)

        try:
            segments, info = self._whisper_model.transcribe(
                filepath,
                language="en",
                beam_size=5,
                best_of=5,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            if text:
                self.transcription_ready.emit(text)
        except Exception as e:
            self.error_occurred.emit(f"Transcription error: {e}")
        finally:
            try:
                os.unlink(filepath)
            except OSError:
                pass

    @staticmethod
    def _write_wav_manual(filepath: str, audio: np.ndarray):
        """Write WAV without soundfile dependency."""
        import struct
        import wave

        pcm = (audio * 32767).astype(np.int16)
        with wave.open(filepath, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(pcm.tobytes())
