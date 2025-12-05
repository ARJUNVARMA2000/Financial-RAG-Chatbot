"""
Multi-model evaluation pipeline for RAG system.

This script runs evaluation questions against multiple LLMs via OpenRouter,
uses Claude Opus to judge answer correctness, and generates a comparison report.

Usage:
    python scripts/run_eval.py --csv data/eval/questions.csv --models all
    python scripts/run_eval.py --csv data/eval/questions.csv --models claude-sonnet,gpt-4o
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import time

import requests
from tqdm import tqdm

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.models_registry import EVAL_MODELS, get_all_model_names, get_model_id
from backend.app.services.eval_judge import EvalJudge, get_eval_judge


API_BASE = "http://localhost:8000"


@dataclass
class EvalQuestion:
    """A question with expected answer for evaluation."""
    question: str
    expected_answer: str
    tickers: List[str]
    period: str


@dataclass
class ModelResult:
    """Result for a single model's answer to a question."""
    model: str
    question: str
    expected_answer: str
    actual_answer: str
    is_correct: bool
    input_tokens: int
    output_tokens: int
    cost: float
    judge_input_tokens: int = 0
    judge_output_tokens: int = 0
    judge_cost: float = 0.0
    latency_ms: float = 0.0


@dataclass
class ModelSummary:
    """Aggregated results for a single model across all questions."""
    model: str
    total_questions: int = 0
    correct: int = 0
    accuracy: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    judge_input_tokens: int = 0
    judge_output_tokens: int = 0
    judge_cost: float = 0.0
    total_latency_ms: float = 0.0


@dataclass
class EvalResults:
    """Complete evaluation results."""
    timestamp: str
    models_evaluated: List[str]
    total_questions: int
    results: List[ModelResult] = field(default_factory=list)
    summaries: List[ModelSummary] = field(default_factory=list)


def load_questions_from_csv(csv_path: str) -> List[EvalQuestion]:
    """Load evaluation questions from a CSV file."""
    questions = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse tickers - can be comma-separated or JSON array
            tickers_raw = row.get("tickers", "")
            if tickers_raw.startswith("["):
                tickers = json.loads(tickers_raw)
            else:
                tickers = [t.strip() for t in tickers_raw.split(",") if t.strip()]

            questions.append(EvalQuestion(
                question=row["question"],
                expected_answer=row["expected_answer"],
                tickers=tickers,
                period=row.get("period", ""),
            ))
    return questions


