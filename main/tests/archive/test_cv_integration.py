#!/usr/bin/env python3
"""
Test cross-validation integration with Task 16 dataset
"""

import sys
from pathlib import Path

# Add main source to path
sys.path.append(str(Path(__file__).parent / "main" / "src"))

from cross_validation.fold_manager import FoldManager


def test_fold_manager_integration():
    """Test FoldManager can load Task 16 dataset."""
    print("Testing FoldManager Integration with Task 16 Dataset")
    print("=" * 55)

    try:
        # Initialize FoldManager with default paths
        fold_manager = FoldManager()

        print("✓ FoldManager initialized successfully")
        print(f"  - Fold count: {fold_manager.get_fold_count()}")
        print(f"  - Document inventory: {len(fold_manager.get_document_inventory())} documents")

        # Test getting document inventory
        inventory = fold_manager.get_document_inventory()
        print(f"  - Documents: {inventory}")

        # Test loading first fold
        fold_id = "fold_1"
        fold_info = fold_manager.get_fold_info(fold_id)
        print(f"\n✓ Fold info loaded for {fold_id}")
        print(f"  - Training docs: {fold_info.train_count}")
        print(f"  - Test docs: {fold_info.test_count}")

        # Test document loading
        train_docs, val_docs = fold_manager.get_fold_documents(fold_id)
        print(f"\n✓ Documents loaded for {fold_id}")
        print(f"  - Training documents loaded: {len(train_docs)}")
        print(f"  - Validation documents loaded: {len(val_docs)}")

        # Verify document content
        if train_docs:
            sample_doc = train_docs[0]
            print(f"  - Sample document: {sample_doc.document_id}")
            print(f"  - Content length: {len(sample_doc.content)} chars")
            print(f"  - Category: {sample_doc.category_folder}")

        # Test iteration over all folds
        print("\n✓ Testing fold iteration:")
        fold_count = 0
        total_train_docs = 0
        total_val_docs = 0

        for fold_id, train_docs, val_docs in fold_manager.iterate_folds():
            fold_count += 1
            total_train_docs += len(train_docs)
            total_val_docs += len(val_docs)
            print(f"  - {fold_id}: {len(train_docs)} train, {len(val_docs)} val docs")

        print("\n✓ Iteration completed")
        print(f"  - Total folds processed: {fold_count}")
        print(f"  - Total training document loads: {total_train_docs}")
        print(f"  - Total validation document loads: {total_val_docs}")

        # Test manifest metadata
        metadata = fold_manager.get_manifest_metadata()
        print("\n✓ Manifest metadata available")
        print(f"  - Metadata keys: {list(metadata.keys())}")

        print("\n🎉 SUCCESS: FoldManager integration with Task 16 dataset is working perfectly!")
        return True

    except Exception as e:
        print(f"\n❌ FAILURE: {e!s}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fold_manager_integration()
    sys.exit(0 if success else 1)
