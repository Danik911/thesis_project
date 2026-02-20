#!/usr/bin/env python3
"""CLI runner for RAG evaluation of LIMS ChromaDB collections.

Usage:
    python scripts/evaluate_rag.py
    python scripts/evaluate_rag.py --collection mda_templates --top-k 3,5,10
    python scripts/evaluate_rag.py --langfuse     # log scores to Langfuse
    python scripts/evaluate_rag.py --sweep         # full top_k parameter sweep

NO FALLBACK LOGIC: fails explicitly if collection is empty or files missing.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main.src.lims.rag_evaluator import RAGEvaluator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def print_summary_table(summary, collection_name: str) -> None:
    """Print evaluation results in a formatted table."""
    print(f"\n{'=' * 70}")  # noqa: T201
    print(f"  RAG Evaluation: {collection_name} (top_k={summary.top_k})")  # noqa: T201
    print(f"{'=' * 70}")  # noqa: T201
    print(f"  Queries:          {summary.total_queries}")  # noqa: T201
    print(f"  Hit Rate@k:       {summary.hit_rate:.3f}")  # noqa: T201
    print(f"  MRR:              {summary.mrr:.3f}")  # noqa: T201
    print(f"  Precision@k:      {summary.mean_precision_at_k:.3f}")  # noqa: T201
    print(f"  Mean Distance:    {summary.mean_distance:.4f}")  # noqa: T201
    print(f"{'=' * 70}")  # noqa: T201

    # Show misses
    misses = [r for r in summary.results if not r.hit]
    if misses:
        print(f"\n  MISSES ({len(misses)}):")  # noqa: T201
        for r in misses:
            print(f"    Query:    {r.query.query_text[:60]}")  # noqa: T201
            print(f"    Expected: {r.query.expected_source_file}")  # noqa: T201
            print(f"    Got:      {r.retrieved_sources[:3]}")  # noqa: T201
            print()  # noqa: T201
    else:
        print("\n  All queries hit! No misses.")  # noqa: T201

    print()  # noqa: T201


def print_sweep_table(sweep_results: dict, collection_name: str) -> None:
    """Print parameter sweep results as a compact table."""
    print(f"\n{'=' * 70}")  # noqa: T201
    print(f"  Parameter Sweep: {collection_name}")  # noqa: T201
    print(f"{'=' * 70}")  # noqa: T201
    print(f"  {'top_k':>6} | {'Hit Rate':>10} | {'MRR':>8} | {'Prec@k':>8} | {'Mean Dist':>10}")  # noqa: T201
    print(f"  {'-' * 6} | {'-' * 10} | {'-' * 8} | {'-' * 8} | {'-' * 10}")  # noqa: T201
    for k in sorted(sweep_results.keys()):
        s = sweep_results[k]
        print(  # noqa: T201
            f"  {k:>6} | {s.hit_rate:>10.3f} | {s.mrr:>8.3f} | "
            f"{s.mean_precision_at_k:>8.3f} | {s.mean_distance:>10.4f}"
        )
    print(f"{'=' * 70}\n")  # noqa: T201


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate RAG retrieval quality for LIMS ChromaDB collections"
    )
    parser.add_argument(
        "--collection",
        default="mda_templates",
        help="ChromaDB collection name (default: mda_templates)",
    )
    parser.add_argument(
        "--chroma-path",
        default="./chroma_db_lims",
        help="Path to ChromaDB storage (default: ./chroma_db_lims)",
    )
    parser.add_argument(
        "--demo-data",
        default="./demo_data",
        help="Path to demo data directory (default: ./demo_data)",
    )
    parser.add_argument(
        "--top-k",
        default="3",
        help="Comma-separated top_k values (default: 3)",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Run full parameter sweep (top_k=1,3,5,10)",
    )
    parser.add_argument(
        "--langfuse",
        action="store_true",
        help="Log evaluation scores to Langfuse dashboard",
    )

    args = parser.parse_args()

    evaluator = RAGEvaluator(
        chroma_path=args.chroma_path,
        collection_name=args.collection,
    )

    queries = evaluator.build_mda_eval_queries(demo_data_dir=args.demo_data)

    if args.sweep:
        sweep_results = evaluator.evaluate_with_sweep(queries)
        print_sweep_table(sweep_results, args.collection)

        if args.langfuse:
            for k, summary in sweep_results.items():
                evaluator.log_to_langfuse(summary, experiment_name="rag-eval-sweep")
            print("Scores logged to Langfuse.")  # noqa: T201
    else:
        top_k_values = [int(x.strip()) for x in args.top_k.split(",")]
        for k in top_k_values:
            summary = evaluator.evaluate(queries, top_k=k)
            print_summary_table(summary, args.collection)

            if args.langfuse:
                evaluator.log_to_langfuse(summary)
                print(f"Scores for top_k={k} logged to Langfuse.")  # noqa: T201


if __name__ == "__main__":
    main()
