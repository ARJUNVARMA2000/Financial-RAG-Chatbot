from typing import Any, List, Optional

from pydantic import BaseModel


class Citation(BaseModel):
    doc_id: str
    doc_title: Optional[str] = None
    ticker: Optional[str] = None
    filing_type: Optional[str] = None
    period: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    table_id: Optional[str] = None
    source_url: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    tickers: Optional[List[str]] = None
    period: Optional[str] = None
    top_k: int = 8


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    raw_context: Optional[List[dict[str, Any]]] = None



