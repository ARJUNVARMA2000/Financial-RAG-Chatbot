from __future__ import annotations

import argparse

from backend.app.config import get_settings
from .build_index import main as build_index_main


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex all configured tickers/periods.")
    parser.add_argument("--ticker", action="append", required=True, help="Ticker symbol, e.g., MSFT")
    parser.add_argument("--period", action="append", required=True, help="Period identifier, e.g., Q4-2024")
    args = parser.parse_args()

    # For simplicity, just loop over combinations and reuse build_index.
    for ticker in args.ticker:
        for period in args.period:
            build_index_main()


if __name__ == "__main__":
    main()



