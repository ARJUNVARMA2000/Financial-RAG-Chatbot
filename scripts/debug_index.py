from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.config import get_settings
from backend.vectorstore.chroma_store import ChromaVectorStore


def main() -> None:
    settings = get_settings()
    store = ChromaVectorStore(persist_directory=str(settings.chroma_persist_dir))
    
    # Check total count
    collection = store._collection
    count = collection.count()
    print(f"Total chunks in collection: {count}")
    
    if count == 0:
        print("ERROR: No chunks found in the index!")
        print("You need to run: python scripts/build_index.py --ticker AMZN --period Q3-2025")
        return
    
    # Get a sample of chunks
    sample = collection.get(limit=5)
    print(f"\nSample chunk IDs: {sample['ids'][:5]}")
    print(f"\nSample metadata keys: {list(sample['metadatas'][0].keys()) if sample['metadatas'] else 'None'}")
    
    # Check for AMZN Q3-2025 chunks
    amzn_chunks = collection.get(
        where={"$and": [{"ticker": "amzn"}, {"period": "Q3-2025"}]},
        limit=5
    )
    print(f"\nAMZN Q3-2025 chunks found: {len(amzn_chunks['ids'])}")
    
    # Test a query
    print("\nTesting query: 'What were Amazon's total net sales in Q3 2025?'")
    results = store.query(
        query_text="What were Amazon's total net sales in Q3 2025?",
        k=5,
        where={"$and": [{"ticker": "amzn"}, {"period": "Q3-2025"}]}
    )
    print(f"Retrieved {len(results)} chunks")
    for i, (chunk, score) in enumerate(results[:3], 1):
        print(f"\n--- Chunk {i} (score: {score:.4f}) ---")
        print(f"Text preview: {chunk.text[:200]}...")
        print(f"Metadata: ticker={chunk.metadata.get('ticker')}, period={chunk.metadata.get('period')}")


if __name__ == "__main__":
    main()

