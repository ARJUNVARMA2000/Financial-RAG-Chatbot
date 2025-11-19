from __future__ import annotations

from pathlib import Path
from typing import List

from .edgar_client import DownloadedFile, download_file


def download_ir_documents_for_urls(
    urls: List[str],
    ticker: str,
    dest_root: Path,
    prefix: str = "ir",
) -> List[DownloadedFile]:
    """
    Download a list of investor-relations documents (press releases, earnings
    presentations, etc.) into data/raw/<ticker>/.
    """
    results: List[DownloadedFile] = []
    for idx, url in enumerate(urls, start=1):
        ext = ".html"
        lower = url.lower()
        if lower.endswith(".pdf"):
            ext = ".pdf"
        dest_dir = dest_root / ticker.lower()
        dest_name = f"{prefix}_{idx}{ext}"
        dest_path = dest_dir / dest_name
        results.append(download_file(url, dest_path))
    return results



