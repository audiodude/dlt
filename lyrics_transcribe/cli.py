"""CLI entry point for lyrics-transcribe."""

import argparse
import sys
import tempfile
from pathlib import Path

from .separate import separate_vocals
from .transcribe import transcribe_vocals
from .format import write_outputs

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma", ".opus"}


def collect_audio_files(paths: list[str]) -> list[Path]:
    """Resolve CLI paths into a flat list of audio files."""
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(
                f for f in sorted(path.iterdir())
                if f.suffix.lower() in AUDIO_EXTENSIONS
            )
        elif path.is_file():
            files.append(path)
        else:
            print(f"Warning: skipping {p} (not found)", file=sys.stderr)
    return files


def process_file(
    audio_path: Path,
    output_dir: Path,
    whisper_model: str,
    keep_vocals: bool,
    vocals_dir: Path,
    keep_instrumental: bool,
    instrumental_dir: Path,
    tmp_dir: Path,
) -> None:
    """Process a single audio file: separate vocals, transcribe, write output."""
    print(f"\n{'='*60}")
    print(f"Processing: {audio_path.name}")
    print(f"{'='*60}")

    # Step 1: Vocal separation (or use cached vocals)
    cached_vocals = vocals_dir / f"{audio_path.stem}_vocals.wav"
    if cached_vocals.exists():
        print("  [1/3] Using cached vocals...")
        vocals_path = cached_vocals
    else:
        print("  [1/3] Separating vocals...")
        vocals_path, no_vocals_path = separate_vocals(audio_path, tmp_dir)
        print(f"         Vocals extracted: {vocals_path}")

        # Save stems to output dirs
        import shutil
        if keep_vocals:
            shutil.copy2(vocals_path, cached_vocals)
            print(f"         {cached_vocals}")
        if keep_instrumental:
            dest = instrumental_dir / f"{audio_path.stem}_instrumental.wav"
            shutil.copy2(no_vocals_path, dest)
            print(f"         {dest}")

    # Step 2: Transcription
    print("  [2/3] Transcribing lyrics...")
    result = transcribe_vocals(str(vocals_path), model_name=whisper_model)

    # Step 3: Write output files
    print("  [3/3] Writing output files...")
    output_stem = output_dir / audio_path.stem
    txt_path, lrc_path = write_outputs(result["segments"], output_stem)
    print(f"         {txt_path}")
    print(f"         {lrc_path}")


def main():
    parser = argparse.ArgumentParser(
        prog="dlt",
        description="Danger Lyrics Transcriber — extract vocals from audio and transcribe lyrics.",
        epilog=(
            "examples:\n"
            "  dlt song.mp3                        Transcribe a single file\n"
            "  dlt *.flac -o ./lyrics               Batch process, output to ./lyrics/\n"
            "  dlt ~/Music/album/ --keep-vocals      Process a directory, keep vocal tracks\n"
            "  dlt song.mp3 --whisper-model medium   Use a smaller/faster Whisper model"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Audio files or directories to process",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Directory for output files (default: current directory)",
    )
    parser.add_argument(
        "--whisper-model",
        default="large-v3",
        help="Whisper model to use (default: large-v3)",
    )
    parser.add_argument(
        "--keep-vocals",
        action="store_true",
        help="Save the separated vocals .wav (to --output-vocals-dir or -o)",
    )
    parser.add_argument(
        "--output-vocals-dir",
        default=None,
        help="Directory for vocals output (default: same as -o)",
    )
    parser.add_argument(
        "--keep-instrumental",
        action="store_true",
        help="Save the instrumental (no vocals) .wav (to --output-instrumental-dir or -o)",
    )
    parser.add_argument(
        "--output-instrumental-dir",
        default=None,
        help="Directory for instrumental output (default: same as -o)",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output_vocals_dir:
        args.keep_vocals = True
    if args.output_instrumental_dir:
        args.keep_instrumental = True

    vocals_dir = Path(args.output_vocals_dir) if args.output_vocals_dir else output_dir
    vocals_dir.mkdir(parents=True, exist_ok=True)
    instrumental_dir = Path(args.output_instrumental_dir) if args.output_instrumental_dir else output_dir
    instrumental_dir.mkdir(parents=True, exist_ok=True)

    audio_files = collect_audio_files(args.inputs)
    if not audio_files:
        print("No audio files found.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(audio_files)} audio file(s) to process.")

    with tempfile.TemporaryDirectory(prefix="lyrics-transcribe-") as tmp_dir:
        for audio_path in audio_files:
            try:
                process_file(
                    audio_path,
                    output_dir,
                    args.whisper_model,
                    args.keep_vocals,
                    vocals_dir,
                    args.keep_instrumental,
                    instrumental_dir,
                    Path(tmp_dir),
                )
            except Exception as e:
                print(f"\nError processing {audio_path.name}: {e}", file=sys.stderr)
                continue

    print(f"\nDone. Processed {len(audio_files)} file(s).")
