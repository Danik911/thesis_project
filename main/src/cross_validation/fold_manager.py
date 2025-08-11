"""
Fold Manager for Cross-Validation Framework

This module handles the 5-fold partitioning of URS documents, providing
deterministic fold assignments and document loading capabilities with
full GAMP-5 compliance and audit trail support.

Key Features:
- Load fold assignments from JSON manifest
- Provide iterator over (fold_id, train_docs, val_docs)
- Load actual URS document content from filesystem
- Deterministic processing with fixed random seed
- ALCOA+ data integrity compliance
- No fallbacks - explicit error handling
"""

import json
import logging
from collections.abc import Iterator
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class FoldAssignment(BaseModel):
    """Model for individual fold assignment data."""
    fold_id: str = Field(description="Unique fold identifier (e.g., 'fold_1')")
    test_documents: list[str] = Field(description="Document IDs for validation set")
    train_documents: list[str] = Field(description="Document IDs for training set")
    train_count: int = Field(description="Number of training documents")
    test_count: int = Field(description="Number of validation documents")

    @field_validator("fold_id")
    @classmethod
    def validate_fold_id(cls, v):
        if not v.startswith("fold_"):
            msg = "Fold ID must start with 'fold_'"
            raise ValueError(msg)
        return v


class CrossValidationManifest(BaseModel):
    """Model for complete fold assignment manifest."""
    metadata: dict = Field(description="Manifest metadata")
    document_inventory: list[str] = Field(description="Complete list of available documents")
    folds: dict[str, FoldAssignment] = Field(description="Fold assignments")
    validation_summary: dict = Field(description="Validation and coverage summary")


class URSDocument(BaseModel):
    """Model for loaded URS document."""
    document_id: str = Field(description="Document identifier (e.g., 'URS-001')")
    file_path: Path = Field(description="Full path to document file")
    content: str = Field(description="Document text content")
    category_folder: str = Field(description="Source category folder")
    file_size_bytes: int = Field(description="File size for audit trail")

    class Config:
        arbitrary_types_allowed = True