def call_rag_api(
    question: str,
    tickers: List[str],
    period: str,
    model: str,
    top_k: int = 8,
) -> dict:
    """Call the RAG API with a specific model."""
    payload = {
        "question": question,
        "tickers": tickers,
        "period": period,
        "top_k": top_k,
        "model": model,
    }
    resp = requests.post(f"{API_BASE}/chat", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def run_evaluation(
    questions: List[EvalQuestion],
    models: List[str],
    judge: EvalJudge,
) -> EvalResults:
    """Run evaluation for all questions across all models."""
    results = EvalResults(
        timestamp=datetime.now().isoformat(),
        models_evaluated=models,
        total_questions=len(questions),
    )

    # Initialize summaries for each model
    model_summaries = {model: ModelSummary(model=model) for model in models}

    total_iterations = len(questions) * len(models)
    with tqdm(total=total_iterations, desc="Evaluating") as pbar:
        for q in questions:
            for model_name in models:
                pbar.set_description(f"Eval: {model_name[:20]}")

                try:
                    start_ts = time.perf_counter()
                    # Get model response via RAG API
                    response = call_rag_api(
                        question=q.question,
                        tickers=q.tickers,
                        period=q.period,
                        model=model_name,
                    )
                    latency_ms = (time.perf_counter() - start_ts) * 1000

                    actual_answer = response.get("answer", "")
                    usage = response.get("usage", {}) or {}
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    cost = usage.get("cost", 0.0)

                    # Judge the answer
                    judgment = judge.judge_answer(
                        question=q.question,
                        expected_answer=q.expected_answer,
                        actual_answer=actual_answer,
                    )

                    result = ModelResult(
                        model=model_name,
                        question=q.question,
                        expected_answer=q.expected_answer,
                        actual_answer=actual_answer,
                        is_correct=judgment.is_correct,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        cost=cost,
                        judge_input_tokens=judgment.input_tokens,
                        judge_output_tokens=judgment.output_tokens,
                        judge_cost=judgment.cost,
                        latency_ms=latency_ms,
                    )
                    results.results.append(result)

                    # Update summary
                    summary = model_summaries[model_name]
                    summary.total_questions += 1
                    if judgment.is_correct:
                        summary.correct += 1
                    summary.total_input_tokens += input_tokens
                    summary.total_output_tokens += output_tokens
                    summary.total_cost += cost
                    summary.judge_input_tokens += judgment.input_tokens
                    summary.judge_output_tokens += judgment.output_tokens
                    summary.judge_cost += judgment.cost
                    summary.total_latency_ms += latency_ms

                except Exception as e:
                    print(f"\nError evaluating {model_name} on question: {q.question[:50]}...")
                    print(f"Error: {e}")
                    # Record as failed
                    result = ModelResult(
                        model=model_name,
                        question=q.question,
                        expected_answer=q.expected_answer,
                        actual_answer=f"ERROR: {e}",
                        is_correct=False,
                        input_tokens=0,
                        output_tokens=0,
                        cost=0.0,
                        latency_ms=0.0,
                    )
                    results.results.append(result)
                    model_summaries[model_name].total_questions += 1

                pbar.update(1)

    # Calculate accuracies and finalize summaries
    for model_name, summary in model_summaries.items():
        if summary.total_questions > 0:
            summary.accuracy = summary.correct / summary.total_questions
        results.summaries.append(summary)

    return results


def save_results(results: EvalResults, output_dir: str) -> tuple[str, str]:
    """Save evaluation results to CSV and JSON files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save detailed results CSV
    detailed_path = output_path / f"eval_detailed_{timestamp}.csv"
    with open(detailed_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model", "question", "expected_answer", "actual_answer", "is_correct",
            "input_tokens", "output_tokens", "cost",
            "judge_input_tokens", "judge_output_tokens", "judge_cost", "latency_ms"
        ])
        for r in results.results:
            writer.writerow([
                r.model, r.question, r.expected_answer, r.actual_answer, r.is_correct,
                r.input_tokens, r.output_tokens, r.cost,
                r.judge_input_tokens, r.judge_output_tokens, r.judge_cost, f"{r.latency_ms:.1f}"
            ])

    # Save summary results CSV
    summary_path = output_path / f"eval_summary_{timestamp}.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "model", "total_questions", "correct", "accuracy",
            "total_input_tokens", "total_output_tokens", "total_cost",
            "judge_input_tokens", "judge_output_tokens", "judge_cost", "avg_latency_ms"
        ])
        for s in results.summaries:
            avg_latency = (s.total_latency_ms / s.total_questions) if s.total_questions else 0.0
            writer.writerow([
                s.model, s.total_questions, s.correct, f"{s.accuracy:.2%}",
                s.total_input_tokens, s.total_output_tokens, f"${s.total_cost:.4f}",
                s.judge_input_tokens, s.judge_output_tokens, f"${s.judge_cost:.4f}",
                f"{avg_latency:.1f}"
            ])

    return str(detailed_path), str(summary_path)


def print_summary(results: EvalResults) -> None:
    """Print a summary table of results."""
    print("\n" + "=" * 100)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 100)
    print(f"Timestamp: {results.timestamp}")
    print(f"Total Questions: {results.total_questions}")
    print(f"Models Evaluated: {', '.join(results.models_evaluated)}")
    print("-" * 100)

    # Table header
    print(f"{'Model':<25} {'Questions':>10} {'Correct':>10} {'Accuracy':>10} "
          f"{'In Tokens':>12} {'Out Tokens':>12} {'Cost':>10} {'Avg ms':>10}")
    print("-" * 100)

    # Sort by accuracy descending
    sorted_summaries = sorted(results.summaries, key=lambda x: x.accuracy, reverse=True)

    for s in sorted_summaries:
        avg_latency = (s.total_latency_ms / s.total_questions) if s.total_questions else 0.0
        print(f"{s.model:<25} {s.total_questions:>10} {s.correct:>10} {s.accuracy:>9.1%} "
              f"{s.total_input_tokens:>12,} {s.total_output_tokens:>12,} ${s.total_cost:>9.4f} {avg_latency:>9.1f}")

    print("=" * 100)

    # Total judge costs
    total_judge_cost = sum(s.judge_cost for s in results.summaries)
    print(f"Total Judge (Claude Opus) Cost: ${total_judge_cost:.4f}")
    print("=" * 100)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run multi-model evaluation on RAG system")
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to CSV file with evaluation questions",
    )
    parser.add_argument(
        "--models",
        type=str,
        default="all",
        help="Comma-separated list of models or 'all' for all models",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/eval/results",
        help="Output directory for results",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default="http://localhost:8000",
        help="Base URL for the RAG API",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit of questions to run for a quick regression (0 = all)",
    )

    args = parser.parse_args()

    global API_BASE
    API_BASE = args.api_base

    # Parse models
    if args.models.lower() == "all":
        models = get_all_model_names()
    else:
        models = [m.strip() for m in args.models.split(",")]
        # Validate models
        for model in models:
            try:
                get_model_id(model)
            except ValueError as e:
                print(f"Error: {e}")
                sys.exit(1)

    print(f"Loading questions from: {args.csv}")
    questions = load_questions_from_csv(args.csv)
    if args.limit and args.limit > 0:
        questions = questions[: args.limit]
    print(f"Loaded {len(questions)} questions")

    print(f"Models to evaluate: {', '.join(models)}")
    print(f"Total evaluations: {len(questions) * len(models)}")

    # Initialize judge
    print("Initializing Claude Opus judge...")
    judge = get_eval_judge()

    # Run evaluation
    print("\nStarting evaluation...")
    results = run_evaluation(questions, models, judge)

    # Save results
    detailed_path, summary_path = save_results(results, args.output)
    print(f"\nDetailed results saved to: {detailed_path}")
    print(f"Summary results saved to: {summary_path}")

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()

