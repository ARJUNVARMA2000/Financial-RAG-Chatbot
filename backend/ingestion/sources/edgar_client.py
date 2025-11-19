from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import httpx


@dataclass
class DownloadedFile:
    url: str
    local_path: Path


USER_AGENT = "financial-rag-bot/0.1 (mailto:example@example.com)"


def download_file(url: str, dest_path: Path, timeout: float = 30.0) -> DownloadedFile:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}
    with httpx.stream("GET", url, headers=headers, timeout=timeout) as resp:
        resp.raise_for_status()
        with dest_path.open("wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)
    return DownloadedFile(url=url, local_path=dest_path)


def download_edgar_filings_for_urls(
    urls: List[str],
    ticker: str,
    dest_root: Path,
    prefix: Optional[str] = None,
) -> List[DownloadedFile]:
    """
    Simple helper that downloads a list of already-known EDGAR document URLs
    into data/raw/<ticker>/.

    This keeps the implementation straightforward for the prototype; more
    advanced EDGAR search (by CIK, year, quarter) can be added later.
    """
    results: List[DownloadedFile] = []
    for idx, url in enumerate(urls, start=1):
        name_prefix = prefix or "filing"
        ext = ".html"
        if url.lower().endswith(".pdf"):
            ext = ".pdf"
        dest_dir = dest_root / ticker.lower()
        dest_name = f"{name_prefix}_{idx}{ext}"
        dest_path = dest_dir / dest_name
        results.append(download_file(url, dest_path))
    return results



