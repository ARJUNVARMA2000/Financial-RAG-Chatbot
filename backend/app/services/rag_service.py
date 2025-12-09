from __future__ import annotations

from typing import List, Optional, Tuple, Dict

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

MIN_SIMILARITY = 0.35  # drop low-signal chunks (cosine distance -> similarity)


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

    def get_available_periods(self, ticker: str) -> List[str]:
        """
        Get all available periods for a given ticker.
        """
        print(f"🔍 get_available_periods called with ticker={ticker}")
        
        try:
            # Use vector store method if available
            if hasattr(self._vector_store, 'get_available_periods'):
                print(f"🔍 Using vector_store.get_available_periods()")
                result = self._vector_store.get_available_periods(ticker)
                print(f"🔍 vector_store returned: {result}")
                return result
            
            print(f"🔍 Using fallback method with retriever")
            # Fallback: query for this ticker and extract unique periods
            chunks_with_scores = self._retriever.retrieve(
                query="",  # Empty query to get all chunks
                k=100,  # Get enough to see all periods
                tickers=[ticker.upper()],
                period=None,
                allow_blank_query=True,
            )
            
            print(f"🔍 Retriever returned {len(chunks_with_scores)} chunks")
            
            periods = set()
            for chunk, _ in chunks_with_scores:
                if 'period' in chunk.metadata:
                    periods.add(chunk.metadata['period'])
                    print(f"🔍 Found period: {chunk.metadata['period']}")
            
            result = sorted(list(periods))
            print(f"🔍 Final periods: {result}")
            return result
        except Exception as e:
            print(f"🔍 ERROR in get_available_periods: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_all_available_data(self) -> Dict[str, List[str]]:
        """
        Get all available tickers and their periods.
        
        Returns:
            Dict mapping ticker -> list of periods
            Example: {"NVDA": ["Q1-2026", "Q2-2026"], "AMZN": ["Q3-2025"]}
        """
        try:
            # Use vector store method if available
            if hasattr(self._vector_store, 'get_ticker_period_map'):
                return self._vector_store.get_ticker_period_map()
            
            # Fallback: query all and extract
            chunks_with_scores = self._retriever.retrieve(
                query="",  # Empty query
                k=1000,  # Get many chunks
                tickers=None,
                period=None,
                allow_blank_query=True,
            )
            
            ticker_periods: Dict[str, set] = {}
            for chunk, _ in chunks_with_scores:
                ticker = chunk.metadata.get('ticker', '').upper()
                period = chunk.metadata.get('period', '')
                
                if ticker and period:
                    if ticker not in ticker_periods:
                        ticker_periods[ticker] = set()
                    ticker_periods[ticker].add(period)
            
            # Convert sets to sorted lists
            return {
                ticker: sorted(list(periods))
                for ticker, periods in ticker_periods.items()
            }
        except Exception as e:
            print(f"Error getting available data: {e}")
            return {}

    def _build_availability_message(
        self, 
        requested_tickers: Optional[List[str]], 
        requested_period: Optional[str]
    ) -> str:
        """
        Build a helpful message about available data when no results found.
        """
        print(f"🔍 DEBUG: requested_tickers = {requested_tickers}")
        print(f"🔍 DEBUG: requested_period = {requested_period}")
        
        if not requested_tickers:
            # No ticker specified - show all available data
            all_data = self.get_all_available_data()
            
            if not all_data:
                return "I don't have any financial data available in my database yet."
            
            msg = "I don't have data for that specific query. Here's what's available:\n\n"
            for ticker, periods in sorted(all_data.items()):
                periods_str = ", ".join(periods)
                msg += f"**{ticker}**: {periods_str}\n"
            
            msg += "\nPlease rephrase your question to specify one of the available tickers and periods."
            return msg
        
        # Ticker(s) specified - check which tickers have data
        tickers_with_data = {}
        tickers_without_data = []
        
        for ticker in requested_tickers:
            periods = self.get_available_periods(ticker)
            print(f"🔍 DEBUG: Checking ticker={ticker}, found periods={periods}")
            if periods:
                tickers_with_data[ticker.upper()] = periods
            else:
                tickers_without_data.append(ticker.upper())
        
        print(f"🔍 DEBUG: tickers_with_data = {tickers_with_data}")
        print(f"🔍 DEBUG: tickers_without_data = {tickers_without_data}")
        
        # Case 1: None of the requested tickers have any data
        if not tickers_with_data:
            print("🔍 DEBUG: Entered CASE 1 - No data for ticker")
            ticker_str = ", ".join([t.upper() for t in requested_tickers])
            all_data = self.get_all_available_data()
            
            msg = f"I don't have any data for {ticker_str}.\n\n"
            
            if all_data:
                msg += "Available companies:\n"
                for ticker, periods in sorted(all_data.items()):
                    periods_str = ", ".join(periods)
                    msg += f"- **{ticker}**: {periods_str}\n"
                
                msg += "\nPlease ask about one of the available companies."
            else:
                msg += "I don't have any financial data available in my database yet."
            
            return msg
        
        # Case 2: Ticker(s) exist, but wrong period or no results for query
        print("🔍 DEBUG: Entered CASE 2 - Ticker exists, wrong period")
        msg = ""
        
        if requested_period:
            # User specified a period - show it's not available
            ticker_str = ", ".join([t.upper() for t in requested_tickers])
            msg += f"I don't have data for **{ticker_str}** in period **{requested_period}**.\n\n"
            msg += "Available periods for your requested ticker(s):\n\n"
        else:
            # No period specified, but no results found
            msg += "I couldn't find relevant data for your query. Here's what's available:\n\n"
        
        # Show available periods for tickers that DO have data
        for ticker, periods in sorted(tickers_with_data.items()):
            periods_str = ", ".join(periods)
            msg += f"**{ticker}**: {periods_str}\n"
        
        msg += "\nPlease rephrase your question using one of the available periods."
        
        return msg

    def answer(self, request: ChatRequest) -> ChatResponse:
        # Basic guardrail for empty/whitespace-only questions
        if not request.question.strip():
            return ChatResponse(
                answer="Please provide a financial question so I can search the filings and transcripts.",
                citations=[],
                raw_context=None,
                model=None,
                usage=None,
                retrieval_debug={"skipped": True, "reason": "empty_question"},
            )

        # Retrieve relevant chunks
        chunks_with_scores = self._retriever.retrieve(
            query=request.question,
            k=request.top_k,
            tickers=request.tickers,
            period=request.period,
            min_similarity=MIN_SIMILARITY,
        )
        
        # ✅ CHECK IF NO RESULTS FOUND
        if not chunks_with_scores or len(chunks_with_scores) == 0:
            # Build helpful message with available periods
            availability_msg = self._build_availability_message(
                requested_tickers=request.tickers,
                requested_period=request.period
            )
            
            return ChatResponse(
                answer=availability_msg,
                citations=[],
                raw_context=None,
                model=None,
                usage=None,
                retrieval_debug={
                    "query_length": len(request.question),
                    "requested_top_k": request.top_k,
                    "filters": {
                        "tickers": request.tickers,
                        "period": request.period,
                    },
                    "retrieved": 0,
                    "filtered": 0,
                    "min_similarity_threshold": MIN_SIMILARITY,
                },
            )
        
        # Continue with normal RAG flow
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
            retrieval_debug={
                "query_length": len(request.question),
                "requested_top_k": request.top_k,
                "filters": {
                    "tickers": request.tickers,
                    "period": request.period,
                },
                "retrieved": len(chunks_with_scores),
                "filtered": len(chunks_with_scores),
                "min_similarity_threshold": MIN_SIMILARITY,
                "min_distance": min(score for _, score in ranked) if ranked else None,
                "max_distance": max(score for _, score in ranked) if ranked else None,
            },
        )


def get_rag_service() -> RAGService:
    settings = get_app_settings()
    vector_store = ChromaVectorStore(persist_directory=str(settings.chroma_persist_dir))
    openai_client = get_openai_client()
    return RAGService(vector_store=vector_store, openai_client=openai_client)

