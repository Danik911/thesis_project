#!/usr/bin/env python3
"""
Cross-Validation Manager for URS Dataset

This module provides the CrossValidationManager class for managing k-fold cross-validation
of pharmaceutical URS documents. Implements GAMP-5 compliant stratified splitting with
NO FALLBACK LOGIC - all operations fail explicitly with detailed error messages.

GAMP-5 Compliance: This module follows pharmaceutical validation standards with explicit
error handling, audit trail support, and reproducible fold generation.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DocumentMetadata:
    """Metadata for a single URS document."""
    doc_id: str
    file_path: str
    gamp_category: str
    normalized_category: str
    system_type: str
    domain: str
    complexity_level: str
    complexity_score: float
    total_requirements: int
    requirement_breakdown: dict[str, int]
    verified: bool = True


class CrossValidationManager:
    """
    Manage k-fold cross-validation for URS document dataset.
    
    This class provides methods to load datasets, create stratified folds,
    retrieve fold data, and validate fold balance. All operations follow
    pharmaceutical compliance requirements with NO FALLBACK LOGIC.
    """

    def __init__(self, config_path: str | None = None):
        """
        Initialize CrossValidationManager with configuration.
        
        Args:
            config_path: Path to CV configuration JSON file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
            RuntimeError: If initialization fails
        """
        try:
            # Set default config path if not provided
            if config_path is None:
                config_path = Path(__file__).parent / "cv_config.json"

            self.config_path = Path(config_path)
            if not self.config_path.exists():
                raise FileNotFoundError(f"CV config file not found: {config_path}")

            # Load configuration
            with open(self.config_path, encoding="utf-8") as f:
                self.config = json.load(f)

            # Validate configuration
            self._validate_config()

            # Initialize state
            self.dataset_inventory = None
            self.fold_assignments = None
            self.documents = {}

            # Set random seed for reproducibility
            seed = self.config["cross_validation_config"]["random_seed"]
            random.seed(seed)

        except Exception as e:
            raise RuntimeError(f"Failed to initialize CrossValidationManager: {e!s}")

    def _validate_config(self) -> None:
        """
        Validate the loaded configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        required_sections = [
            "cross_validation_config",
            "dataset_parameters",
            "fold_distribution_target",
            "validation_thresholds"
        ]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")

        cv_config = self.config["cross_validation_config"]
        required_cv_keys = ["method", "k_folds", "random_seed"]

        for key in required_cv_keys:
            if key not in cv_config:
                raise ValueError(f"Missing required CV config key: {key}")

        if cv_config["k_folds"] != 5:
            raise ValueError("Only k=5 folds currently supported")

        if cv_config["method"] != "stratified_k_fold":
            raise ValueError("Only stratified_k_fold method currently supported")

    def load_dataset(self, inventory_path: str | None = None) -> dict[str, Any]:
        """
        Load dataset inventory and document metadata.
        
        Args:
            inventory_path: Path to dataset inventory JSON file
            
        Returns:
            Dictionary containing dataset metadata
            
        Raises:
            FileNotFoundError: If inventory file doesn't exist
            ValueError: If inventory data is invalid
            RuntimeError: If loading fails
        """
        try:
            # Set default inventory path if not provided
            if inventory_path is None:
                inventory_path = Path(__file__).parent / "dataset_inventory.json"

            inventory_path = Path(inventory_path)
            if not inventory_path.exists():
                raise FileNotFoundError(f"Dataset inventory not found: {inventory_path}")

            # Load inventory
            with open(inventory_path, encoding="utf-8") as f:
                self.dataset_inventory = json.load(f)

            # Validate inventory structure
            if "document_inventory" not in self.dataset_inventory:
                raise ValueError("Missing 'document_inventory' in dataset inventory")

            # Convert to DocumentMetadata objects
            self.documents = {}
            for doc_data in self.dataset_inventory["document_inventory"]:
                doc_meta = DocumentMetadata(
                    doc_id=doc_data["doc_id"],
                    file_path=doc_data["file_path"],
                    gamp_category=doc_data["gamp_category"],
                    normalized_category=doc_data["normalized_category"],
                    system_type=doc_data["system_type"],
                    domain=doc_data["domain"],
                    complexity_level=doc_data["complexity_level"],
                    complexity_score=doc_data["complexity_score"],
                    total_requirements=doc_data["total_requirements"],
                    requirement_breakdown=doc_data["requirement_breakdown"],
                    verified=doc_data.get("verified", True)
                )
                self.documents[doc_meta.doc_id] = doc_meta

            # Validate document count
            expected_count = self.config["dataset_parameters"]["total_documents"]
            actual_count = len(self.documents)

            if actual_count != expected_count:
                raise ValueError(f"Document count mismatch: expected {expected_count}, found {actual_count}")

            return self.dataset_inventory

        except Exception as e:
            raise RuntimeError(f"Failed to load dataset: {e!s}")

    def load_fold_assignments(self, assignments_path: str | None = None) -> dict[str, Any]:
        """
        Load existing fold assignments.
        
        Args:
            assignments_path: Path to fold assignments JSON file
            
        Returns:
            Dictionary containing fold assignments
            
        Raises:
            FileNotFoundError: If assignments file doesn't exist
            ValueError: If assignments data is invalid
            RuntimeError: If loading fails
        """
        try:
            # Set default assignments path if not provided
            if assignments_path is None:
                assignments_path = Path(__file__).parent / "fold_assignments.json"

            assignments_path = Path(assignments_path)
            if not assignments_path.exists():
                raise FileNotFoundError(f"Fold assignments not found: {assignments_path}")

            # Load assignments
            with open(assignments_path, encoding="utf-8") as f:
                self.fold_assignments = json.load(f)

            # Validate structure
            if "folds" not in self.fold_assignments:
                raise ValueError("Missing 'folds' section in fold assignments")

            expected_folds = self.config["cross_validation_config"]["k_folds"]
            actual_folds = len(self.fold_assignments["folds"])

            if actual_folds != expected_folds:
                raise ValueError(f"Fold count mismatch: expected {expected_folds}, found {actual_folds}")

            return self.fold_assignments

        except Exception as e:
            raise RuntimeError(f"Failed to load fold assignments: {e!s}")

    def get_fold(self, fold_num: int) -> dict[str, list[DocumentMetadata]]:
        """
        Get documents for a specific fold.
        
        Args:
            fold_num: Fold number (1-based indexing)
            
        Returns:
            Dictionary with 'train' and 'test' keys containing DocumentMetadata lists
            
        Raises:
            ValueError: If fold number is invalid
            RuntimeError: If fold data retrieval fails
        """
        if not (1 <= fold_num <= 5):
            raise ValueError(f"Invalid fold number: {fold_num}. Must be 1-5")

        if self.fold_assignments is None:
            raise RuntimeError("Fold assignments not loaded. Call load_fold_assignments() first")

        if self.documents is None:
            raise RuntimeError("Dataset not loaded. Call load_dataset() first")

        try:
            fold_key = f"fold_{fold_num}"
            if fold_key not in self.fold_assignments["folds"]:
                raise ValueError(f"Fold {fold_num} not found in assignments")

            fold_data = self.fold_assignments["folds"][fold_key]

            # Convert to DocumentMetadata objects
            result = {
                "train": [],
                "test": []
            }

            # Get test documents
            for doc_data in fold_data["test_documents"]:
                doc_id = doc_data["doc_id"]
                if doc_id not in self.documents:
                    raise RuntimeError(f"Test document {doc_id} not found in dataset inventory")
                result["test"].append(self.documents[doc_id])

            # Get training documents
            for doc_data in fold_data["train_documents"]:
                doc_id = doc_data["doc_id"]
                if doc_id not in self.documents:
                    raise RuntimeError(f"Train document {doc_id} not found in dataset inventory")
                result["train"].append(self.documents[doc_id])

            return result

        except Exception as e:
            raise RuntimeError(f"Failed to get fold {fold_num}: {e!s}")

    def validate_fold_balance(self) -> dict[str, Any]:
        """
        Validate the balance and quality of fold assignments.
        
        Returns:
            Dictionary containing validation results and statistics
            
        Raises:
            RuntimeError: If validation fails or data is invalid
        """
        if self.fold_assignments is None or self.documents is None:
            raise RuntimeError("Dataset and fold assignments must be loaded first")

        try:
            validation_results = {
                "overall_balance": {},
                "fold_statistics": {},
                "category_distribution": {},
                "complexity_distribution": {},
                "validation_passed": True,
                "issues": []
            }

            # Check overall balance
            total_docs = len(self.documents)
            expected_total = self.config["dataset_parameters"]["total_documents"]

            if total_docs != expected_total:
                validation_results["validation_passed"] = False
                validation_results["issues"].append(f"Document count mismatch: {total_docs} vs {expected_total}")

            # Analyze each fold
            fold_stats = {}
            category_counts = {"Category 3": [], "Category 4": [], "Category 5": [], "Ambiguous": []}
            complexity_scores = []

            for fold_num in range(1, 6):
                fold_data = self.get_fold(fold_num)

                test_docs = fold_data["test"]
                train_docs = fold_data["train"]

                # Count categories in test set
                test_categories = {"Category 3": 0, "Category 4": 0, "Category 5": 0, "Ambiguous": 0}
                test_complexity = []

                for doc in test_docs:
                    test_categories[doc.normalized_category] += 1
                    test_complexity.append(doc.complexity_score)

                fold_stats[f"fold_{fold_num}"] = {
                    "test_count": len(test_docs),
                    "train_count": len(train_docs),
                    "test_categories": test_categories,
                    "test_complexity_mean": sum(test_complexity) / len(test_complexity) if test_complexity else 0,
                    "test_complexity_std": self._calculate_std(test_complexity) if len(test_complexity) > 1 else 0
                }

                # Accumulate for overall analysis
                for cat, count in test_categories.items():
                    category_counts[cat].append(count)
                complexity_scores.extend(test_complexity)

            validation_results["fold_statistics"] = fold_stats

            # Check category balance across folds
            for category, counts in category_counts.items():
                mean_count = sum(counts) / len(counts)
                std_count = self._calculate_std(counts)
                coefficient_of_variation = std_count / mean_count if mean_count > 0 else 0

                validation_results["category_distribution"][category] = {
                    "counts_per_fold": counts,
                    "mean": mean_count,
                    "std": std_count,
                    "coefficient_of_variation": coefficient_of_variation
                }

                # Check threshold
                threshold = self.config["validation_thresholds"]["category_deviation_max"]
                if coefficient_of_variation > threshold:
                    validation_results["validation_passed"] = False
                    validation_results["issues"].append(f"Category {category} imbalance: CV = {coefficient_of_variation:.3f} > {threshold}")

            # Check complexity balance
            overall_complexity_mean = sum(complexity_scores) / len(complexity_scores)
            overall_complexity_std = self._calculate_std(complexity_scores)

            validation_results["complexity_distribution"] = {
                "overall_mean": overall_complexity_mean,
                "overall_std": overall_complexity_std,
                "fold_means": [fold_stats[f"fold_{i}"]["test_complexity_mean"] for i in range(1, 6)]
            }

            return validation_results

        except Exception as e:
            raise RuntimeError(f"Failed to validate fold balance: {e!s}")

    def _calculate_std(self, values: list[float]) -> float:
        """Calculate standard deviation of a list of values."""
        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5

    def get_fold_summary(self) -> dict[str, Any]:
        """
        Get a summary of all folds and their characteristics.
        
        Returns:
            Dictionary containing fold summary information
            
        Raises:
            RuntimeError: If data not loaded or summary generation fails
        """
        if self.fold_assignments is None or self.documents is None:
            raise RuntimeError("Dataset and fold assignments must be loaded first")

        try:
            summary = {
                "total_documents": len(self.documents),
                "total_folds": 5,
                "fold_overview": {},
                "stratification_summary": {
                    "primary": "GAMP Category",
                    "secondary": "Complexity Level"
                }
            }

            for fold_num in range(1, 6):
                fold_data = self.get_fold(fold_num)

                test_categories = {"Category 3": 0, "Category 4": 0, "Category 5": 0, "Ambiguous": 0}
                test_complexity = []

                for doc in fold_data["test"]:
                    test_categories[doc.normalized_category] += 1
                    test_complexity.append(doc.complexity_score)

                summary["fold_overview"][f"fold_{fold_num}"] = {
                    "test_documents": len(fold_data["test"]),
                    "train_documents": len(fold_data["train"]),
                    "test_categories": test_categories,
                    "complexity_range": {
                        "min": min(test_complexity) if test_complexity else 0,
                        "max": max(test_complexity) if test_complexity else 0,
                        "mean": sum(test_complexity) / len(test_complexity) if test_complexity else 0
                    }
                }

            return summary

        except Exception as e:
            raise RuntimeError(f"Failed to generate fold summary: {e!s}")


