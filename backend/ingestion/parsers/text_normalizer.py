from __future__ import annotations

import re
from typing import Iterable

from ..metadata_schema import Block


SECTION_PATTERNS = {
    "income_statement": re.compile(r"consolidated statements? of income", re.I),
    "balance_sheet": re.compile(r"consolidated balance sheets?", re.I),
    "cash_flow": re.compile(r"consolidated statements? of cash flows", re.I),
    "revenue": re.compile(r"\brevenue\b|\bsales\b", re.I),
    "segment_information": re.compile(r"\bsegment\b", re.I),
}


def clean_whitespace(text: str) -> str:
    return " ".join(text.split())


def tag_sections(blocks: Iterable[Block]) -> None:
    """
    In-place heuristic section tagging based on block text.
    """
    for block in blocks:
        text = block.text.lower()
        for name, pattern in SECTION_PATTERNS.items():
            if pattern.search(text):
                block.section = name
                break



