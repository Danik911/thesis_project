#!/usr/bin/env python3
"""
Dataset Validation Script

Validates the completeness and structure of the URS cross-validation dataset
without external dependencies.
"""

import json
import re
from pathlib import Path


def validate_urs_document_structure(file_path: Path) -> dict[str, any]:
    """Validate the structure of a single URS document."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        validation_result = {
            "file": file_path.name,
            "valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }

        # Check for required sections
        required_sections = [
            r"## 1\. Introduction",
            r"## 2\. Functional Requirements",
            r"## \d+\. Performance Requirements",
            r"## \d+\. Regulatory Requirements",
            r"## \d+\. Integration Requirements"
        ]

        for section in required_sections:
            if not re.search(section, content):
                validation_result["errors"].append(f"Missing required section: {section}")
                validation_result["valid"] = False

        # Check for metadata headers
        metadata_patterns = [
            r"\*\*GAMP Category\*\*:",
            r"\*\*System Type\*\*:",
            r"\*\*Domain\*\*:",
            r"\*\*Complexity Level\*\*:"
        ]

        for pattern in metadata_patterns:
            if not re.search(pattern, content):
                validation_result["warnings"].append(f"Missing metadata: {pattern}")

        # Count requirements
        requirement_pattern = r"- \*\*URS-[A-Z]+-\d+\*\*:"
        requirements = re.findall(requirement_pattern, content)
        req_count = len(requirements)

        validation_result["metrics"]["requirement_count"] = req_count

        # Validate requirement count range
        if req_count < 12:
            validation_result["errors"].append(f"Too few requirements: {req_count} (minimum 12)")
            validation_result["valid"] = False
        elif req_count > 40:
            validation_result["warnings"].append(f"High requirement count: {req_count} (typical max 40)")

        # Extract GAMP category
        gamp_match = re.search(r"\*\*GAMP Category\*\*:\s*([^*\n]+)", content)
        if gamp_match:
            validation_result["metrics"]["gamp_category"] = gamp_match.group(1).strip()

        return validation_result

    except Exception as e:
        return {
            "file": file_path.name,
            "valid": False,
            "errors": [f"Failed to read file: {e!s}"],
            "warnings": [],
            "metrics": {}
        }


def validate_cross_validation_config(cv_file: Path) -> dict[str, any]:
    """Validate the cross-validation configuration."""
    try:
        with open(cv_file, encoding="utf-8") as f:
            cv_config = json.load(f)

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        # Check basic structure
        if "folds" not in cv_config:
            validation_result["errors"].append("Missing 'folds' key in configuration")
            validation_result["valid"] = False
            return validation_result

        folds = cv_config["folds"]
        fold_count = len(folds)
        validation_result["statistics"]["fold_count"] = fold_count

        if fold_count != 5:
            validation_result["warnings"].append(f"Expected 5 folds, found {fold_count}")

        # Validate each fold
        all_documents = set()
        test_documents = set()

        for fold_name, fold_data in folds.items():
            train_docs = fold_data.get("train_documents", [])
            test_docs = fold_data.get("test_documents", [])

            # Collect document IDs - handle both string and dict formats
            for doc in train_docs:
                if isinstance(doc, dict):
                    doc_id = doc.get("document_id")
                else:
                    doc_id = doc

                if doc_id:
                    all_documents.add(doc_id)

            for doc in test_docs:
                if isinstance(doc, dict):
                    doc_id = doc.get("document_id")
                else:
                    doc_id = doc

                if doc_id:
                    if doc_id in test_documents:
                        validation_result["errors"].append(f"Document {doc_id} appears in multiple test sets")
                        validation_result["valid"] = False
                    test_documents.add(doc_id)
                    all_documents.add(doc_id)

            # Check fold balance (75/25 split approximately)
            total_in_fold = len(train_docs) + len(test_docs)
            test_ratio = len(test_docs) / total_in_fold if total_in_fold > 0 else 0

            if abs(test_ratio - 0.25) > 0.1:  # Allow 10% tolerance for 75/25 split
                validation_result["warnings"].append(
                    f"Fold {fold_name} test ratio {test_ratio:.2f} deviates significantly from 25%"
                )

        validation_result["statistics"]["total_documents"] = len(all_documents)
        validation_result["statistics"]["unique_test_documents"] = len(test_documents)

        # Verify each document appears exactly once in test sets
        if len(test_documents) != len(all_documents):
            validation_result["errors"].append(
                f"Not all documents appear as test data: {len(test_documents)} test vs {len(all_documents)} total"
            )
            validation_result["valid"] = False

        return validation_result

    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Failed to validate cross-validation config: {e!s}"],
            "warnings": [],
            "statistics": {}
        }


def validate_directory_structure(dataset_root: Path) -> dict[str, any]:
    """Validate the overall dataset directory structure."""
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "statistics": {}
    }

    # Expected directories
    expected_dirs = [
        "urs_corpus/category_3",
        "urs_corpus/category_4",
        "urs_corpus/category_5",
        "urs_corpus/ambiguous",
        "metrics",
        "baselines",
        "cross_validation"
    ]

    for expected_dir in expected_dirs:
        dir_path = dataset_root / expected_dir
        if not dir_path.exists():
            validation_result["errors"].append(f"Missing directory: {expected_dir}")
            validation_result["valid"] = False

    # Count URS files by category
    categories = {
        "category_3": "urs_corpus/category_3",
        "category_4": "urs_corpus/category_4",
        "category_5": "urs_corpus/category_5",
        "ambiguous": "urs_corpus/ambiguous"
    }

    for category, directory in categories.items():
        dir_path = dataset_root / directory
        if dir_path.exists():
            urs_files = list(dir_path.glob("URS-*.md"))
            validation_result["statistics"][f"{category}_count"] = len(urs_files)

            # Expected counts
            expected_counts = {
                "category_3": 5,
                "category_4": 5,
                "category_5": 5,
                "ambiguous": 2
            }

            expected = expected_counts.get(category, 0)
            actual = len(urs_files)

            if actual != expected:
                validation_result["errors"].append(
                    f"Wrong number of files in {category}: expected {expected}, found {actual}"
                )
                validation_result["valid"] = False

    return validation_result


def main():
    """Main validation function."""
    dataset_root = Path(__file__).parent

    print("VALIDATING URS CROSS-VALIDATION DATASET")
    print("=" * 50)

    # Validate directory structure
    print("\nValidating Directory Structure...")
    dir_validation = validate_directory_structure(dataset_root)

    if dir_validation["valid"]:
        print("PASS: Directory structure is valid")
        for category, count in dir_validation["statistics"].items():
            print(f"   - {category}: {count} files")
    else:
        print("FAIL: Directory structure validation failed:")
        for error in dir_validation["errors"]:
            print(f"   - {error}")

    # Validate individual URS documents
    print("\nValidating URS Documents...")
    urs_files = list(dataset_root.rglob("URS-*.md"))

    valid_docs = 0
    total_requirements = 0
    gamp_distribution = {}

    for urs_file in sorted(urs_files):
        validation = validate_urs_document_structure(urs_file)

        if validation["valid"]:
            valid_docs += 1
            req_count = validation["metrics"].get("requirement_count", 0)
            total_requirements += req_count

            gamp_cat = validation["metrics"].get("gamp_category", "Unknown")
            gamp_distribution[gamp_cat] = gamp_distribution.get(gamp_cat, 0) + 1

            print(f"PASS: {validation['file']}: {req_count} requirements")
        else:
            print(f"FAIL: {validation['file']}: FAILED")
            for error in validation["errors"]:
                print(f"     - {error}")

        # Show warnings
        for warning in validation["warnings"]:
            print(f"WARN: {validation['file']}: {warning}")

    print("\nURS Document Statistics:")
    print(f"   - Valid documents: {valid_docs}/{len(urs_files)}")
    print(f"   - Total requirements: {total_requirements}")
    print(f"   - Average requirements per document: {total_requirements/len(urs_files):.1f}")
    print(f"   - GAMP distribution: {gamp_distribution}")

    # Validate cross-validation configuration
    print("\nValidating Cross-Validation Configuration...")
    cv_file = dataset_root / "cross_validation" / "fold_assignments.json"

    if cv_file.exists():
        cv_validation = validate_cross_validation_config(cv_file)

        if cv_validation["valid"]:
            print("PASS: Cross-validation configuration is valid")
            stats = cv_validation["statistics"]
            print(f"   - Folds: {stats.get('fold_count', 'Unknown')}")
            print(f"   - Total documents: {stats.get('total_documents', 'Unknown')}")
            print(f"   - Unique test documents: {stats.get('unique_test_documents', 'Unknown')}")
        else:
            print("FAIL: Cross-validation configuration validation failed:")
            for error in cv_validation["errors"]:
                print(f"   - {error}")

        for warning in cv_validation["warnings"]:
            print(f"WARN: Cross-validation: {warning}")
    else:
        print("FAIL: Cross-validation configuration file not found")

    # Final summary
    print("\nValidation Summary:")
    all_valid = (
        dir_validation["valid"] and
        valid_docs == len(urs_files) and
        cv_file.exists() and
        cv_validation.get("valid", False)
    )

    if all_valid:
        print("PASS: Dataset validation PASSED - Ready for cross-validation testing!")
    else:
        print("FAIL: Dataset validation FAILED - Please address the issues above")

    return all_valid


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
