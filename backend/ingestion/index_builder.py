from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from tqdm import tqdm

from ..app.openai_client import OpenAIClient
from .chunking import chunk_document, ChunkingConfig
from .metadata_schema import Chunk, Document
from ..vectorstore.chroma_store import ChromaVectorStore


def build_chunks_for_documents(documents: Iterable[Document]) -> List[Chunk]:
    """Build chunks from documents using the default chunking configuration."""
    # Create chunking config with default values
    config = ChunkingConfig(
        max_tokens=800,
        overlap_tokens=200,
        min_chunk_size=100,
        max_block_tokens=500,
        keep_tables_intact=True,
        keep_charts_intact=True,
        add_document_context=True,
        add_section_headers=True,
        use_semantic_boundaries=True,
    )
    
    chunks: List[Chunk] = []
    for doc in documents:
        doc_chunks = chunk_document(doc, config)
        for ch in doc_chunks:
            # Add chunk_id into metadata for easier round-tripping
            ch.metadata["chunk_id"] = ch.chunk_id
        chunks.extend(doc_chunks)
    return chunks


def index_documents(
    documents: Iterable[Document],
    *,
    openai_client: OpenAIClient,
    persist_dir: Path,
    collection_name: str = "financial_docs",
) -> None:
    vector_store = ChromaVectorStore(persist_directory=str(persist_dir), collection_name=collection_name)
    chunks = build_chunks_for_documents(documents)
    
    print(f"Created {len(chunks)} chunks from documents")

    if not chunks:
        print("WARNING: No chunks created! Check document parsing.")
        return

    # Embed in batches to avoid very large requests
    batch_size = 64
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    print(f"Indexing {len(chunks)} chunks in {total_batches} batches...")
    
    for i in tqdm(range(0, len(chunks), batch_size), desc="Indexing chunks"):
        batch = chunks[i : i + batch_size]
        try:
            embeddings = openai_client.embed_texts([c.text for c in batch])
            # Chroma can accept embeddings directly, but to keep things simple and
            # avoid tight coupling we store only texts + metadata and let Chroma
            # do its own embedding if configured. For now, we ignore embeddings.
            vector_store.upsert(batch)
        except Exception as e:
            print(f"ERROR in batch {i//batch_size + 1}: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # Verify storage
    collection = vector_store._collection
    stored_count = collection.count()
    print(f"Verification: {stored_count} chunks stored in vector database")

# from __future__ import annotations

# from pathlib import Path
# from typing import Iterable, List

# from tqdm import tqdm

# from ..app.openai_client import OpenAIClient
# from .chunking import chunk_document
# from .metadata_schema import Chunk, Document
# from ..vectorstore.chroma_store import ChromaVectorStore


# def build_chunks_for_documents(documents: Iterable[Document]) -> List[Chunk]:
#     chunks: List[Chunk] = []
#     for doc in documents:
#         doc_chunks = chunk_document(doc)
#         for ch in doc_chunks:
#             # Add chunk_id into metadata for easier round-tripping
#             ch.metadata["chunk_id"] = ch.chunk_id
#         chunks.extend(doc_chunks)
#     return chunks


# def index_documents(
#     documents: Iterable[Document],
#     *,
#     openai_client: OpenAIClient,
#     persist_dir: Path,
#     collection_name: str = "financial_docs",
# ) -> None:
#     vector_store = ChromaVectorStore(persist_directory=str(persist_dir), collection_name=collection_name)
#     chunks = build_chunks_for_documents(documents)
    
#     print(f"Created {len(chunks)} chunks from documents")

#     if not chunks:
#         print("WARNING: No chunks created! Check document parsing.")
#         return

#     # Embed in batches to avoid very large requests
#     batch_size = 64
#     total_batches = (len(chunks) + batch_size - 1) // batch_size
#     print(f"Indexing {len(chunks)} chunks in {total_batches} batches...")
    
#     for i in tqdm(range(0, len(chunks), batch_size), desc="Indexing chunks"):
#         batch = chunks[i : i + batch_size]
#         try:
#             embeddings = openai_client.embed_texts([c.text for c in batch])
#             # Chroma can accept embeddings directly, but to keep things simple and
#             # avoid tight coupling we store only texts + metadata and let Chroma
#             # do its own embedding if configured. For now, we ignore embeddings.
#             vector_store.upsert(batch)
#         except Exception as e:
#             print(f"ERROR in batch {i//batch_size + 1}: {e}")
#             import traceback
#             traceback.print_exc()
#             raise
    
#     # Verify storage
#     collection = vector_store._collection
#     stored_count = collection.count()
#     print(f"Verification: {stored_count} chunks stored in vector database")



