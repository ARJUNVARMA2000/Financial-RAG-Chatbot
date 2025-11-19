from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class TranscriptInfo:
    ticker: str
    period: str
    local_path: Path


def save_transcript_text(
    text: str,
    ticker: str,
    period: str,
    dest_root: Path,
    name: str = "transcript",
) -> TranscriptInfo:
    """
    For now this is a simple helper that lets you manually paste transcript
    text and persist it to data/raw/<ticker>/ as a .txt file.

    Later this can be extended to fetch from a real transcripts API or data
    provider.
    """
    dest_dir = dest_root / ticker.lower()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / f"{name}_{period}.txt"
    dest_path.write_text(text, encoding="utf-8")
    return TranscriptInfo(ticker=ticker, period=period, local_path=dest_path)



