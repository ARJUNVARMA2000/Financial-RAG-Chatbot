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
    ) -> List[Tuple[Chunk, float]]:
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
        return results



