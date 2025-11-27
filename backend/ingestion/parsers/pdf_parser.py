from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pdfplumber
import fitz
from PIL import Image
from openai import OpenAI
import io 
import base64     

from ..metadata_schema import Block, Document, DocumentMetadata, Line, TableCell


def _extract_chart_blocks(
    file_path: Path, 
    page_number: int, 
    starting_block_id: int,
    starting_line: int = 1,
    openai_client: Optional[OpenAI] = None
) -> tuple[List[Block], int]:
    """
    Extract charts/graphs from PDF using GPT-4o Vision.
    Returns: (blocks, next_line_number)
    """
    blocks: List[Block] = []
    
    if openai_client is None:
        return blocks, starting_line
    
    try:
        pdf_doc = fitz.open(file_path)
        page = pdf_doc[page_number - 1]
        image_list = page.get_images()
        
        if not image_list:
            return blocks, starting_line
        
        print(f"Found {len(image_list)} images on page {page_number}")
        
        current_id = starting_block_id
        current_line = starting_line
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = pdf_doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                image = Image.open(io.BytesIO(image_bytes))
                width, height = image.size
                
                if width < 200 or height < 200:
                    print(f"        Skipping small image ({width}x{height})")
                    continue
                
                buffered = io.BytesIO()
                image.save(buffered, format="PNG")
                image_b64 = base64.b64encode(buffered.getvalue()).decode()
                
                print(f"        Analyzing chart {img_index + 1} with GPT-4o Vision...")
                chart_data = _analyze_chart_with_vision(image_b64, openai_client)
                
                if chart_data and chart_data.strip():
                    chart_line_start = current_line
                    
                    lines_obj = [
                        Line(line_number=current_line + i, text=line)
                        for i, line in enumerate(chart_data.splitlines())
                    ]
                    
                    current_line += len(lines_obj)
                    chart_line_end = current_line - 1
                    
                    block = Block(
                        block_id=f"c_{page_number}_{current_id}",
                        type="chart",
                        page_number=page_number,
                        text=chart_data,
                        lines=lines_obj,
                        metadata={"section": "Unknown"}
                    )
                    
                    # ✅ Page-based line numbers
                    block.line_start = chart_line_start
                    block.line_end = chart_line_end
                    
                    blocks.append(block)
                    current_id += 1
                    print(f"        ✅ Extracted chart data ({len(chart_data)} chars)")
                
            except Exception as e:
                print(f"        ⚠️  Error processing image {img_index}: {e}")
                continue
        
        pdf_doc.close()
        
    except Exception as e:
        print(f"      ⚠️  Error extracting charts from page {page_number}: {e}")
    
    return blocks, current_line


def _analyze_chart_with_vision(image_b64: str, openai_client: OpenAI) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                { "role": "user", "content": [
                    { "type": "text", "text": "..." },
                    { "type": "image_url", "image_url": { "url": f"data:image/png;base64,{image_b64}" } }
                ]}
            ],
        )

        msg = response.choices[0].message

        if isinstance(msg.content, str):
            return msg.content.strip()

        if isinstance(msg.content, list):
            parts = []
            for c in msg.content:
                if c.get("type") in ("text", "output_text"):
                    parts.append(c.get("text", ""))
            return "\n".join(parts).strip()

        return ""

    except Exception as e:
        print(f"⚠️ GPT Vision error: {e}")
        return ""


def _extract_paragraph_blocks(page, starting_block_id: int, page_number: int, starting_line: int = 1) -> tuple[List[Block], int]:
    """
    Extract text paragraphs - SPLIT BY PARAGRAPH, NOT ENTIRE PAGE!
    
    Line numbers are PAGE-BASED (reset for each page).
    Returns: (blocks, next_line_number_on_this_page)
    """
    blocks: List[Block] = []
    text = page.extract_words() or ""
    if not text.strip():
        return blocks, starting_line
    
    # Split text into paragraphs
    paragraphs = text.split('\n\n')
    
    current_line = starting_line
    
    for para_idx, para_text in enumerate(paragraphs):
        para_text = para_text.strip()
        if not para_text:
            continue
        
        # Track line start for this paragraph (on this page)
        para_line_start = current_line
        
        # Count lines in this paragraph
        lines_in_para = para_text.split('\n')
        lines_obj: List[Line] = []
        
        for line_text in lines_in_para:
            line_text = line_text.rstrip()
            if line_text:  # Only add non-empty lines
                lines_obj.append(Line(line_number=current_line, text=line_text))
                current_line += 1
        
        if not lines_obj:
            continue
        
        # Track line end for this paragraph (on this page)
        para_line_end = current_line - 1
        
        block = Block(
            block_id=f"p_{page_number}_{starting_block_id + para_idx}",
            type="paragraph",
            page_number=page_number,
            text=para_text,
            lines=lines_obj,
            metadata={"section": "Unknown"} 
        )
        
        # ✅ Page-based line numbers
        block.line_start = para_line_start
        block.line_end = para_line_end
        
        blocks.append(block)
    
    return blocks, current_line


