"""Lyrics transcription using Whisper."""

import whisper


def transcribe_vocals(vocals_path: str, model_name: str = "large-v3") -> dict:
    """Transcribe a vocals audio file and return Whisper result with segments."""
    model = whisper.load_model(model_name)
    result = model.transcribe(
        str(vocals_path),
        language="en",
        word_timestamps=True,
    )
    return result
