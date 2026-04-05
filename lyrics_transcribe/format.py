"""Format Whisper transcription results into lyrics."""

import re
from pathlib import Path

# Gaps (in seconds) between words used to determine breaks.
LINE_GAP = 0.3
PARAGRAPH_GAP = 1.5

# If a line exceeds this many words without a gap-based break,
# break at the largest gap found so far.
MAX_LINE_WORDS = 16

# Patterns Whisper hallucinates during silence at the end of tracks.
HALLUCINATION_PATTERNS = [
    re.compile(r"subtitles\s+(by|from)", re.IGNORECASE),
    re.compile(r"amara\.org", re.IGNORECASE),
    re.compile(r"contributed\s+by", re.IGNORECASE),
    re.compile(r"thank(s| you)\s+(for\s+watching|for\s+listening)", re.IGNORECASE),
    re.compile(r"please\s+subscribe", re.IGNORECASE),
]


def _is_hallucination(text: str) -> bool:
    return any(p.search(text) for p in HALLUCINATION_PATTERNS)


def _format_timestamp_lrc(seconds: float) -> str:
    """Format seconds as [mm:ss.xx] for LRC."""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"[{minutes:02d}:{secs:05.2f}]"


def _extract_words(segments: list[dict]) -> list[dict]:
    """Flatten all word-level timestamps from segments, filtering hallucinations."""
    words = []
    for seg in segments:
        if _is_hallucination(seg.get("text", "")):
            continue
        for w in seg.get("words", []):
            word = w.get("word", "").strip()
            if word:
                words.append({"word": word, "start": w["start"], "end": w["end"]})
    return words


def _build_lines(words: list[dict]) -> list[dict]:
    """Group words into lines using gaps and max-length heuristic.

    Returns a list of dicts with 'text' and 'start' keys.
    """
    if not words:
        return []

    lines: list[dict] = []
    current_words: list[str] = [words[0]["word"]]
    line_start = words[0]["start"]
    # Track the best break point (largest gap) within the current line
    best_gap = 0.0
    best_gap_idx = 0  # index into current_words where we'd split

    for i in range(1, len(words)):
        gap = words[i]["start"] - words[i - 1]["end"]

        if gap >= PARAGRAPH_GAP:
            lines.append({"text": " ".join(current_words), "start": line_start, "paragraph_after": True})
            current_words = [words[i]["word"]]
            line_start = words[i]["start"]
            best_gap = 0.0
            best_gap_idx = 0
        elif gap >= LINE_GAP:
            lines.append({"text": " ".join(current_words), "start": line_start, "paragraph_after": False})
            current_words = [words[i]["word"]]
            line_start = words[i]["start"]
            best_gap = 0.0
            best_gap_idx = 0
        else:
            # Track the largest gap position for forced breaks
            if gap >= best_gap:
                best_gap = gap
                best_gap_idx = len(current_words)

            current_words.append(words[i]["word"])

            # Force a break if line is getting too long
            if len(current_words) >= MAX_LINE_WORDS and best_gap_idx > 0:
                left = current_words[:best_gap_idx]
                right = current_words[best_gap_idx:]
                lines.append({"text": " ".join(left), "start": line_start, "paragraph_after": False})
                line_start = words[i - len(right) + 1]["start"]
                current_words = right
                best_gap = 0.0
                best_gap_idx = 0

    if current_words:
        lines.append({"text": " ".join(current_words), "start": line_start, "paragraph_after": False})

    return lines


def segments_to_txt(segments: list[dict]) -> str:
    """Convert Whisper segments to formatted plain-text lyrics."""
    words = _extract_words(segments)
    lines = _build_lines(words)

    output: list[str] = []
    for line in lines:
        output.append(line["text"])
        if line["paragraph_after"]:
            output.append("")

    return "\n".join(output) + "\n"


def segments_to_lrc(segments: list[dict]) -> str:
    """Convert Whisper segments to LRC (timed lyrics) format."""
    words = _extract_words(segments)
    lines = _build_lines(words)

    lrc_lines: list[str] = []
    for line in lines:
        timestamp = _format_timestamp_lrc(line["start"])
        lrc_lines.append(f"{timestamp} {line['text']}")
        if line["paragraph_after"]:
            lrc_lines.append("")

    return "\n".join(lrc_lines) + "\n"


def write_outputs(segments: list[dict], output_stem: Path) -> tuple[Path, Path]:
    """Write .txt and .lrc files. Returns (txt_path, lrc_path)."""
    txt_path = output_stem.with_suffix(".txt")
    lrc_path = output_stem.with_suffix(".lrc")

    txt_path.write_text(segments_to_txt(segments))
    lrc_path.write_text(segments_to_lrc(segments))

    return txt_path, lrc_path