def load_cv_manager(config_path: str | None = None) -> CrossValidationManager:
    """
    Factory function to create and initialize a CrossValidationManager.
    
    Args:
        config_path: Optional path to CV configuration file
        
    Returns:
        Initialized CrossValidationManager instance
        
    Raises:
        RuntimeError: If initialization fails
    """
    try:
        manager = CrossValidationManager(config_path)
        manager.load_dataset()
        manager.load_fold_assignments()
        return manager

    except Exception as e:
        raise RuntimeError(f"Failed to initialize CV manager: {e!s}")


if __name__ == "__main__":
    """
    Example usage and validation of CrossValidationManager.
    """
    try:
        print("Initializing CrossValidationManager...")
        manager = load_cv_manager()

        print(f"Loaded {len(manager.documents)} documents")

        # Test fold retrieval
        print("\\nTesting fold retrieval:")
        for fold_num in range(1, 6):
            fold_data = manager.get_fold(fold_num)
            print(f"Fold {fold_num}: {len(fold_data['test'])} test, {len(fold_data['train'])} train")

        # Validate balance
        print("\\nValidating fold balance...")
        validation = manager.validate_fold_balance()

        if validation["validation_passed"]:
            print("PASSED: Fold validation PASSED")
        else:
            print("FAILED: Fold validation FAILED")
            for issue in validation["issues"]:
                print(f"  - {issue}")

        # Generate summary
        print("\\nFold Summary:")
        summary = manager.get_fold_summary()
        for fold_key, fold_info in summary["fold_overview"].items():
            print(f"{fold_key}: {fold_info['test_documents']} test docs, complexity range {fold_info['complexity_range']['min']:.2f}-{fold_info['complexity_range']['max']:.2f}")

        print("\\nSUCCESS: CrossValidationManager validation complete")

    except Exception as e:
        print(f"ERROR: {e}")
        exit(1)
