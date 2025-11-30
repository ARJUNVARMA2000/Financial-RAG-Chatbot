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
    chunk_id: Optional[str] = None
    highlight_url: Optional[str] = None
    text: Optional[str] = None  # Text preview for citation
    relevance_score: Optional[float] = None  # Relevance score (lower = more relevant)


class UsageInfo(BaseModel):
    """Token usage and cost information for a request."""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0  # Cost in USD


class ChatRequest(BaseModel):
    question: str
    tickers: Optional[List[str]] = None
    period: Optional[str] = None
    top_k: int = 8
    model: Optional[str] = None  # OpenRouter model ID for evaluation


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    raw_context: Optional[List[dict[str, Any]]] = None
    model: Optional[str] = None  # Model used for this response
    usage: Optional[UsageInfo] = None  # Token usage and cost tracking


class ParseQueryRequest(BaseModel):
    """Request to parse a user query for entity extraction."""
    question: str


class ParseQueryResponse(BaseModel):
    """Response containing extracted entities from a user query."""
    tickers: Optional[List[str]] = None
    period: Optional[str] = None
    needs_clarification: bool = False
    clarification_message: Optional[str] = None



