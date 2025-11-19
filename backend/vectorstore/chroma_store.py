from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

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



