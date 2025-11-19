from __future__ import annotations

from typing import Iterable, List

from .metadata_schema import Block, Chunk, Document


def _block_token_length(block: Block) -> int:
    # Simple heuristic: number of words
    return len(block.text.split())


def chunk_document(
    document: Document,
    max_tokens: int = 400,
    overlap_tokens: int = 50,
) -> List[Chunk]:
    """
    Create overlapping chunks from a document while preserving block and
    line-level mapping via metadata.
    """
    chunks: List[Chunk] = []
    current_tokens = 0
    current_blocks: List[Block] = []

    def flush_chunk(idx: int) -> None:
        nonlocal current_blocks, current_tokens
        if not current_blocks:
            return
        text_parts: List[str] = []
        line_start = None
        line_end = None
        block_ids: List[str] = []
        pages: List[int] = []

        for block in current_blocks:
            block_ids.append(block.block_id)
            pages.append(block.page_number or 0)
            text_parts.append(block.text)
            if block.lines:
                if line_start is None:
                    line_start = block.lines[0].line_number
                line_end = block.lines[-1].line_number

        text = "\n\n".join(text_parts)
        metadata = {
            "doc_id": document.metadata.doc_id,
            "ticker": document.metadata.ticker.lower(),  # Normalize to lowercase for filtering
            "filing_type": document.metadata.filing_type,
            "period": document.metadata.period,
            "source_url": document.metadata.source_url or "",
            "title": document.metadata.title or "",
            "block_ids": ",".join(block_ids),  # Convert list to comma-separated string for ChromaDB
            "page_start": min(pages) if pages else None,
            "page_end": max(pages) if pages else None,
            "line_start": line_start,
            "line_end": line_end,
            "local_path": str(document.metadata.local_path) if document.metadata.local_path else "",
        }
        chunk = Chunk(
            chunk_id=f"{document.metadata.doc_id}_chunk_{idx}",
            text=text,
            metadata=metadata,
        )
        chunks.append(chunk)
        current_blocks = []
        current_tokens = 0

    blocks: Iterable[Block] = document.blocks
    idx = 0
    for block in blocks:
        block_tokens = _block_token_length(block)
        if current_tokens + block_tokens > max_tokens and current_blocks:
            flush_chunk(idx)
            idx += 1
            if overlap_tokens > 0 and chunks:
                last_chunk_text = chunks[-1].text
                overlap_words = " ".join(last_chunk_text.split()[-overlap_tokens:])
                # Create a synthetic overlap block
                overlap_block = Block(
                    block_id=f"overlap_{idx}",
                    type="paragraph",  # type: ignore[arg-type]
                    page_number=None,
                    text=overlap_words,
                    lines=[],
                )
                current_blocks.append(overlap_block)
                current_tokens = _block_token_length(overlap_block)
        current_blocks.append(block)
        current_tokens += block_tokens

    if current_blocks:
        flush_chunk(idx)

    return chunks



