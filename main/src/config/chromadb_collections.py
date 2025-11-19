"""
ChromaDB Collection Name Constants

CRITICAL: These constants must be used consistently across ALL modules to prevent
collection name mismatches that can make documents invisible to the workflow.

Usage:
    from main.src.config.chromadb_collections import REGULATORY_COLLECTION

    collection = chroma_client.get_or_create_collection(
        name=REGULATORY_COLLECTION  # ✅ Use constant
    )

Affected Modules:
    - main/src/agents/parallel/context_provider.py (lines 470-503)
    - main/scripts/ingest-documents.py (line 74)
    - main/scripts/seed_chroma.py (lines 67-84)

GAMP-5 Compliance Note:
    Collection naming consistency is required for audit trail integrity and
    data traceability per ALCOA+ principles (Complete, Consistent).
"""

# Collection Names (SINGLE SOURCE OF TRUTH)
GAMP5_COLLECTION = "gamp5_documents"
REGULATORY_COLLECTION = "regulatory_documents"
SOP_COLLECTION = "sop_documents"
BEST_PRACTICES_COLLECTION = "best_practices"

# Collection Metadata Templates
COLLECTION_METADATA = {
    GAMP5_COLLECTION: {
        "description": "GAMP-5 validation and testing guidelines",
        "compliance_level": "regulatory",
        "doc_type": "regulatory_guide"
    },
    REGULATORY_COLLECTION: {
        "description": "FDA, EMA, ICH regulatory requirements",
        "compliance_level": "mandatory",
        "doc_type": "regulatory_guide"
    },
    SOP_COLLECTION: {
        "description": "Standard Operating Procedures",
        "compliance_level": "internal",
        "doc_type": "sop"
    },
    BEST_PRACTICES_COLLECTION: {
        "description": "Industry best practices and methodologies",
        "compliance_level": "recommended",
        "doc_type": "best_practice"
    }
}

# Dictionary Key Mapping (for backward compatibility)
# Maps internal code keys to actual ChromaDB collection names
KEY_TO_COLLECTION = {
    "gamp5": GAMP5_COLLECTION,
    "regulatory": REGULATORY_COLLECTION,
    "sops": SOP_COLLECTION,
    "best_practices": BEST_PRACTICES_COLLECTION
}

# Validation Helper
def validate_collection_name(collection_name: str) -> bool:
    """
    Validate that collection name matches one of the defined constants.

    Args:
        collection_name: Name to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_collection_name("regulatory_documents")
        True
        >>> validate_collection_name("regulatory")
        False  # Should use constant REGULATORY_COLLECTION
    """
    valid_names = {
        GAMP5_COLLECTION,
        REGULATORY_COLLECTION,
        SOP_COLLECTION,
        BEST_PRACTICES_COLLECTION
    }
    return collection_name in valid_names


def get_collection_metadata(collection_name: str) -> dict:
    """
    Get metadata template for a collection.

    Args:
        collection_name: Collection name (must be a valid constant)

    Returns:
        Metadata dictionary

    Raises:
        ValueError: If collection_name is not valid
    """
    if not validate_collection_name(collection_name):
        raise ValueError(
            f"Invalid collection name: {collection_name}. "
            f"Must use constants from chromadb_collections.py"
        )
    return COLLECTION_METADATA[collection_name]
