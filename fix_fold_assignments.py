#!/usr/bin/env python3
"""
Script to fix fold assignments JSON format for cross-validation execution.

The current fold_assignments.json has full document objects, but the FoldManager
expects just document IDs as strings. This script converts the format.
"""

import json
from pathlib import Path

def fix_fold_assignments():
    """Convert fold assignments from object format to ID-only format."""
    
    # Load current manifest
    fold_path = Path("datasets/cross_validation/fold_assignments.json")
    with open(fold_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("Converting fold assignments format...")
    
    # Convert each fold
    for fold_id, fold_data in data["folds"].items():
        # Extract just document IDs from test documents
        test_docs = [doc["doc_id"] for doc in fold_data["test_documents"]]
        train_docs = [doc["doc_id"] for doc in fold_data["train_documents"]]
        
        # Update the fold data
        fold_data["test_documents"] = test_docs
        fold_data["train_documents"] = train_docs
        
        print(f"  {fold_id}: {len(test_docs)} test, {len(train_docs)} train")
    
    # Create backup first
    backup_path = fold_path.with_suffix('.json.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Backup saved to: {backup_path}")
    
    # Save updated manifest
    with open(fold_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"Updated fold assignments saved to: {fold_path}")
    print("Conversion complete!")

if __name__ == "__main__":
    fix_fold_assignments()