def _extract_table_blocks(page, starting_block_id: int, page_number: int, starting_line: int = 1) -> tuple[List[Block], int]:
    """
    Extract tables from page.
    
    Line numbers are PAGE-BASED (reset for each page).
    Returns: (blocks, next_line_number_on_this_page)
    """
    blocks: List[Block] = []
    tables = page.extract_tables()
    current_id = starting_block_id
    current_line = starting_line
    
    for table in tables or []:
        cells: List[TableCell] = []
        text_lines: List[Line] = []
        
        # Track line start for this table (on this page)
        table_line_start = current_line
        
        for r_idx, row in enumerate(table):
            row_text_items: List[str] = []
            for c_idx, cell in enumerate(row):
                cell_text = (cell or "").strip()
                cells.append(TableCell(row=r_idx, col=c_idx, text=cell_text))
                row_text_items.append(cell_text)
            row_text = " | ".join(row_text_items)
            text_lines.append(Line(line_number=current_line, text=row_text))
            current_line += 1
        
        # Track line end for this table (on this page)
        table_line_end = current_line - 1
        
        text = "\n".join(l.text for l in text_lines)
        block = Block(
            block_id=f"t_{page_number}_{current_id}",
            type="table",
            page_number=page_number,
            text=text,
            lines=text_lines,
            cells=cells,
            metadata={"section": "Unknown"} 
        )
        
        # ✅ Page-based line numbers
        block.line_start = table_line_start if text_lines else None
        block.line_end = table_line_end if text_lines else None
        
        blocks.append(block)
        current_id += 1
    
    return blocks, current_line


def parse_pdf_to_document(
    file_path: Path,
    *,
    doc_id: str,
    ticker: str,
    filing_type: str,
    period: str,
    source_url: Optional[str] = None,
    title: Optional[str] = None,
    openai_client: Optional[OpenAI] = None,
    extract_charts: bool = True, 
) -> Document:
    """
    Parse PDF to Document with PAGE-BASED line numbering.
    
    Each page's line numbers start from 1, making it easy to reference:
    "Page 5, Lines 10-25" instead of "Lines 510-525"
    """
    blocks: List[Block] = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            # ✅ RESET line counter for each page (page-based numbering)
            page_line_number = 1
            
            # Extract paragraphs
            paragraph_blocks, page_line_number = _extract_paragraph_blocks(
                page, 
                starting_block_id=len(blocks), 
                page_number=page_index,
                starting_line=page_line_number
            )
            blocks.extend(paragraph_blocks)
            
            # Extract tables
            table_blocks, page_line_number = _extract_table_blocks(
                page, 
                starting_block_id=len(blocks), 
                page_number=page_index,
                starting_line=page_line_number
            )
            blocks.extend(table_blocks)
            
            # Extract charts
            if extract_charts and openai_client:
                chart_blocks, page_line_number = _extract_chart_blocks(
                    file_path,
                    page_number=page_index,
                    starting_block_id=len(blocks),
                    starting_line=page_line_number,
                    openai_client=openai_client
                )
                blocks.extend(chart_blocks)

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

################################################################################################################


# from __future__ import annotations

# from pathlib import Path
# from typing import List, Optional

# import pdfplumber

# from ..metadata_schema import Block, Document, DocumentMetadata, Line, TableCell


# def _extract_paragraph_blocks(page, starting_block_id: int, page_number: int) -> List[Block]:
#     blocks: List[Block] = []
#     text = page.extract_text() or ""
#     if not text.strip():
#         return blocks
#     lines_obj: List[Line] = []
#     for idx, raw_line in enumerate(text.splitlines(), start=1):
#         lines_obj.append(Line(line_number=idx, text=raw_line.rstrip()))
#     block = Block(
#         block_id=f"p_{page_number}_{starting_block_id}",
#         type="paragraph",
#         page_number=page_number,
#         text=text,
#         lines=lines_obj,
#     )
#     blocks.append(block)
#     return blocks


# def _extract_table_blocks(page, starting_block_id: int, page_number: int) -> List[Block]:
#     blocks: List[Block] = []
#     tables = page.extract_tables()
#     current_id = starting_block_id
#     for table in tables or []:
#         cells: List[TableCell] = []
#         text_lines: List[Line] = []
#         line_num = 1
#         for r_idx, row in enumerate(table):
#             row_text_items: List[str] = []
#             for c_idx, cell in enumerate(row):
#                 cell_text = (cell or "").strip()
#                 cells.append(TableCell(row=r_idx, col=c_idx, text=cell_text))
#                 row_text_items.append(cell_text)
#             row_text = " | ".join(row_text_items)
#             text_lines.append(Line(line_number=line_num, text=row_text))
#             line_num += 1
#         text = "\n".join(l.text for l in text_lines)
#         block = Block(
#             block_id=f"t_{page_number}_{current_id}",
#             type="table",
#             page_number=page_number,
#             text=text,
#             lines=text_lines,
#             cells=cells,
#         )
#         blocks.append(block)
#         current_id += 1
#     return blocks


# def parse_pdf_to_document(
#     file_path: Path,
#     *,
#     doc_id: str,
#     ticker: str,
#     filing_type: str,
#     period: str,
#     source_url: Optional[str] = None,
#     title: Optional[str] = None,
# ) -> Document:
#     blocks: List[Block] = []
#     with pdfplumber.open(file_path) as pdf:
#         for page_index, page in enumerate(pdf.pages, start=1):
#             paragraph_blocks = _extract_paragraph_blocks(page, starting_block_id=len(blocks), page_number=page_index)
#             blocks.extend(paragraph_blocks)
#             table_blocks = _extract_table_blocks(page, starting_block_id=len(blocks), page_number=page_index)
#             blocks.extend(table_blocks)

#     metadata = DocumentMetadata(
#         doc_id=doc_id,
#         ticker=ticker,
#         filing_type=filing_type,
#         period=period,
#         source_url=source_url,
#         title=title,
#         local_path=file_path,
#     )
#     return Document(metadata=metadata, blocks=blocks)



