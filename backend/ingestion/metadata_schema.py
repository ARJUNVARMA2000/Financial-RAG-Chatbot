from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional


@dataclass
class Line:
    line_number: int
    text: str


BlockType = Literal["paragraph", "table"]


@dataclass
class TableCell:
    row: int
    col: int
    text: str


@dataclass
class Block:
    block_id: str
    type: BlockType
    page_number: Optional[int]
    text: str
    lines: List[Line]
    section: Optional[str] = None
    cells: Optional[List[TableCell]] = None


@dataclass
class DocumentMetadata:
    doc_id: str
    ticker: str
    filing_type: str
    period: str
    source_url: Optional[str]
    title: Optional[str] = None
    local_path: Optional[Path] = None


@dataclass
class Document:
    metadata: DocumentMetadata
    blocks: List[Block]


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: Dict[str, Any]



