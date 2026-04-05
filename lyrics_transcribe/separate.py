"""Vocal separation using Demucs."""

import subprocess
import sys
from pathlib import Path


def separate_vocals(audio_path: Path, output_dir: Path) -> Path:
    """Run Demucs to extract vocals from an audio file.

    Returns the path to the extracted vocals wav file.
    """
    subprocess.run(
        [
            sys.executable, "-m", "demucs",
            "--two-stems", "vocals",
            "-n", "htdemucs_ft",
            "-o", str(output_dir),
            str(audio_path),
        ],
        check=True,
    )

    vocals_path = output_dir / "htdemucs_ft" / audio_path.stem / "vocals.wav"
    if not vocals_path.exists():
        raise FileNotFoundError(f"Expected vocals file not found: {vocals_path}")
    return vocals_path
