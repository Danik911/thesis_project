"""
Pharmaceutical Document Loader - Simple implementation for E2E testing
"""
from pathlib import Path
from typing import Any, Dict


class PharmaceuticalDocumentLoader:
    """Simple document loader for testing purposes."""
    
    def __init__(self):
        pass
        
    def load_document(self, file_path: str | Path) -> Dict[str, Any]:
        """
        Load and return document content.
        
        Args:
            file_path: Path to the document to load
            
        Returns:
            Dict containing document content and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
            
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {
            "content": content,
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "content_type": "text/plain"
        }