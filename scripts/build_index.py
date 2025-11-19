from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

# Ensure we're using absolute paths
import os

from backend.app.config import get_settings
from backend.app.dependencies import get_openai_client
from backend.ingestion.metadata_schema import Document
from backend.ingestion.parsers.html_parser import parse_html_to_document
from backend.ingestion.parsers.pdf_parser import parse_pdf_to_document
from backend.ingestion.parsers.text_normalizer import tag_sections
from backend.ingestion.index_builder import index_documents


def load_documents_for_ticker(ticker: str, period: str) -> List[Document]:
    settings = get_settings()
    # Resolve to absolute path to avoid working directory issues
    raw_dir = settings.raw_dir.resolve() / ticker.lower()
    print(f"Looking for documents in: {raw_dir}")
    print(f"Directory exists: {raw_dir.exists()}")
    
    if not raw_dir.exists():
        print(f"WARNING: Directory {raw_dir} does not exist!")
        print(f"Checking parent: {settings.raw_dir}")
        print(f"Parent exists: {settings.raw_dir.exists()}")
        if settings.raw_dir.exists():
            print(f"Contents of {settings.raw_dir}:")
            for item in settings.raw_dir.iterdir():
                print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
        return []
    
    # List all files first
    all_files = list(raw_dir.iterdir())
    print(f"All files in directory: {len(all_files)}")
    for f in all_files:
        print(f"  - {f.name} (is_file: {f.is_file()}, suffix: {f.suffix})")
    
    docs: List[Document] = []

    pdf_files = list(raw_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files via glob")
    for path in pdf_files:
        print(f"  Parsing: {path.name}")
        try:
            doc = parse_pdf_to_document(
                path,
                doc_id=f"{ticker}_{period}_{path.stem}",
                ticker=ticker,
                filing_type="pdf",
                period=period,
                source_url=None,
                title=path.stem,
            )
            tag_sections(doc.blocks)
            print(f"    Created document with {len(doc.blocks)} blocks")
            docs.append(doc)
        except Exception as e:
            print(f"    ERROR parsing {path.name}: {e}")
            import traceback
            traceback.print_exc()

    html_files = list(raw_dir.glob("*.html"))
    print(f"Found {len(html_files)} HTML files")
    for path in html_files:
        print(f"  Parsing: {path.name}")
        try:
            doc = parse_html_to_document(
                path,
                doc_id=f"{ticker}_{period}_{path.stem}",
                ticker=ticker,
                filing_type="html",
                period=period,
                source_url=None,
                title=path.stem,
            )
            tag_sections(doc.blocks)
            print(f"    Created document with {len(doc.blocks)} blocks")
            docs.append(doc)
        except Exception as e:
            print(f"    ERROR parsing {path.name}: {e}")
            import traceback
            traceback.print_exc()

    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build vector index for financial documents.")
    parser.add_argument("--ticker", action="append", required=True, help="Ticker symbol, e.g., MSFT")
    parser.add_argument("--period", required=True, help="Period identifier, e.g., Q4-2024")
    args = parser.parse_args()

    print(f"Building index for tickers: {args.ticker}, period: {args.period}")
    
    all_docs: List[Document] = []
    for ticker in args.ticker:
        docs = load_documents_for_ticker(ticker, args.period)
        print(f"Loaded {len(docs)} documents for {ticker}")
        all_docs.extend(docs)

    if not all_docs:
        print("ERROR: No documents found! Check that PDF/HTML files exist in data/raw/<ticker>/")
        return

    print(f"Total documents to index: {len(all_docs)}")
    
    settings = get_settings()
    openai_client = get_openai_client()

    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    print(f"Indexing to: {settings.chroma_persist_dir}")
    
    try:
        index_documents(all_docs, openai_client=openai_client, persist_dir=settings.chroma_persist_dir)
        print("Indexing completed successfully!")
    except Exception as e:
        print(f"ERROR during indexing: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    print("Starting build_index.py...", flush=True)
    main()
    print("build_index.py finished.", flush=True)



