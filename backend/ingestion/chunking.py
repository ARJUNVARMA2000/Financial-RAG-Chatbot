from __future__ import annotations
from typing import List, Optional, Tuple
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from .metadata_schema import Block, Chunk, Document

@dataclass
class ChunkingConfig:
    max_tokens: int = 800
    overlap_tokens: int = 200
    min_chunk_size: int = 100
    max_block_tokens: int = 500

    keep_tables_intact: bool = True
    keep_charts_intact: bool = True

    add_document_context: bool = True
    add_section_headers: bool = True

    use_semantic_boundaries: bool = True
    separators: List[str] = None

    def __post_init__(self):
        if self.separators is None:
            # Paragraph → line → sentence → phrase → word → character
            self.separators = ["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]


def _split_large_blocks(blocks: List[Block], max_block_tokens: int):
    """Split blocks that exceed max_block_tokens, while safely handling missing attributes."""
    new_blocks = []

    for block in blocks:
        words = block.text.split()
        total_words = len(words)

        if total_words <= max_block_tokens:
            new_blocks.append(block)
            continue

        # Safe defaults for metadata (these may not exist)
        block_line_start = getattr(block, "line_start", None)
        block_line_end = getattr(block, "line_end", None)

        # Allowed Block fields — we extract them directly from the instance
        allowed_keys = set(block.__dataclass_fields__.keys())

        start_idx = 0
        chunk_id = 0

        while start_idx < total_words:
            end_idx = min(start_idx + max_block_tokens, total_words)

            chunk_text = " ".join(words[start_idx:end_idx])

            # Estimate line metadata ONLY if block originally had it
            if block_line_start is not None and block_line_end is not None:
                approx_lines = block_line_end - block_line_start + 1
                words_per_line = max(total_words / approx_lines, 1)

                est_line_start = block_line_start + int(start_idx / words_per_line)
                est_line_end = block_line_start + int(end_idx / words_per_line)
            else:
                est_line_start = None
                est_line_end = None

            # Prepare safe dict for Block init
            new_block_dict = {}

            for key in allowed_keys:
                # Copy existing metadata
                new_block_dict[key] = getattr(block, key, None)

            # Override block_id and text
            new_block_dict["block_id"] = f"{block.block_id}_split_{chunk_id}"
            new_block_dict["text"] = chunk_text

            # Only include line metadata if Block supports it
            if "line_start" in allowed_keys:
                new_block_dict["line_start"] = est_line_start
            if "line_end" in allowed_keys:
                new_block_dict["line_end"] = est_line_end

            # Construct the new block safely
            new_blocks.append(Block(**new_block_dict))

            start_idx = end_idx
            chunk_id += 1

    return new_blocks

def _build_chunk_metadata(blocks: List[Block]) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
    """
    Calculate line and page start/end for a chunk.
    """
    line_numbers = [b.line_number for b in blocks if hasattr(b, "line_number")]
    page_numbers = [b.page_number for b in blocks if hasattr(b, "page_number")]

    line_start = min(line_numbers) if line_numbers else None
    line_end = max(line_numbers) if line_numbers else None
    page_start = min(page_numbers) if page_numbers else None
    page_end = max(page_numbers) if page_numbers else None

    return line_start, line_end, page_start, page_end


def chunk_document(doc: Document, config: ChunkingConfig) -> List[Chunk]:
    """
    Chunk a document into smaller pieces using config.
    """
    all_chunks: List[Chunk] = []

    for page_blocks in doc.blocks:
        # Step 1: Split large blocks
        page_blocks = _split_large_blocks(page_blocks, config.max_block_tokens)

        # Step 2: Use text splitter on block text
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.max_tokens,
            chunk_overlap=config.overlap_tokens,
            separators=config.separators,
            length_function=lambda t: len(t.split())
        )

        for block in page_blocks:
            text_chunks = splitter.split_text(block.text)
            for idx, chunk_text in enumerate(text_chunks):
                # Compute chunk metadata
                blocks_in_chunk = [block]  # simple case: one block per chunk
                line_start, line_end, page_start, page_end = _build_chunk_metadata(blocks_in_chunk)

                # Optional page_number for single-page chunks
                page_number = page_start if page_start == page_end else None

                metadata = {
                    "doc_id": doc.metadata.doc_id,
                    "page_start": page_start,
                    "page_end": page_end,
                    "page_number": page_number,
                    "line_start": line_start,
                    "line_end": line_end,
                    "block_ids": block.block_id,
                    "block_type": getattr(block, "type", "unknown")
                }

                chunk = Chunk(
                    chunk_id=f"{doc.metadata.doc_id}_chunk_{len(all_chunks)+1}",
                    text=chunk_text,
                    metadata=metadata
                )
                all_chunks.append(chunk)

    return all_chunks




