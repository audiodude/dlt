"""Vocal separation using Demucs."""

import subprocess
import sys
from pathlib import Path


def separate_vocals(audio_path: Path, output_dir: Path) -> tuple[Path, Path]:
    """Run Demucs to extract vocals from an audio file.

    Returns (vocals_path, no_vocals_path).
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

    stem_dir = output_dir / "htdemucs_ft" / audio_path.stem
    vocals_path = stem_dir / "vocals.wav"
    no_vocals_path = stem_dir / "no_vocals.wav"
    if not vocals_path.exists():
        raise FileNotFoundError(f"Expected vocals file not found: {vocals_path}")
    if not no_vocals_path.exists():
        raise FileNotFoundError(f"Expected no_vocals file not found: {no_vocals_path}")
    return vocals_path, no_vocals_path
