from __future__ import annotations

from typing import List, Optional, Tuple

from ...ingestion.metadata_schema import Chunk
from ...vectorstore.chroma_store import ChromaVectorStore
from ..dependencies import get_app_settings, get_openai_client, get_openrouter_client
from ..models_registry import get_model_id
from ..openai_client import OpenAIClient
from ..openrouter_client import OpenRouterClient
from ..schemas import ChatRequest, ChatResponse, UsageInfo
from .citation import build_citations
from .ranking import rerank_by_distance
from .retriever import Retriever


SYSTEM_PROMPT = """You are a financial analysis assistant.
You are given context from official company documents (filings, press releases, and earnings call transcripts).
Answer the user's question using ONLY the provided context.
If the answer cannot be found in the context, say that you do not know and suggest which documents or periods might contain it.
Be precise with numbers and clearly state which company and period you are referring to.
When referencing information from the context, include the page number(s) from the source document (e.g., "as stated on page 5" or "according to page 12-13")."""


def _format_context(chunks_with_scores: List[Tuple[Chunk, float]]) -> str:
    parts: List[str] = []
    for idx, (chunk, _score) in enumerate(chunks_with_scores, start=1):
        meta = chunk.metadata
        page_start = meta.get('page_start')
        page_end = meta.get('page_end')
        page_info = ""
        if page_start:
            if page_end and page_end != page_start:
                page_info = f" | Page {page_start}-{page_end}"
            else:
                page_info = f" | Page {page_start}"
        header = f"[Chunk {idx} | {meta.get('ticker','')} | {meta.get('filing_type','')} | {meta.get('period','')}{page_info}]"
        parts.append(header)
        parts.append(chunk.text)
        parts.append("")
    return "\n".join(parts)


class RAGService:
    def __init__(
        self,
        vector_store: ChromaVectorStore,
        openai_client: Optional[OpenAIClient] = None,
        openrouter_client: Optional[OpenRouterClient] = None,
    ) -> None:
        self._vector_store = vector_store
        self._retriever = Retriever(vector_store)
        self._openai = openai_client or get_openai_client()
        self._openrouter = openrouter_client

    def answer(self, request: ChatRequest) -> ChatResponse:
        chunks_with_scores = self._retriever.retrieve(
            query=request.question,
            k=request.top_k,
            tickers=request.tickers,
            period=request.period,
        )
        ranked = rerank_by_distance(chunks_with_scores)
        context = _format_context(ranked)
        system_prompt = SYSTEM_PROMPT + "\n\nContext:\n" + context

        # Use OpenRouter if a specific model is requested, otherwise use default OpenAI client
        usage_info: Optional[UsageInfo] = None
        model_used: Optional[str] = None

        if request.model:
            # Use OpenRouter for multi-model evaluation
            model_id = get_model_id(request.model)
            openrouter = self._openrouter or get_openrouter_client(model_id)
            result = openrouter.chat(
                system_prompt=system_prompt,
                user_message=request.question,
                model=model_id,
            )
            answer_text = result.answer
            usage_info = UsageInfo(
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                total_tokens=result.total_tokens,
                cost=result.cost,
            )
            model_used = result.model
        else:
            # Use default OpenAI client
            answer_text = self._openai.chat(system_prompt=system_prompt, user_message=request.question)

        chunks_with_scores = ranked  # Keep scores for citations
        chunks_only: List[Chunk] = [cw[0] for cw in ranked]
        citations = build_citations(chunks_with_scores)
        raw_context = [
            {
                "text": chunk.text,
                "metadata": chunk.metadata,
                "score": score,
            }
            for chunk, score in ranked
        ]
        return ChatResponse(
            answer=answer_text,
            citations=citations,
            raw_context=raw_context,
            model=model_used,
            usage=usage_info,
        )


def get_rag_service() -> RAGService:
    settings = get_app_settings()
    vector_store = ChromaVectorStore(persist_directory=str(settings.chroma_persist_dir))
    openai_client = get_openai_client()
    return RAGService(vector_store=vector_store, openai_client=openai_client)