# from __future__ import annotations

# from typing import Iterable, List

# from .metadata_schema import Block, Chunk, Document


# def _block_token_length(block: Block) -> int:
#     # Simple heuristic: number of words
#     return len(block.text.split())


# def chunk_document(
#     document: Document,
#     max_tokens: int = 400,
#     overlap_tokens: int = 50,
# ) -> List[Chunk]:
#     """
#     Create overlapping chunks from a document while preserving block and
#     line-level mapping via metadata.
#     """
#     chunks: List[Chunk] = []
#     current_tokens = 0
#     current_blocks: List[Block] = []

#     def flush_chunk(idx: int) -> None:
#         nonlocal current_blocks, current_tokens
#         if not current_blocks:
#             return
#         text_parts: List[str] = []
#         line_start = None
#         line_end = None
#         block_ids: List[str] = []
#         pages: List[int] = []

#         for block in current_blocks:
#             block_ids.append(block.block_id)
#             pages.append(block.page_number or 0)
#             text_parts.append(block.text)
#             if block.lines:
#                 if line_start is None:
#                     line_start = block.lines[0].line_number
#                 line_end = block.lines[-1].line_number

#         text = "\n\n".join(text_parts)
#         metadata = {
#             "doc_id": document.metadata.doc_id,
#             "ticker": document.metadata.ticker.lower(),  # Normalize to lowercase for filtering
#             "filing_type": document.metadata.filing_type,
#             "period": document.metadata.period,
#             "source_url": document.metadata.source_url or "",
#             "title": document.metadata.title or "",
#             "block_ids": ",".join(block_ids),  # Convert list to comma-separated string for ChromaDB
#             "page_start": min(pages) if pages else None,
#             "page_end": max(pages) if pages else None,
#             "line_start": line_start,
#             "line_end": line_end,
#             "local_path": str(document.metadata.local_path) if document.metadata.local_path else "",
#         }
#         chunk = Chunk(
#             chunk_id=f"{document.metadata.doc_id}_chunk_{idx}",
#             text=text,
#             metadata=metadata,
#         )
#         chunks.append(chunk)
#         current_blocks = []
#         current_tokens = 0

#     blocks: Iterable[Block] = document.blocks
#     idx = 0
#     for block in blocks:
#         block_tokens = _block_token_length(block)
#         if current_tokens + block_tokens > max_tokens and current_blocks:
#             flush_chunk(idx)
#             idx += 1
#             if overlap_tokens > 0 and chunks:
#                 last_chunk_text = chunks[-1].text
#                 overlap_words = " ".join(last_chunk_text.split()[-overlap_tokens:])
#                 # Create a synthetic overlap block
#                 overlap_block = Block(
#                     block_id=f"overlap_{idx}",
#                     type="paragraph",  # type: ignore[arg-type]
#                     page_number=None,
#                     text=overlap_words,
#                     lines=[],
#                 )
#                 current_blocks.append(overlap_block)
#                 current_tokens = _block_token_length(overlap_block)
#         current_blocks.append(block)
#         current_tokens += block_tokens

#     if current_blocks:
#         flush_chunk(idx)

#     return chunks





