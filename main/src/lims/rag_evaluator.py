"""RAG evaluation framework for LIMS ChromaDB collections.

Computes retrieval quality metrics:
- **Hit Rate@k**: Fraction of queries where the expected source appears in top-k
- **MRR** (Mean Reciprocal Rank): Average of 1/rank for the expected source
- **Precision@k**: Fraction of top-k results from the expected source

Ground truth is derived from demo_data/ where matching PDF+XLSX pairs share
a filename stem (e.g. ``AND_ACS_DYE-LAB-2499.pdf`` -> ``AND_ACS_DYE-LAB-2499.xlsx``).

NO FALLBACK LOGIC.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import chromadb

logger = logging.getLogger(__name__)


@dataclass
class EvalQuery:
    """A single ground-truth query for RAG evaluation."""

    query_text: str
    expected_source_file: str  # e.g. "AND_ACS_DYE-LAB-2499.xlsx"
    test_type: str = ""        # optional label


@dataclass
class EvalResult:
    """Result of evaluating a single query against retrieval."""

    query: EvalQuery
    hit: bool                   # expected source in top-k results
    reciprocal_rank: float      # 1/rank if hit, else 0.0
    precision_at_k: float       # fraction of top-k from expected source
    distances: list[float] = field(default_factory=list)
    retrieved_sources: list[str] = field(default_factory=list)


@dataclass
class EvalSummary:
    """Aggregate metrics across all evaluation queries."""

    total_queries: int
    hit_rate: float
    mrr: float
    mean_precision_at_k: float
    mean_distance: float
    results: list[EvalResult] = field(default_factory=list)
    top_k: int = 0

    def __str__(self) -> str:
        return (
            f"EvalSummary(top_k={self.top_k}, queries={self.total_queries}, "
            f"hit_rate={self.hit_rate:.3f}, mrr={self.mrr:.3f}, "
            f"precision@k={self.mean_precision_at_k:.3f}, "
            f"mean_dist={self.mean_distance:.4f})"
        )


class RAGEvaluator:
    """Evaluate retrieval quality of a ChromaDB collection.

    Args:
        chroma_path: Path to the ChromaDB persistent storage.
        collection_name: Name of the collection to evaluate.
    """

    def __init__(
        self,
        chroma_path: str = "./chroma_db_lims",
        collection_name: str = "mda_templates",
    ) -> None:
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        self._client = chromadb.PersistentClient(path=chroma_path)
        self._collection = self._client.get_or_create_collection(collection_name)

        doc_count = self._collection.count()
        if doc_count == 0:
            raise RuntimeError(
                f"ChromaDB collection '{collection_name}' is empty. "
                f"Seed it first before running evaluation."
            )
        logger.info(
            "RAGEvaluator: collection=%s docs=%d", collection_name, doc_count
        )

    def build_mda_eval_queries(
        self,
        demo_data_dir: str = "./demo_data",
    ) -> list[EvalQuery]:
        """Build evaluation queries from PDF+XLSX pairs in demo_data/.

        For each XLSX file, creates a query using the file stem as the
        query text (simulating a user searching for that template).
        The expected source is the XLSX filename.

        Args:
            demo_data_dir: Directory containing matched PDF+XLSX pairs.

        Returns:
            List of EvalQuery objects.

        Raises:
            FileNotFoundError: If demo_data_dir doesn't exist or has no XLSX.
        """
        demo_dir = Path(demo_data_dir)
        if not demo_dir.exists():
            raise FileNotFoundError(
                f"Demo data directory does not exist: {demo_dir.resolve()}"
            )

        xlsx_files = sorted(demo_dir.glob("*.xlsx"))
        if not xlsx_files:
            raise FileNotFoundError(
                f"No .xlsx files found in {demo_dir.resolve()}"
            )

        pdf_stems = {p.stem for p in demo_dir.glob("*.pdf")}

        queries: list[EvalQuery] = []
        for xlsx_path in xlsx_files:
            # Only include XLSX files that have a matching PDF
            if xlsx_path.stem in pdf_stems:
                # Build a realistic query from the filename
                # e.g. "AND_ACS_DYE-LAB-2499" -> "AND ACS DYE LAB 2499"
                query_text = xlsx_path.stem.replace("_", " ").replace("-", " ")
                queries.append(
                    EvalQuery(
                        query_text=query_text,
                        expected_source_file=xlsx_path.name,
                    )
                )

        logger.info(
            "Built %d eval queries from %d XLSX files (%d with matching PDFs)",
            len(queries),
            len(xlsx_files),
            len(queries),
        )
        return queries

    def evaluate(
        self,
        queries: list[EvalQuery],
        top_k: int = 3,
    ) -> EvalSummary:
        """Run all queries and compute aggregate metrics.

        Args:
            queries: List of ground-truth queries.
            top_k: Number of results to retrieve per query.

        Returns:
            EvalSummary with per-query results and aggregate metrics.
        """
        if not queries:
            raise ValueError("queries list must not be empty")

        results: list[EvalResult] = []

        for eq in queries:
            effective_k = min(top_k, self._collection.count())
            raw = self._collection.query(
                query_texts=[eq.query_text],
                n_results=effective_k,
                include=["metadatas", "distances"],
            )

            metadatas = raw.get("metadatas", [[]])[0]
            distances_raw = raw.get("distances", [[]])[0]

            distances = [float(d) for d in distances_raw]
            retrieved_sources = [
                str((m or {}).get("source_file", "UNKNOWN"))
                for m in metadatas
            ]

            # Compute metrics
            hit = eq.expected_source_file in retrieved_sources

            reciprocal_rank = 0.0
            if hit:
                rank = retrieved_sources.index(eq.expected_source_file) + 1
                reciprocal_rank = 1.0 / rank

            relevant_count = sum(
                1 for s in retrieved_sources if s == eq.expected_source_file
            )
            precision = relevant_count / len(retrieved_sources) if retrieved_sources else 0.0

            results.append(
                EvalResult(
                    query=eq,
                    hit=hit,
                    reciprocal_rank=reciprocal_rank,
                    precision_at_k=precision,
                    distances=distances,
                    retrieved_sources=retrieved_sources,
                )
            )

        # Aggregate
        total = len(results)
        hit_rate = sum(1 for r in results if r.hit) / total
        mrr = sum(r.reciprocal_rank for r in results) / total
        mean_precision = sum(r.precision_at_k for r in results) / total

        all_distances = [d for r in results for d in r.distances]
        mean_distance = (
            sum(all_distances) / len(all_distances) if all_distances else 0.0
        )

        summary = EvalSummary(
            total_queries=total,
            hit_rate=hit_rate,
            mrr=mrr,
            mean_precision_at_k=mean_precision,
            mean_distance=mean_distance,
            results=results,
            top_k=top_k,
        )

        logger.info("Evaluation complete: %s", summary)
        return summary

    def evaluate_with_sweep(
        self,
        queries: list[EvalQuery],
        top_k_values: list[int] | None = None,
    ) -> dict[int, EvalSummary]:
        """Run evaluation for multiple top_k values.

        Args:
            queries: List of ground-truth queries.
            top_k_values: List of k values to sweep. Defaults to [1, 3, 5, 10].

        Returns:
            Dict mapping top_k -> EvalSummary.
        """
        if top_k_values is None:
            top_k_values = [1, 3, 5, 10]

        sweep_results: dict[int, EvalSummary] = {}
        for k in top_k_values:
            logger.info("Sweep: evaluating top_k=%d", k)
            sweep_results[k] = self.evaluate(queries, top_k=k)

        return sweep_results

    def log_to_langfuse(
        self,
        summary: EvalSummary,
        experiment_name: str = "rag-eval",
    ) -> None:
        """Log evaluation scores to Langfuse dashboard.

        Args:
            summary: Evaluation results to log.
            experiment_name: Name prefix for the Langfuse trace.
        """
        from main.src.lims.langfuse_tracing import get_lims_langfuse

        langfuse = get_lims_langfuse()
        if langfuse is None:
            logger.warning(
                "Langfuse not configured -- skipping evaluation logging"
            )
            return

        span = langfuse.start_span(
            name=f"{experiment_name}-top_k_{summary.top_k}",
            input={
                "collection": self.collection_name,
                "top_k": summary.top_k,
                "total_queries": summary.total_queries,
            },
            output={
                "hit_rate": summary.hit_rate,
                "mrr": summary.mrr,
                "mean_precision_at_k": summary.mean_precision_at_k,
                "mean_distance": summary.mean_distance,
            },
        )

        # Log individual scores
        span.score(name="hit_rate", value=summary.hit_rate)
        span.score(name="mrr", value=summary.mrr)
        span.score(name="precision_at_k", value=summary.mean_precision_at_k)
        span.score(name="mean_distance", value=summary.mean_distance)

        # Log misses for debugging
        misses = [r for r in summary.results if not r.hit]
        if misses:
            miss_details = [
                {
                    "query": r.query.query_text,
                    "expected": r.query.expected_source_file,
                    "retrieved": r.retrieved_sources[:3],
                }
                for r in misses
            ]
            span.update(
                metadata={"misses": miss_details},
            )

        span.end()
        langfuse.flush()
        logger.info(
            "Logged evaluation to Langfuse: %s (hit_rate=%.3f, mrr=%.3f)",
            experiment_name,
            summary.hit_rate,
            summary.mrr,
        )
