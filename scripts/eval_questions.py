from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import requests


@dataclass
class EvalQuestion:
    question: str
    tickers: List[str]
    period: str


API_BASE = "http://localhost:8000"


def run_eval(questions: List[EvalQuestion]) -> None:
    for q in questions:
        payload = {
            "question": q.question,
            "tickers": q.tickers,
            "period": q.period,
            "top_k": 8,
        }
        resp = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        print("Question:", q.question)
        print("Answer:", data.get("answer", ""))
        print("Citations:")
        for c in data.get("citations", []):
            print(" ", c)
        print("-" * 80)


def main() -> None:
    questions = [
        EvalQuestion(
            question="Among Microsoft and Amazon which company had greater cloud revenues in Q4-2024?",
            tickers=["MSFT", "AMZN"],
            period="Q4-2024",
        )
    ]
    run_eval(questions)


if __name__ == "__main__":
    main()



