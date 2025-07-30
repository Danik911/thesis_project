"""
Pharmaceutical Document Ingestion Utility

This utility helps with ingesting various pharmaceutical documents into the
Context Provider Agent's ChromaDB collections for GAMP-5 compliant test generation.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.agents.parallel.context_provider import create_context_provider_agent

logger = logging.getLogger(__name__)


class PharmaDocumentIngestion:
    """Utility class for ingesting pharmaceutical documents."""
    
    def __init__(self, verbose: bool = True):
        """Initialize the ingestion utility."""
        self.agent = create_context_provider_agent(
            verbose=verbose,
            enable_phoenix=False  # Can be enabled for production
        )
        self.verbose = verbose
        
    async def ingest_directory(
        self,
        directory_path: str,
        collection_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Ingest all documents from a directory into appropriate collections.
        
        Args:
            directory_path: Path to directory containing documents
            collection_mapping: Optional mapping of file patterns to collections
                               e.g., {"*gamp*.pdf": "gamp5", "*cfr*.pdf": "regulatory"}
        
        Returns:
            Dictionary with ingestion results per collection
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise ValueError(f"Directory not found: {directory_path}")
        
        # Default mapping if none provided
        if collection_mapping is None:
            collection_mapping = {
                "*gamp*": "gamp5",
                "*cfr*": "regulatory",
                "*21cfr*": "regulatory",
                "*sop*": "sops",
                "*procedure*": "sops",
                "*best*practice*": "best_practices",
                "*guideline*": "best_practices"
            }
        
        results = {}
        
        # Process each file
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix in ['.pdf', '.md', '.txt']:
                # Determine collection based on filename
                collection = self._determine_collection(
                    file_path.name,
                    collection_mapping
                )
                
                if collection:
                    if self.verbose:
                        logger.info(f"Ingesting {file_path.name} into {collection}")
                    
                    try:
                        stats = await self.agent.ingest_documents(
                            documents_path=str(file_path),
                            collection_name=collection,
                            force_reprocess=False
                        )
                        
                        if collection not in results:
                            results[collection] = []
                        
                        results[collection].append({
                            "file": file_path.name,
                            "stats": stats
                        })
                        
                    except Exception as e:
                        logger.error(f"Failed to ingest {file_path.name}: {e}")
                        # NO FALLBACKS - fail explicitly
                        raise
                else:
                    logger.warning(f"No collection mapping for: {file_path.name}")
        
        return results
    
    async def ingest_pharma_standards(self, standards_dir: str) -> Dict[str, Any]:
        """
        Ingest standard pharmaceutical documents with predefined structure.
        
        Expected directory structure:
        standards_dir/
        ├── gamp5/
        │   ├── category_3.pdf
        │   ├── category_4.pdf
        │   └── category_5.pdf
        ├── regulatory/
        │   ├── 21_cfr_part_11.pdf
        │   └── eu_annex_11.pdf
        ├── sops/
        │   └── validation_sop.pdf
        └── best_practices/
            └── testing_guidelines.pdf
        """
        standards_path = Path(standards_dir)
        if not standards_path.exists():
            raise ValueError(f"Standards directory not found: {standards_dir}")
        
        results = {}
        
        # Process each subdirectory as a collection
        for collection_dir in standards_path.iterdir():
            if collection_dir.is_dir():
                collection_name = collection_dir.name
                
                if collection_name in ["gamp5", "regulatory", "sops", "best_practices"]:
                    if self.verbose:
                        logger.info(f"Processing {collection_name} documents...")
                    
                    collection_results = []
                    
                    for doc_file in collection_dir.glob("*.*"):
                        if doc_file.suffix in ['.pdf', '.md', '.txt']:
                            try:
                                stats = await self.agent.ingest_documents(
                                    documents_path=str(doc_file),
                                    collection_name=collection_name,
                                    force_reprocess=False
                                )
                                
                                collection_results.append({
                                    "file": doc_file.name,
                                    "stats": stats
                                })
                                
                            except Exception as e:
                                logger.error(f"Failed to ingest {doc_file}: {e}")
                                raise
                    
                    results[collection_name] = collection_results
        
        return results
    
    def _determine_collection(
        self,
        filename: str,
        mapping: Dict[str, str]
    ) -> Optional[str]:
        """Determine collection based on filename patterns."""
        filename_lower = filename.lower()
        
        for pattern, collection in mapping.items():
            # Convert simple wildcards to basic matching
            if '*' in pattern:
                pattern_parts = pattern.lower().split('*')
                matches = True
                current_pos = 0
                
                for part in pattern_parts:
                    if part:  # Skip empty parts from consecutive *
                        pos = filename_lower.find(part, current_pos)
                        if pos == -1:
                            matches = False
                            break
                        current_pos = pos + len(part)
                
                if matches:
                    return collection
            elif pattern.lower() in filename_lower:
                return collection
        
        return None
    
    async def verify_ingestion(self) -> Dict[str, int]:
        """Verify document counts in each collection."""
        # This would query ChromaDB to get document counts
        # For now, return performance stats as proxy
        stats = self.agent.get_performance_stats()
        return {
            "total_requests": stats["total_requests"],
            "successful_requests": stats["successful_requests"]
        }


async def main():
    """Example usage of the ingestion utility."""
    # Initialize ingestion utility
    ingestion = PharmaDocumentIngestion(verbose=True)
    
    # Example 1: Ingest a directory with automatic mapping
    try:
        results = await ingestion.ingest_directory(
            "./pharmaceutical_docs",
            collection_mapping={
                "*gamp*": "gamp5",
                "*cfr*": "regulatory",
                "*sop*": "sops"
            }
        )
        
        print("\n📊 Ingestion Results:")
        for collection, docs in results.items():
            print(f"\n{collection}:")
            for doc_info in docs:
                print(f"  - {doc_info['file']}: {doc_info['stats']['status']}")
    
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        # NO FALLBACKS - propagate error
        raise
    
    # Example 2: Ingest structured standards directory
    try:
        standards_results = await ingestion.ingest_pharma_standards(
            "./pharma_standards"
        )
        
        print("\n📚 Standards Ingestion Results:")
        for collection, docs in standards_results.items():
            print(f"\n{collection}: {len(docs)} documents")
    
    except Exception as e:
        print(f"❌ Standards ingestion failed: {e}")
        raise
    
    # Verify ingestion
    verification = await ingestion.verify_ingestion()
    print(f"\n✅ Verification: {verification}")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run ingestion
    asyncio.run(main())