class FoldManager:
    """
    Manages fold assignments and document loading for cross-validation.

    This class provides the core functionality for:
    - Loading fold assignments from JSON manifest
    - Iterating over folds with train/validation splits
    - Loading actual URS document content from filesystem
    - Maintaining audit trail for regulatory compliance
    """

    def __init__(
        self,
        fold_assignments_path: str | Path,
        urs_corpus_path: str | Path,
        random_seed: int = 42
    ):
        """
        Initialize the FoldManager.

        Args:
            fold_assignments_path: Path to fold assignments JSON file
            urs_corpus_path: Path to URS corpus directory
            random_seed: Random seed for reproducible processing
        """
        self.fold_assignments_path = Path(fold_assignments_path)
        self.urs_corpus_path = Path(urs_corpus_path)
        self.random_seed = random_seed
        self.logger = logging.getLogger(__name__)

        # Validation
        if not self.fold_assignments_path.exists():
            msg = f"Fold assignments file not found: {fold_assignments_path}"
            raise FileNotFoundError(msg)
        if not self.urs_corpus_path.exists():
            msg = f"URS corpus directory not found: {urs_corpus_path}"
            raise FileNotFoundError(msg)

        # Load and validate manifest
        self._manifest = self._load_manifest()
        self._document_cache: dict[str, URSDocument] = {}

        self.logger.info(f"FoldManager initialized: {len(self._manifest.folds)} folds, "
                        f"{len(self._manifest.document_inventory)} documents")

    def _load_manifest(self) -> CrossValidationManifest:
        """
        Load and validate the fold assignments manifest.

        Returns:
            CrossValidationManifest with validated fold data

        Raises:
            ValueError: If manifest validation fails
            FileNotFoundError: If manifest file doesn't exist
        """
        try:
            with open(self.fold_assignments_path, encoding="utf-8") as f:
                manifest_data = json.load(f)

            # Convert nested fold data to FoldAssignment objects
            validated_folds = {}
            for fold_id, fold_data in manifest_data["folds"].items():
                validated_folds[fold_id] = FoldAssignment(
                    fold_id=fold_id,
                    test_documents=fold_data["test_documents"],
                    train_documents=fold_data["train_documents"],
                    train_count=fold_data["train_count"],
                    test_count=fold_data["test_count"]
                )

            manifest = CrossValidationManifest(
                metadata=manifest_data["metadata"],
                document_inventory=manifest_data["document_inventory"],
                folds=validated_folds,
                validation_summary=manifest_data["validation_summary"]
            )

            # Validate manifest integrity
            self._validate_manifest_integrity(manifest)

            return manifest

        except json.JSONDecodeError as e:
            msg = f"Invalid JSON in fold assignments file: {e}"
            raise ValueError(msg)
        except KeyError as e:
            msg = f"Missing required field in manifest: {e}"
            raise ValueError(msg)
        except Exception as e:
            msg = f"Failed to load fold assignments manifest: {e}"
            raise ValueError(msg)

    def _validate_manifest_integrity(self, manifest: CrossValidationManifest) -> None:
        """
        Validate the integrity of the fold assignments manifest.

        Args:
            manifest: Loaded manifest to validate

        Raises:
            ValueError: If validation fails (no fallbacks allowed)
        """
        # Check that all documents appear exactly once in validation sets
        all_test_docs = []
        all_train_docs = []

        for fold_assignment in manifest.folds.values():
            all_test_docs.extend(fold_assignment.test_documents)
            all_train_docs.extend(fold_assignment.train_documents)

        # Verify each document appears exactly once in test sets
        test_doc_counts = {}
        for doc in all_test_docs:
            test_doc_counts[doc] = test_doc_counts.get(doc, 0) + 1

        duplicates = [doc for doc, count in test_doc_counts.items() if count > 1]
        if duplicates:
            msg = f"Documents appear multiple times in test sets: {duplicates}"
            raise ValueError(msg)

        missing_from_test = set(manifest.document_inventory) - set(all_test_docs)
        if missing_from_test:
            msg = f"Documents missing from test sets: {missing_from_test}"
            raise ValueError(msg)

        # Verify document counts match expectations
        total_docs = len(manifest.document_inventory)
        expected_test_docs = len(all_test_docs)

        if total_docs != expected_test_docs:
            msg = (
                f"Document count mismatch: inventory has {total_docs}, "
                f"test sets have {expected_test_docs}"
            )
            raise ValueError(
                msg
            )

        self.logger.info(f"Manifest validation passed: {total_docs} documents, "
                        f"{len(manifest.folds)} folds")

    def _find_document_file(self, document_id: str) -> Path:
        """
        Find the file path for a document ID in the URS corpus.

        Args:
            document_id: Document identifier (e.g., 'URS-001')

        Returns:
            Path to the document file

        Raises:
            FileNotFoundError: If document file cannot be found
        """
        # Search all category subdirectories
        for category_dir in self.urs_corpus_path.iterdir():
            if not category_dir.is_dir():
                continue

            doc_path = category_dir / f"{document_id}.md"
            if doc_path.exists():
                return doc_path

        msg = f"Document file not found: {document_id}"
        raise FileNotFoundError(msg)

    def _load_document(self, document_id: str) -> URSDocument:
        """
        Load a URS document from filesystem with caching.

        Args:
            document_id: Document identifier

        Returns:
            URSDocument with loaded content

        Raises:
            FileNotFoundError: If document cannot be found
            ValueError: If document cannot be read
        """
        # Check cache first
        if document_id in self._document_cache:
            return self._document_cache[document_id]

        try:
            file_path = self._find_document_file(document_id)
            content = file_path.read_text(encoding="utf-8")
            file_size = file_path.stat().st_size
            category_folder = file_path.parent.name

            document = URSDocument(
                document_id=document_id,
                file_path=file_path,
                content=content,
                category_folder=category_folder,
                file_size_bytes=file_size
            )

            # Cache the document
            self._document_cache[document_id] = document

            self.logger.debug(f"Loaded document {document_id}: {len(content)} chars, "
                             f"category {category_folder}")

            return document

        except Exception as e:
            msg = f"Failed to load document {document_id}: {e}"
            raise ValueError(msg)

    def get_fold_count(self) -> int:
        """Get the number of folds in the cross-validation setup."""
        return len(self._manifest.folds)

    def get_document_inventory(self) -> list[str]:
        """Get the complete list of available documents."""
        return self._manifest.document_inventory.copy()

    def get_fold_info(self, fold_id: str) -> FoldAssignment:
        """
        Get information about a specific fold.

        Args:
            fold_id: Fold identifier (e.g., 'fold_1')

        Returns:
            FoldAssignment with fold details

        Raises:
            ValueError: If fold_id is invalid
        """
        if fold_id not in self._manifest.folds:
            available_folds = list(self._manifest.folds.keys())
            msg = f"Invalid fold_id '{fold_id}'. Available: {available_folds}"
            raise ValueError(msg)

        return self._manifest.folds[fold_id]

    def iterate_folds(self) -> Iterator[tuple[str, list[URSDocument], list[URSDocument]]]:
        """
        Iterate over all folds, yielding (fold_id, train_docs, val_docs).

        Yields:
            Tuple of (fold_id, list of training documents, list of validation documents)

        Raises:
            ValueError: If document loading fails
        """
        for fold_id, fold_assignment in self._manifest.folds.items():
            try:
                # Load training documents
                train_docs = []
                for doc_id in fold_assignment.train_documents:
                    train_docs.append(self._load_document(doc_id))

                # Load validation documents
                val_docs = []
                for doc_id in fold_assignment.test_documents:
                    val_docs.append(self._load_document(doc_id))

                self.logger.info(f"Fold {fold_id}: {len(train_docs)} train, "
                               f"{len(val_docs)} validation documents")

                yield fold_id, train_docs, val_docs

            except Exception as e:
                msg = f"Failed to load documents for fold {fold_id}: {e}"
                raise ValueError(msg)

    def get_fold_documents(self, fold_id: str) -> tuple[list[URSDocument], list[URSDocument]]:
        """
        Get training and validation documents for a specific fold.

        Args:
            fold_id: Fold identifier

        Returns:
            Tuple of (training documents, validation documents)
        """
        fold_assignment = self.get_fold_info(fold_id)

        # Load training documents
        train_docs = [self._load_document(doc_id) for doc_id in fold_assignment.train_documents]

        # Load validation documents
        val_docs = [self._load_document(doc_id) for doc_id in fold_assignment.test_documents]

        return train_docs, val_docs

    def get_manifest_metadata(self) -> dict:
        """Get manifest metadata for audit trail."""
        return self._manifest.metadata.copy()

    def clear_cache(self) -> None:
        """Clear the document cache."""
        self._document_cache.clear()
        self.logger.debug("Document cache cleared")
