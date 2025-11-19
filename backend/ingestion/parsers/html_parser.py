from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup

from ..metadata_schema import Block, Document, DocumentMetadata, Line, TableCell


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def parse_html_to_document(
    file_path: Path,
    *,
    doc_id: str,
    ticker: str,
    filing_type: str,
    period: str,
    source_url: Optional[str] = None,
    title: Optional[str] = None,
) -> Document:
    html = file_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    blocks: List[Block] = []
    block_index = 0

    # Paragraph-like elements
    for p in soup.find_all(["p", "div"]):
        text = _normalize_whitespace(p.get_text(separator=" ", strip=True))
        if not text:
            continue
        lines = [Line(line_number=1, text=text)]
        block = Block(
            block_id=f"p_{block_index}",
            type="paragraph",
            page_number=None,
            text=text,
            lines=lines,
        )
        blocks.append(block)
        block_index += 1

    # Simple table extraction
    for table in soup.find_all("table"):
        cells: List[TableCell] = []
        lines: List[Line] = []
        line_num = 1
        for r_idx, row in enumerate(table.find_all("tr")):
            row_texts: List[str] = []
            cols = row.find_all(["td", "th"])
            for c_idx, cell in enumerate(cols):
                cell_text = _normalize_whitespace(cell.get_text(separator=" ", strip=True))
                cells.append(TableCell(row=r_idx, col=c_idx, text=cell_text))
                row_texts.append(cell_text)
            if row_texts:
                row_line = " | ".join(row_texts)
                lines.append(Line(line_number=line_num, text=row_line))
                line_num += 1
        if lines:
            text = "\n".join(l.text for l in lines)
            block = Block(
                block_id=f"t_{block_index}",
                type="table",
                page_number=None,
                text=text,
                lines=lines,
                cells=cells,
            )
            blocks.append(block)
            block_index += 1

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



