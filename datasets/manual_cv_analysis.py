#!/usr/bin/env python3
"""
Manual Cross-Validation Analysis for URS Corpus

Simplified version that manually extracts metadata and creates stratified splits
without dependency on the complexity calculator.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class URSDocumentSimple:
    """Simplified URS document representation."""
    doc_id: str
    file_path: str
    gamp_category: str
    normalized_category: str
    system_type: str
    domain: str
    complexity_level: str
    estimated_complexity: float
    total_requirements: int


def extract_metadata_manual(file_path: Path) -> URSDocumentSimple:
    """Extract metadata manually from URS file."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    metadata = {"doc_id": file_path.stem}

    # Extract header metadata
    for line in lines[:15]:
        line = line.strip()
        if line.startswith("**GAMP Category**"):
            match = re.search(r"\*\*GAMP Category\*\*:\s*(.+)", line)
            if match:
                metadata["gamp_category"] = match.group(1).strip()
        elif line.startswith("**System Type**"):
            match = re.search(r"\*\*System Type\*\*:\s*(.+)", line)
            if match:
                metadata["system_type"] = match.group(1).strip()
        elif line.startswith("**Domain**"):
            match = re.search(r"\*\*Domain\*\*:\s*(.+)", line)
            if match:
                metadata["domain"] = match.group(1).strip()
        elif line.startswith("**Complexity Level**"):
            match = re.search(r"\*\*Complexity Level\*\*:\s*(.+)", line)
            if match:
                metadata["complexity_level"] = match.group(1).strip()

    # Count requirements
    requirement_count = len(re.findall(r"- \*\*URS-[A-Z]+-\d+\*\*:", content))

    # Normalize GAMP category
    gamp_lower = metadata["gamp_category"].lower()
    if "3" in gamp_lower or "standard software" in gamp_lower:
        normalized = "Category 3"
    elif "4" in gamp_lower or "configured" in gamp_lower:
        normalized = "Category 4"
    elif "5" in gamp_lower or "custom" in gamp_lower:
        normalized = "Category 5"
    elif "ambiguous" in gamp_lower or "/" in gamp_lower:
        normalized = "Ambiguous"
    else:
        normalized = "Unknown"

    # Estimate complexity based on level and category
    complexity_mapping = {
        ("Low", "Category 3"): 0.18,
        ("Medium", "Category 4"): 0.30,
        ("Medium", "Ambiguous"): 0.32,
        ("Medium-High", "Category 4"): 0.55,
        ("High", "Category 4"): 0.65,
        ("High", "Category 5"): 0.75,
        ("High", "Ambiguous"): 0.70,
        ("Very High", "Category 5"): 0.90
    }

    complexity_level = metadata["complexity_level"]
    estimated_complexity = complexity_mapping.get((complexity_level, normalized), 0.5)

    return URSDocumentSimple(
        doc_id=metadata["doc_id"],
        file_path=str(file_path),
        gamp_category=metadata["gamp_category"],
        normalized_category=normalized,
        system_type=metadata["system_type"],
        domain=metadata["domain"],
        complexity_level=complexity_level,
        estimated_complexity=estimated_complexity,
        total_requirements=requirement_count
    )


def analyze_all_documents() -> list[URSDocumentSimple]:
    """Analyze all URS documents."""
    corpus_path = Path("urs_corpus")
    urs_files = list(corpus_path.rglob("URS-*.md"))

    documents = []
    for file_path in sorted(urs_files):
        try:
            doc = extract_metadata_manual(file_path)
            documents.append(doc)
            print(f"✓ {doc.doc_id}: {doc.normalized_category}, complexity={doc.estimated_complexity:.2f}, reqs={doc.total_requirements}")
        except Exception as e:
            print(f"✗ Failed {file_path}: {e}")

    return documents


def create_stratified_folds_manual(documents: list[URSDocumentSimple], k: int = 5) -> dict:
    """Create stratified k-fold splits manually."""
    print(f"\nCreating {k}-fold cross-validation splits...")

    # Group by category
    category_groups = {}
    for doc in documents:
        cat = doc.normalized_category
        if cat not in category_groups:
            category_groups[cat] = []
        category_groups[cat].append(doc)

    print("\nCategory Distribution:")
    for cat, docs in category_groups.items():
        print(f"  {cat}: {len(docs)} documents")

    # Initialize folds
    folds = {f"fold_{i+1}": {"test_documents": [], "train_documents": []} for i in range(k)}

    # Round-robin assignment within each category
    for category, cat_docs in category_groups.items():
        # Sort by complexity for even distribution
        sorted_docs = sorted(cat_docs, key=lambda d: d.estimated_complexity)

        for i, doc in enumerate(sorted_docs):
            fold_idx = i % k
            fold_name = f"fold_{fold_idx + 1}"
            folds[fold_name]["test_documents"].append(doc)

    # Assign training documents (all except test)
    all_docs = {doc.doc_id: doc for doc in documents}
    for fold_name, fold_data in folds.items():
        test_ids = {doc.doc_id for doc in fold_data["test_documents"]}
        fold_data["train_documents"] = [doc for doc_id, doc in all_docs.items() if doc_id not in test_ids]

    print("\nFold Distribution:")
    for fold_name, fold_data in folds.items():
        test_cats = {}
        for doc in fold_data["test_documents"]:
            cat = doc.normalized_category
            test_cats[cat] = test_cats.get(cat, 0) + 1

        cat_str = ", ".join([f"{cat}:{count}" for cat, count in sorted(test_cats.items())])
        print(f"  {fold_name}: {len(fold_data['test_documents'])} test ({cat_str})")

    return folds


