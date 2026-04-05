"""Lyrics transcription using Whisper."""

import time
import urllib.error

import whisper

MAX_RETRIES = 3
RETRY_DELAY = 5


def _load_model_with_retry(model_name: str) -> whisper.Whisper:
    """Load a Whisper model, retrying on network failures."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return whisper.load_model(model_name)
        except (urllib.error.URLError, ConnectionError, OSError) as e:
            if attempt == MAX_RETRIES:
                raise
            print(f"  Model download failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            print(f"  Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)


def transcribe_vocals(vocals_path: str, model_name: str = "large-v3") -> dict:
    """Transcribe a vocals audio file and return Whisper result with segments."""
    model = _load_model_with_retry(model_name)
    result = model.transcribe(
        str(vocals_path),
        language="en",
        word_timestamps=True,
        verbose=False,
    )
    return result
