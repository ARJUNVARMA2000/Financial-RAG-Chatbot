from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ...ingestion.metadata_schema import Chunk
from ..schemas import Citation
from .highlight import append_pdf_fragment, build_search_phrase


def _build_highlight_url(chunk: Chunk) -> Optional[str]:
    meta: Dict[str, Any] = chunk.metadata
    doc_id = str(meta.get("doc_id") or "")
    chunk_id = str(meta.get("chunk_id") or "")
    page = meta.get("page_start")
    search_phrase = build_search_phrase(chunk.text)
    local_path = str(meta.get("local_path") or "")
    if local_path and doc_id and chunk_id:
        return f"/documents/{doc_id}/chunks/{chunk_id}/viewer"
    source_url = str(meta.get("source_url") or "")
    if source_url:
        if source_url.lower().endswith(".pdf"):
            return append_pdf_fragment(source_url, page, search_phrase)
        return source_url
    return None


def build_citations(chunks_with_scores: List[Tuple[Chunk, float]]) -> List[Citation]:
    """
    Build citations from chunks with their relevance scores.
    
    Args:
        chunks_with_scores: List of (Chunk, score) tuples where score is distance (lower = more relevant)
    
    Returns:
        List of Citation objects ordered by relevance
    """
    citations: List[Citation] = []
    for ch, score in chunks_with_scores:
        meta: Dict[str, Any] = ch.metadata
        
        # Extract page number, handling various types (int, str, None)
        # ChromaDB may return None, 0, empty string, or actual page numbers
        page_start = meta.get("page_start")
        page_num = None
        if page_start is not None and page_start != "":
            try:
                # Convert to int and only use if it's a valid positive page number
                page_int = int(page_start)
                if page_int > 0:  # Only use positive page numbers (0 means no page info)
                    page_num = page_int
            except (ValueError, TypeError):
                page_num = None
        
        # Extract line numbers similarly
        line_start = meta.get("line_start")
        line_end = meta.get("line_end")
        if line_start is not None:
            try:
                line_start = int(line_start) if line_start != 0 else None
            except (ValueError, TypeError):
                line_start = None
        if line_end is not None:
            try:
                line_end = int(line_end) if line_end != 0 else None
            except (ValueError, TypeError):
                line_end = None
        
        # Convert distance to similarity score (lower distance = higher similarity)
        # Normalize to 0-1 range where 1 is most relevant
        # Cosine distance ranges from 0-2, so we convert: similarity = 1 - (distance / 2)
        similarity_score = max(0.0, min(1.0, 1.0 - (score / 2.0))) if score is not None else None
        
        citations.append(
            Citation(
                doc_id=str(meta.get("doc_id", "")),
                doc_title=str(meta.get("title") or ""),
                ticker=str(meta.get("ticker") or ""),
                filing_type=str(meta.get("filing_type") or ""),
                period=str(meta.get("period") or ""),
                section=str(meta.get("section") or ""),
                page=page_num,
                line_start=line_start,
                line_end=line_end,
                table_id=str(meta.get("table_id") or "") or None,
                source_url=str(meta.get("source_url") or "") or None,
                chunk_id=str(meta.get("chunk_id") or "") or None,
                highlight_url=_build_highlight_url(ch),
                text=ch.text[:500] if ch.text else None,  # Add text preview (first 500 chars)
                relevance_score=similarity_score,  # Relevance score (0-1, higher = more relevant)
            )
        )
    return citations