def create_fold_config(folds: dict, all_documents: list[URSDocumentSimple]) -> dict:
    """Create serializable fold configuration."""
    serializable_folds = {}

    for fold_name, fold_data in folds.items():
        test_docs = []
        train_docs = []

        for doc in fold_data["test_documents"]:
            test_docs.append({
                "doc_id": doc.doc_id,
                "file_path": doc.file_path,
                "gamp_category": doc.gamp_category,
                "normalized_category": doc.normalized_category,
                "system_type": doc.system_type,
                "domain": doc.domain,
                "complexity_level": doc.complexity_level,
                "complexity_score": doc.estimated_complexity,
                "total_requirements": doc.total_requirements,
                "requirement_breakdown": {
                    "functional": 0,  # Not calculated in simplified version
                    "regulatory": 0,
                    "performance": 0,
                    "integration": 0,
                    "technical": 0,
                    "total": doc.total_requirements
                }
            })

        for doc in fold_data["train_documents"]:
            train_docs.append({
                "doc_id": doc.doc_id,
                "file_path": doc.file_path,
                "gamp_category": doc.gamp_category,
                "normalized_category": doc.normalized_category,
                "system_type": doc.system_type,
                "domain": doc.domain,
                "complexity_level": doc.complexity_level,
                "complexity_score": doc.estimated_complexity,
                "total_requirements": doc.total_requirements,
                "requirement_breakdown": {
                    "functional": 0,
                    "regulatory": 0,
                    "performance": 0,
                    "integration": 0,
                    "technical": 0,
                    "total": doc.total_requirements
                }
            })

        serializable_folds[fold_name] = {
            "test_documents": test_docs,
            "train_documents": train_docs,
            "test_count": len(test_docs),
            "train_count": len(train_docs)
        }

    # Calculate statistics
    total_reqs = sum(doc.total_requirements for doc in all_documents)
    complexity_scores = [doc.estimated_complexity for doc in all_documents]

    category_dist = {}
    for doc in all_documents:
        cat = doc.normalized_category
        category_dist[cat] = category_dist.get(cat, 0) + 1

    import statistics
    return {
        "metadata": {
            "description": "Stratified 5-fold cross-validation assignments for URS corpus",
            "total_documents": len(all_documents),
            "total_requirements": total_reqs,
            "folds": len(folds),
            "stratification_method": "GAMP category + complexity level (manual)",
            "created_date": "2025-08-13",
            "validation_strategy": "Stratified K-Fold with balanced GAMP category distribution",
            "random_seed": None,
            "complexity_range": {
                "min": round(min(complexity_scores), 4),
                "max": round(max(complexity_scores), 4),
                "mean": round(statistics.mean(complexity_scores), 4),
                "std": round(statistics.stdev(complexity_scores), 4)
            },
            "category_distribution": category_dist
        },
        "document_inventory": [doc.doc_id for doc in sorted(all_documents, key=lambda d: d.doc_id)],
        "folds": serializable_folds,
        "validation_summary": {
            "total_unique_documents": len(all_documents),
            "documents_per_test_set": "Each document appears exactly once as test data across all folds",
            "stratification_balance": "GAMP categories distributed across folds, complexity levels balanced",
            "coverage": "100% of documents used for testing exactly once"
        }
    }


def main():
    """Main execution."""
    print("Cross-Validation Dataset Preparation (Manual)")
    print("=" * 50)

    # Analyze documents
    print("\n1. Analyzing URS documents...")
    documents = analyze_all_documents()
    print(f"Analyzed {len(documents)} documents")

    # Create folds
    print("\n2. Creating stratified folds...")
    folds = create_stratified_folds_manual(documents, k=5)

    # Create configuration
    print("\n3. Creating fold configuration...")
    fold_config = create_fold_config(folds, documents)

    # Save configuration
    print("\n4. Saving configuration...")
    output_path = Path("cross_validation/fold_assignments.json")
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fold_config, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved to {output_path}")

    # Summary report
    print("\n" + "=" * 60)
    print("CROSS-VALIDATION DATASET SUMMARY")
    print("=" * 60)

    print("\nDATASET OVERVIEW:")
    print(f"  Total Documents: {len(documents)}")
    print(f"  Total Requirements: {sum(doc.total_requirements for doc in documents)}")
    print(f"  Complexity Range: {fold_config['metadata']['complexity_range']['min']:.3f} - {fold_config['metadata']['complexity_range']['max']:.3f}")

    print("\nGAMP CATEGORY DISTRIBUTION:")
    for cat, count in fold_config["metadata"]["category_distribution"].items():
        pct = (count / len(documents)) * 100
        print(f"  {cat}: {count} documents ({pct:.1f}%)")

    print("\nFOLD BALANCE:")
    for fold_name, fold_data in fold_config["folds"].items():
        print(f"  {fold_name}: {fold_data['test_count']} test, {fold_data['train_count']} train")

    print("\n✓ Cross-validation dataset preparation completed!")


if __name__ == "__main__":
    main()
