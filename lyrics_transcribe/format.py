"""Format Whisper transcription results into lyrics."""

from pathlib import Path

# Gaps (in seconds) used to determine line and paragraph breaks.
LINE_GAP = 1.5
PARAGRAPH_GAP = 3.5


def _format_timestamp_lrc(seconds: float) -> str:
    """Format seconds as [mm:ss.xx] for LRC."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"[{minutes:02d}:{secs:05.2f}]"


def segments_to_txt(segments: list[dict]) -> str:
    """Convert Whisper segments to formatted plain-text lyrics.

    Inserts line breaks at pauses > LINE_GAP seconds and
    paragraph breaks at pauses > PARAGRAPH_GAP seconds.
    """
    lines: list[str] = []
    prev_end = 0.0

    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue

        gap = seg["start"] - prev_end

        if prev_end > 0 and gap >= PARAGRAPH_GAP:
            lines.append("")  # blank line = paragraph break
        elif prev_end > 0 and gap >= LINE_GAP:
            pass  # new line, no blank line
        elif lines:
            # Short gap — append to the previous line
            lines[-1] += " " + text
            prev_end = seg["end"]
            continue

        lines.append(text)
        prev_end = seg["end"]

    return "\n".join(lines) + "\n"


def segments_to_lrc(segments: list[dict]) -> str:
    """Convert Whisper segments to LRC (timed lyrics) format."""
    lrc_lines: list[str] = []
    prev_end = 0.0

    for seg in segments:
        text = seg["text"].strip()
        if not text:
            continue

        gap = seg["start"] - prev_end
        timestamp = _format_timestamp_lrc(seg["start"])

        if prev_end > 0 and gap >= PARAGRAPH_GAP:
            # Insert an empty timed line for the paragraph gap
            gap_ts = _format_timestamp_lrc(prev_end + 0.5)
            lrc_lines.append(f"{gap_ts}")

        lrc_lines.append(f"{timestamp} {text}")
        prev_end = seg["end"]

    return "\n".join(lrc_lines) + "\n"


def write_outputs(segments: list[dict], output_stem: Path) -> tuple[Path, Path]:
    """Write .txt and .lrc files. Returns (txt_path, lrc_path)."""
    txt_path = output_stem.with_suffix(".txt")
    lrc_path = output_stem.with_suffix(".lrc")

    txt_path.write_text(segments_to_txt(segments))
    lrc_path.write_text(segments_to_lrc(segments))

    return txt_path, lrc_path
