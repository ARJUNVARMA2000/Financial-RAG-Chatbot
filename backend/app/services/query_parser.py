"""Query parser service for extracting entities from natural language queries."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import List, Optional, Tuple

from ..dependencies import get_openai_client
from ..openai_client import OpenAIClient


EXTRACTION_PROMPT = """You are an entity extraction assistant for a financial RAG system.
Extract stock ticker symbols and time periods from the user's question.

Rules:
1. Tickers: Extract company stock symbols (e.g., AMZN, AAPL, GOOGL, MSFT). 
   - If a company name is mentioned (e.g., "Amazon"), convert to ticker (AMZN).
   - Return as uppercase list, or null if no company is mentioned.

2. Period: Extract fiscal quarter and year in format "Q#-YYYY" (e.g., "Q3-2025").
   - "last quarter" or "most recent quarter" -> use CURRENT_QUARTER
   - "Q3 2025" or "third quarter 2025" -> "Q3-2025"
   - Return null if no period is mentioned.

3. needs_clarification: Set to true if:
   - Multiple companies could be inferred but unclear which one
   - Time period is ambiguous (e.g., "recently" without specifics)
   - The question is too vague to determine what data is needed

4. clarification_message: If needs_clarification is true, provide a helpful message
   asking the user to specify what's missing.

Current date for reference: CURRENT_DATE

Respond ONLY with valid JSON in this exact format:
{
  "tickers": ["AMZN"] or null,
  "period": "Q3-2025" or null,
  "needs_clarification": false,
  "clarification_message": null or "Please specify..."
}"""


def _get_current_quarter() -> str:
    """Get the current fiscal quarter in Q#-YYYY format."""
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    return f"Q{quarter}-{now.year}"


def _resolve_relative_period(period: Optional[str]) -> Optional[str]:
    """Resolve relative period references like 'last quarter'."""
    if period == "CURRENT_QUARTER":
        return _get_current_quarter()
    return period


_PERIOD_REGEX = re.compile(r"q([1-4])[-\s]?(\d{4})", re.IGNORECASE)
_TICKER_REGEX = re.compile(r"\b([A-Z]{1,5})(?=\b)")


def _extract_json_block(text: str) -> Optional[str]:
    """Try to pull the first JSON object from a string."""
    # Prefer fenced json code blocks
    fenced = re.search(r"```json\s*({.*?})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1)

    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if match:
        return match.group()
    return None


def _fallback_parse(question: str) -> tuple[Optional[List[str]], Optional[str]]:
    """
    Heuristic extraction when LLM JSON parse fails:
    - Tickers: uppercase 1-5 letters, deduped.
    - Periods: Q# YYYY -> Q#-YYYY.
    """
    tickers: List[str] = []
    for symbol in _TICKER_REGEX.findall(question.upper()):
        # Skip common words that match the regex accidentally
        if symbol in {"THE", "AND", "FOR", "WITH", "THIS", "THAT"}:
            continue
        tickers.append(symbol)

    period_match = _PERIOD_REGEX.search(question)
    period = None
    if period_match:
        period = f"Q{period_match.group(1)}-{period_match.group(2)}"

    deduped_tickers = list(dict.fromkeys(tickers)) or None
    return deduped_tickers, period


class QueryParser:
    """Parses user queries to extract ticker symbols and time periods."""

    def __init__(self, openai_client: Optional[OpenAIClient] = None) -> None:
        self._openai = openai_client or get_openai_client()

    def parse(self, question: str) -> Tuple[Optional[List[str]], Optional[str], bool, Optional[str]]:
        """
        Parse a question to extract entities.

        Returns:
            Tuple of (tickers, period, needs_clarification, clarification_message)
        """
        current_date = datetime.now().strftime("%B %d, %Y")
        current_quarter = _get_current_quarter()

        prompt = EXTRACTION_PROMPT.replace("CURRENT_DATE", current_date).replace(
            "CURRENT_QUARTER", current_quarter
        )

        try:
            response = self._openai.chat(system_prompt=prompt, user_message=question)
            json_block = _extract_json_block(response) or response
            data = json.loads(json_block)

            tickers = data.get("tickers")
            period = data.get("period")
            needs_clarification = data.get("needs_clarification", False)
            clarification_message = data.get("clarification_message")

            # Normalize tickers to uppercase
            if tickers:
                tickers = [t.upper() for t in tickers]

            # Resolve relative periods
            period = _resolve_relative_period(period)

            # If the LLM gave us nothing, fall back to heuristics
            if not tickers or not period:
                fallback_tickers, fallback_period = _fallback_parse(question)
                if not tickers:
                    tickers = fallback_tickers
                if not period:
                    period = fallback_period

            # If still missing, mark for clarification
            if not tickers or not period:
                needs_clarification = True
                clarification_message = clarification_message or (
                    "Please specify the company ticker and fiscal period (e.g., AMZN, Q3-2025)."
                )

            return tickers, period, needs_clarification, clarification_message

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            # If parsing fails, return needs_clarification
            return (
                None,
                None,
                True,
                "I couldn't understand your query. Please specify the company ticker and time period.",
            )


def get_query_parser() -> QueryParser:
    """Factory function to create a QueryParser instance."""
    return QueryParser(openai_client=get_openai_client())

