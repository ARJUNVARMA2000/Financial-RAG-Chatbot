from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from ...vectorstore.chroma_store import ChromaVectorStore
from ...ingestion.metadata_schema import Chunk


class Retriever:
    def __init__(self, vector_store: ChromaVectorStore) -> None:
        self._store = vector_store

    def retrieve(
        self,
        query: str,
        *,
        k: int = 10,
        tickers: Optional[List[str]] = None,
        period: Optional[str] = None,
        min_similarity: Optional[float] = None,
        allow_blank_query: bool = False,
    ) -> List[Tuple[Chunk, float]]:
        """
        Run a vector search with optional filters and guardrails.

        Args:
            query: User query text.
            k: Number of results to return.
            tickers: Optional ticker filter(s).
            period: Optional period filter (e.g., Q3-2025).
            min_similarity: If provided, drop results whose similarity falls below this threshold.
            allow_blank_query: If False, short-circuit blank queries to avoid meaningless retrievals.
        """
        if not query.strip() and not allow_blank_query:
            return []

        # Chroma expects a single top-level operator in `where`, so we build
        # simple conditions and combine them with $and when needed.
        conditions: List[Dict[str, Any]] = []
        if tickers:
            conditions.append({"ticker": {"$in": [t.lower() for t in tickers]}})
        if period:
            conditions.append({"period": period})

        if not conditions:
            where: Dict[str, Any] = {}
        elif len(conditions) == 1:
            where = conditions[0]
        else:
            where = {"$and": conditions}

        results = self._store.query(query_text=query, k=k, where=where)

        if min_similarity is None:
            return results

        filtered: List[Tuple[Chunk, float]] = []
        for chunk, distance in results:
            similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
            if similarity >= min_similarity:
                filtered.append((chunk, distance))
        return filtered



