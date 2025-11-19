from __future__ import annotations

from typing import List, Tuple

from ...ingestion.metadata_schema import Chunk


def rerank_by_distance(chunks_with_scores: List[Tuple[Chunk, float]]) -> List[Tuple[Chunk, float]]:
    """
    Simple reranker that sorts by ascending distance (higher similarity first).
    More advanced reranking (recency, source type) can be layered here later.
    """
    return sorted(chunks_with_scores, key=lambda cs: cs[1])



