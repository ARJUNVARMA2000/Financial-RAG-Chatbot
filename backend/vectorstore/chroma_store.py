from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Set

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..ingestion.metadata_schema import Chunk


class ChromaVectorStore:
    def __init__(self, persist_directory: str, collection_name: str = "financial_docs") -> None:
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: Sequence[Chunk]) -> None:
        if not chunks:
            return
        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []
        for chunk in chunks:
            ids.append(chunk.chunk_id)
            texts.append(chunk.text)
            metadatas.append(chunk.metadata)
        self._collection.upsert(ids=ids, documents=texts, metadatas=metadatas)

    def query(
        self,
        query_text: str,
        k: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Chunk, float]]:
        result = self._collection.query(
            query_texts=[query_text],
            n_results=k,
            where=where or {},
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        chunks: List[Tuple[Chunk, float]] = []
        for doc_text, meta, dist in zip(documents, metadatas, distances):
            chunk = Chunk(
                chunk_id=str(meta.get("chunk_id", "")) if "chunk_id" in meta else "",
                text=doc_text,
                metadata=meta,
            )
            chunks.append((chunk, float(dist)))
        return chunks

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        if not chunk_id:
            return None
        result = self._collection.get(ids=[chunk_id])
        ids = result.get("ids") or []
        if not ids:
            return None
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []
        if not documents or not metadatas:
            return None
        text = documents[0]
        metadata = metadatas[0]
        return Chunk(
            chunk_id=chunk_id,
            text=text,
            metadata=metadata,
        )

    def get_all_metadata(self, ticker: Optional[str] = None, limit: int = 10000) -> List[Dict[str, Any]]:
        """
        Get metadata for all documents, optionally filtered by ticker.
        
        Args:
            ticker: Optional ticker to filter by (case-insensitive)
            limit: Maximum number of documents to retrieve (default 10000)
            
        Returns:
            List of metadata dictionaries
        """
        try:
            if ticker:
                # Try both uppercase and lowercase ticker
                # ChromaDB's $or operator for case-insensitive search
                where_clause = {
                    "$or": [
                        {"ticker": ticker.upper()},
                        {"ticker": ticker.lower()}
                    ]
                }
            else:
                where_clause = None
            
            # ChromaDB get() retrieves documents by metadata filter
            result = self._collection.get(
                where=where_clause,
                limit=limit,
                include=["metadatas"]
            )
            
            return result.get("metadatas", [])
        except Exception as e:
            print(f"Error getting metadata: {e}")
            return []

    def get_available_periods(self, ticker: str) -> List[str]:
        """
        Get all available periods for a specific ticker.
        
        Args:
            ticker: Ticker symbol (e.g., "NVDA")
            
        Returns:
            Sorted list of unique periods
        """
        metadatas = self.get_all_metadata(ticker=ticker)
        
        periods: Set[str] = set()
        for meta in metadatas:
            if "period" in meta and meta["period"]:
                periods.add(meta["period"])
        
        return sorted(list(periods))

    def get_all_tickers(self) -> List[str]:
        """
        Get all available tickers in the database.
        
        Returns:
            Sorted list of unique ticker symbols
        """
        metadatas = self.get_all_metadata()
        
        tickers: Set[str] = set()
        for meta in metadatas:
            if "ticker" in meta and meta["ticker"]:
                tickers.add(meta["ticker"].upper())
        
        return sorted(list(tickers))

    def get_ticker_period_map(self) -> Dict[str, List[str]]:
        """
        Get mapping of all tickers to their available periods.
        
        Returns:
            Dict like {"NVDA": ["Q1-2026", "Q2-2026"], "AMZN": ["Q1-2026", "Q2-2026", "Q3-2026"]}
        """
        metadatas = self.get_all_metadata()
        
        ticker_periods: Dict[str, Set[str]] = {}
        
        for meta in metadatas:
            ticker = meta.get("ticker", "").upper()
            period = meta.get("period", "")
            
            if ticker and period:
                if ticker not in ticker_periods:
                    ticker_periods[ticker] = set()
                ticker_periods[ticker].add(period)
        
        # Convert sets to sorted lists
        return {
            ticker: sorted(list(periods))
            for ticker, periods in sorted(ticker_periods.items())
        }

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dict with stats like total chunks, tickers, periods
        """
        ticker_period_map = self.get_ticker_period_map()
        
        total_chunks = self._collection.count()
        total_tickers = len(ticker_period_map)
        
        # Count total unique periods across all tickers
        all_periods: Set[str] = set()
        for periods in ticker_period_map.values():
            all_periods.update(periods)
        
        return {
            "total_chunks": total_chunks,
            "total_tickers": total_tickers,
            "total_periods": len(all_periods),
            "ticker_period_map": ticker_period_map,
        }
