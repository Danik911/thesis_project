#!/usr/bin/env python3
"""
Simple integration test for Task 16 dataset without complex imports
"""

import json
from pathlib import Path


def test_dataset_cv_compatibility():
    """Test that dataset is compatible with cross-validation framework expectations."""
    print("Testing Dataset Cross-Validation Compatibility")
    print("=" * 50)

    try:
        # Load fold assignments
        fold_file = Path("datasets/cross_validation/fold_assignments.json")
        with open(fold_file, encoding="utf-8") as f:
            fold_data = json.load(f)

        print("PASS: Fold assignments loaded successfully")

        # Check structure compatibility with FoldManager expectations
        required_keys = ["metadata", "document_inventory", "folds", "validation_summary"]
        for key in required_keys:
            if key not in fold_data:
                raise ValueError(f"Missing required key: {key}")

        print("PASS: Required manifest structure present")

        # Test document loading
        urs_corpus_path = Path("datasets/urs_corpus")
        document_count = 0
        loaded_docs = {}

        for doc_id in fold_data["document_inventory"]:
            # Find document file
            doc_found = False
            for category_dir in urs_corpus_path.iterdir():
                if not category_dir.is_dir():
                    continue

                doc_path = category_dir / f"{doc_id}.md"
                if doc_path.exists():
                    # Load content
                    content = doc_path.read_text(encoding="utf-8")
                    loaded_docs[doc_id] = {
                        "path": str(doc_path),
                        "content_length": len(content),
                        "category": category_dir.name,
                        "size_bytes": doc_path.stat().st_size
                    }
                    document_count += 1
                    doc_found = True
                    break

            if not doc_found:
                raise FileNotFoundError(f"Document not found: {doc_id}")

        print(f"PASS: All {document_count} documents found and loadable")

        # Test fold iteration simulation
        fold_stats = []
        for fold_id, fold_info in fold_data["folds"].items():
            train_docs = fold_info["train_documents"]
            test_docs = fold_info["test_documents"]

            # Verify all documents exist
            for doc_id in train_docs + test_docs:
                if doc_id not in loaded_docs:
                    raise ValueError(f"Document {doc_id} in fold but not in corpus")

            fold_stats.append({
                "fold_id": fold_id,
                "train_count": len(train_docs),
                "test_count": len(test_docs),
                "total_content_chars": sum(loaded_docs[doc_id]["content_length"]
                                         for doc_id in train_docs + test_docs)
            })

        print(f"PASS: All {len(fold_stats)} folds validated")

        # Display fold statistics
        for stat in fold_stats:
            print(f"  - {stat['fold_id']}: {stat['train_count']} train, {stat['test_count']} test docs, "
                  f"{stat['total_content_chars']:,} chars")

        # Test metrics integration
        metrics_file = Path("datasets/metrics/metrics.csv")
        if metrics_file.exists():
            with open(metrics_file, encoding="utf-8") as f:
                metrics_lines = f.readlines()

            metrics_doc_ids = []
            for line in metrics_lines[1:]:  # Skip header
                if line.strip():
                    doc_id = line.split(",")[0]
                    metrics_doc_ids.append(doc_id)

            # Verify all fold documents have metrics
            all_fold_docs = set(fold_data["document_inventory"])
            metrics_doc_set = set(metrics_doc_ids)

            missing_metrics = all_fold_docs - metrics_doc_set
            extra_metrics = metrics_doc_set - all_fold_docs

            if missing_metrics:
                raise ValueError(f"Documents missing metrics: {missing_metrics}")
            if extra_metrics:
                print(f"WARNING: Extra metrics for: {extra_metrics}")

            print(f"PASS: Metrics available for all {len(metrics_doc_ids)} documents")

        # Test baseline timing integration
        baseline_file = Path("datasets/baselines/baseline_timings.csv")
        if baseline_file.exists():
            with open(baseline_file, encoding="utf-8") as f:
                baseline_lines = f.readlines()

            baseline_doc_ids = []
            for line in baseline_lines[1:]:  # Skip header
                if line.strip():
                    doc_id = line.split(",")[0]
                    baseline_doc_ids.append(doc_id)

            all_fold_docs = set(fold_data["document_inventory"])
            baseline_doc_set = set(baseline_doc_ids)

            missing_baselines = all_fold_docs - baseline_doc_set
            if missing_baselines:
                raise ValueError(f"Documents missing baseline timings: {missing_baselines}")

            print(f"PASS: Baseline timings available for all {len(baseline_doc_ids)} documents")

        print("\nSUCCESS: Dataset is fully compatible with cross-validation framework!")
        print("Dataset Summary:")
        print(f"  - Total documents: {len(fold_data['document_inventory'])}")
        print(f"  - Folds: {len(fold_data['folds'])}")
        print(f"  - Total content: {sum(doc['content_length'] for doc in loaded_docs.values()):,} characters")
        print(f"  - Average document size: {sum(doc['content_length'] for doc in loaded_docs.values()) // len(loaded_docs):,} characters")

        return True

    except Exception as e:
        print(f"\nFAILURE: {e!s}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_dataset_cv_compatibility()
    exit(0 if success else 1)
