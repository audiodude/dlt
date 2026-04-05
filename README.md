# Danger Lyrics Transcriber (dlt)

Extract vocals from audio files and transcribe lyrics automatically.

Uses [Demucs](https://github.com/facebookresearch/demucs) (htdemucs_ft) for vocal isolation and [Whisper](https://github.com/openai/whisper) (large-v3) for transcription. Outputs plain text lyrics with natural line/paragraph breaks, plus timed `.lrc` files.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- NVIDIA GPU with ~10GB VRAM recommended (for large-v3 model)

## Install

```bash
uv sync
```

## Usage

```
dlt [-h] [-o OUTPUT_DIR] [--whisper-model MODEL] [--keep-vocals] inputs [inputs ...]
```

### Examples

```bash
# Transcribe a single file
dlt song.mp3

# Batch process a directory, output to ./lyrics/
dlt ~/Music/album/ -o ./lyrics/

# Process multiple files, keep the isolated vocal tracks
dlt track1.mp3 track2.flac --keep-vocals

# Use a smaller/faster model (if you have less VRAM)
dlt song.mp3 --whisper-model medium
```

### Options

| Flag | Description |
|---|---|
| `inputs` | Audio files or directories to process (.mp3, .wav, .flac, .ogg, .m4a, .aac, .wma, .opus) |
| `-o`, `--output-dir` | Directory for output files (default: current directory) |
| `--whisper-model` | Whisper model size (default: `large-v3`) |
| `--keep-vocals` | Save the separated vocals .wav to the output directory |

### Output

For each input file, dlt produces:

- **`songname.txt`** — plain text lyrics with line and paragraph breaks
- **`songname.lrc`** — timed lyrics in LRC format (for karaoke/synced lyrics players)
- **`songname_vocals.wav`** — isolated vocal track (only with `--keep-vocals`)

## How it works

1. **Vocal separation** — Demucs (`htdemucs_ft` model) isolates the vocal stem from the full mix
2. **Transcription** — Whisper transcribes the isolated vocals with word-level timestamps
3. **Formatting** — Gaps between segments determine line breaks (>1.5s) and paragraph breaks (>3.5s)
