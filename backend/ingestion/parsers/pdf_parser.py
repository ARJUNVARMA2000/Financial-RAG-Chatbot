from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pdfplumber

from ..metadata_schema import Block, Document, DocumentMetadata, Line, TableCell


def _extract_paragraph_blocks(page, starting_block_id: int, page_number: int) -> List[Block]:
    blocks: List[Block] = []
    text = page.extract_text() or ""
    if not text.strip():
        return blocks
    lines_obj: List[Line] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        lines_obj.append(Line(line_number=idx, text=raw_line.rstrip()))
    block = Block(
        block_id=f"p_{page_number}_{starting_block_id}",
        type="paragraph",
        page_number=page_number,
        text=text,
        lines=lines_obj,
    )
    blocks.append(block)
    return blocks


def _extract_table_blocks(page, starting_block_id: int, page_number: int) -> List[Block]:
    blocks: List[Block] = []
    tables = page.extract_tables()
    current_id = starting_block_id
    for table in tables or []:
        cells: List[TableCell] = []
        text_lines: List[Line] = []
        line_num = 1
        for r_idx, row in enumerate(table):
            row_text_items: List[str] = []
            for c_idx, cell in enumerate(row):
                cell_text = (cell or "").strip()
                cells.append(TableCell(row=r_idx, col=c_idx, text=cell_text))
                row_text_items.append(cell_text)
            row_text = " | ".join(row_text_items)
            text_lines.append(Line(line_number=line_num, text=row_text))
            line_num += 1
        text = "\n".join(l.text for l in text_lines)
        block = Block(
            block_id=f"t_{page_number}_{current_id}",
            type="table",
            page_number=page_number,
            text=text,
            lines=text_lines,
            cells=cells,
        )
        blocks.append(block)
        current_id += 1
    return blocks


def parse_pdf_to_document(
    file_path: Path,
    *,
    doc_id: str,
    ticker: str,
    filing_type: str,
    period: str,
    source_url: Optional[str] = None,
    title: Optional[str] = None,
) -> Document:
    blocks: List[Block] = []
    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            paragraph_blocks = _extract_paragraph_blocks(page, starting_block_id=len(blocks), page_number=page_index)
            blocks.extend(paragraph_blocks)
            table_blocks = _extract_table_blocks(page, starting_block_id=len(blocks), page_number=page_index)
            blocks.extend(table_blocks)

    metadata = DocumentMetadata(
        doc_id=doc_id,
        ticker=ticker,
        filing_type=filing_type,
        period=period,
        source_url=source_url,
        title=title,
        local_path=file_path,
    )
    return Document(metadata=metadata, blocks=blocks)



