from __future__ import annotations

from typing import Optional
from urllib.parse import quote


def build_search_phrase(text: str, max_words: int = 24) -> str:
    """
    Normalize whitespace and keep only the first N words to form a stable
    search phrase for PDF viewers.
    """
    normalized = " ".join(text.split())
    if not normalized:
        return ""
    words = normalized.split()
    return " ".join(words[:max_words])


def append_pdf_fragment(base: str, page: Optional[int], phrase: str) -> str:
    """
    Append page/search parameters to the base PDF URL, preserving any
    existing fragments.
    """
    fragment_parts = []
    if page:
        fragment_parts.append(f"page={page}")
    if phrase:
        fragment_parts.append(f"search={quote(phrase)}")
    if not fragment_parts:
        return base
    if "#" in base:
        return f"{base}&{'&'.join(fragment_parts)}"
    return f"{base}#{'&'.join(fragment_parts)}"
