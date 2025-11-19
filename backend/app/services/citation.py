from __future__ import annotations

from typing import Any, Dict, List

from ...ingestion.metadata_schema import Chunk
from ..schemas import Citation


def build_citations(chunks: List[Chunk]) -> List[Citation]:
    citations: List[Citation] = []
    for ch in chunks:
        meta: Dict[str, Any] = ch.metadata
        citations.append(
            Citation(
                doc_id=str(meta.get("doc_id", "")),
                doc_title=str(meta.get("title") or ""),
                ticker=str(meta.get("ticker") or ""),
                filing_type=str(meta.get("filing_type") or ""),
                period=str(meta.get("period") or ""),
                section=str(meta.get("section") or ""),
                page=int(meta.get("page_start") or 0) or None,
                line_start=meta.get("line_start"),
                line_end=meta.get("line_end"),
                table_id=str(meta.get("table_id") or "") or None,
                source_url=str(meta.get("source_url") or "") or None,
            )
        )
    return citations



