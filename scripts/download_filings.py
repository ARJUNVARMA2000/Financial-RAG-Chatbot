from __future__ import annotations

import argparse
from pathlib import Path

from backend.app.config import get_settings
from backend.ingestion.sources.edgar_client import download_edgar_filings_for_urls
from backend.ingestion.sources.ir_client import download_ir_documents_for_urls


def main() -> None:
    parser = argparse.ArgumentParser(description="Download filings/IR documents for a company.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g., MSFT")
    parser.add_argument(
        "--edgar-url",
        action="append",
        default=[],
        help="EDGAR document URL (can be specified multiple times).",
    )
    parser.add_argument(
        "--ir-url",
        action="append",
        default=[],
        help="Investor relations document URL (can be specified multiple times).",
    )
    args = parser.parse_args()

    settings = get_settings()
    raw_root = settings.raw_dir

    if args.edgar_url:
        download_edgar_filings_for_urls(args.edgar_url, args.ticker, raw_root, prefix="edgar")
    if args.ir_url:
        download_ir_documents_for_urls(args.ir_url, args.ticker, raw_root, prefix="ir")


if __name__ == "__main__":
    main()



