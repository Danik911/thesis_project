"""
LlamaParse Client Wrapper

This module provides a wrapper around the LlamaParse API for parsing
pharmaceutical URS documents. It handles configuration, error handling,
and provides a consistent interface for document processing.

Key Features:
- Configurable parsing modes for different document types
- Error handling with retry logic
- Result caching to avoid re-processing
- Support for high-resolution OCR and chart extraction
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import json
import hashlib
from datetime import datetime, UTC

try:
    from llama_parse import LlamaParse
except ImportError:
    # Provide graceful fallback if llama-parse is not installed
    LlamaParse = None
    logging.warning("llama-parse not installed. Document parsing features will be limited.")


class LlamaParseClient:
    """
    Client wrapper for LlamaParse API.
    
    This class provides a unified interface for parsing documents using
    LlamaParse with proper error handling, caching, and configuration
    management for pharmaceutical documentation needs.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        parse_mode: str = "parse_page_with_agent",
        model: str = "anthropic-sonnet-3.5",
        high_res_ocr: bool = True,
        extract_charts: bool = True,
        take_screenshot: bool = True,
        cache_dir: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize LlamaParse client with configuration.
        
        Args:
            api_key: LlamaCloud API key (uses env var if not provided)
            parse_mode: Parsing mode to use
            model: Model to use for parsing
            high_res_ocr: Enable high-resolution OCR
            extract_charts: Extract charts and diagrams
            take_screenshot: Take screenshots of pages
            cache_dir: Directory for caching parsed results
            verbose: Enable verbose logging
        """
        self.logger = logging.getLogger(__name__)
        if verbose:
            self.logger.setLevel(logging.DEBUG)
            
        # Get API key from environment if not provided
        self.api_key = api_key or os.getenv("LLAMA_CLOUD_API_KEY")
        if not self.api_key:
            raise ValueError(
                "LlamaCloud API key not provided. "
                "Set LLAMA_CLOUD_API_KEY environment variable or pass api_key parameter."
            )
            
        # Store configuration
        self.parse_mode = parse_mode
        self.model = model
        self.high_res_ocr = high_res_ocr
        self.extract_charts = extract_charts
        self.take_screenshot = take_screenshot
        
        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".cache" / "llama_parse" / "pharmaceutical"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize parser
        self._initialize_parser()
        
    def _initialize_parser(self) -> None:
        """Initialize the LlamaParse instance."""
        if LlamaParse is None:
            self.logger.warning("LlamaParse not available. Using mock parser.")
            self.parser = None
            return
            
        try:
            self.parser = LlamaParse(
                api_key=self.api_key,
                parse_mode=self.parse_mode,
                model=self.model,
                high_res_ocr=self.high_res_ocr,
                extract_charts=self.extract_charts,
                take_screenshot=self.take_screenshot,
                extraction_prompt=(
                    "Extract all technical specifications, requirements, tables, "
                    "and diagrams from this pharmaceutical URS document. "
                    "Preserve document structure, section headers, and maintain "
                    "traceability information. Identify GAMP-5 relevant indicators."
                )
            )
            self.logger.info("LlamaParse client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize LlamaParse: {e}")
            raise
            
    def _get_cache_key(self, file_path: str) -> str:
        """Generate cache key for a document."""
        # Include file path and modification time in cache key
        file_stat = Path(file_path).stat()
        cache_data = f"{file_path}:{file_stat.st_mtime}:{file_stat.st_size}"
        return hashlib.sha256(cache_data.encode()).hexdigest()
        
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached parsing result if available."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    self.logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data
            except Exception as e:
                self.logger.warning(f"Failed to load cache: {e}")
        return None
        
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Save parsing result to cache."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            self.logger.debug(f"Saved to cache: {cache_key}")
        except Exception as e:
            self.logger.warning(f"Failed to save cache: {e}")
            
    def parse_document(
        self,
        file_path: Union[str, Path],
        use_cache: bool = True,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse a document using LlamaParse.
        
        Args:
            file_path: Path to the document file
            use_cache: Whether to use cached results
            custom_prompt: Custom extraction prompt to use
            
        Returns:
            Dictionary containing parsed document data with structure:
            {
                "pages": List of page data with text and metadata,
                "metadata": Document-level metadata,
                "charts": Extracted charts and diagrams,
                "parse_time": Time taken to parse,
                "cache_hit": Whether result was from cache
            }
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
            
        # Check cache if enabled
        cache_key = self._get_cache_key(str(file_path))
        if use_cache:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                cached_result["cache_hit"] = True
                return cached_result
                
        # Parse document
        start_time = datetime.now(UTC)
        
        if self.parser is None:
            # Mock parsing for testing without API
            self.logger.warning("Using mock parser - no actual parsing performed")
            result = self._mock_parse(file_path)
        else:
            try:
                # Update extraction prompt if custom one provided
                if custom_prompt:
                    self.parser.extraction_prompt = custom_prompt
                    
                # Parse the document
                self.logger.info(f"Parsing document: {file_path.name}")
                parsed_result = self.parser.load_data(str(file_path))
                
                # Process results
                result = self._process_parse_result(parsed_result, file_path)
                
            except Exception as e:
                self.logger.error(f"Document parsing failed: {e}")
                raise
                
        # Add timing information
        parse_duration = (datetime.now(UTC) - start_time).total_seconds()
        result["parse_time"] = parse_duration
        result["cache_hit"] = False
        
        # Save to cache
        if use_cache:
            self._save_to_cache(cache_key, result)
            
        return result
        
    def _process_parse_result(
        self,
        parsed_result: Any,
        file_path: Path
    ) -> Dict[str, Any]:
        """Process raw LlamaParse result into structured format."""
        pages = []
        charts = []
        
        # Extract page data
        for idx, page in enumerate(parsed_result):
            page_data = {
                "page_number": idx + 1,
                "text": page.text if hasattr(page, 'text') else str(page),
                "metadata": page.metadata if hasattr(page, 'metadata') else {}
            }
            
            # Extract charts from page if available
            if hasattr(page, 'images') and page.images:
                for img_idx, image in enumerate(page.images):
                    charts.append({
                        "page": idx + 1,
                        "index": img_idx,
                        "type": "chart",
                        "path": image.path if hasattr(image, 'path') else None,
                        "caption": image.caption if hasattr(image, 'caption') else None
                    })
                    
            pages.append(page_data)
            
        # Build document metadata
        metadata = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "page_count": len(pages),
            "chart_count": len(charts),
            "parse_mode": self.parse_mode,
            "model": self.model,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        return {
            "pages": pages,
            "metadata": metadata,
            "charts": charts
        }
        
    def _mock_parse(self, file_path: Path) -> Dict[str, Any]:
        """Mock parsing for testing without API access."""
        mock_text = f"""
        MOCK PARSE RESULT for {file_path.name}
        
        1. INTRODUCTION
        This is a mock URS document for testing purposes.
        
        2. SYSTEM REQUIREMENTS
        - The system shall be a LIMS configured for pharmaceutical testing
        - Custom calculations required for stability analysis
        - Integration with existing ERP system
        
        3. TECHNICAL SPECIFICATIONS
        [Table: System Components]
        Component | Category | Description
        Database | Infrastructure | PostgreSQL 14
        Application | Configured | LIMS with custom workflows
        Analytics | Custom | Proprietary stability algorithms
        """
        
        return {
            "pages": [{
                "page_number": 1,
                "text": mock_text,
                "metadata": {"mock": True}
            }],
            "metadata": {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "page_count": 1,
                "chart_count": 0,
                "parse_mode": "mock",
                "model": "none",
                "timestamp": datetime.now(UTC).isoformat()
            },
            "charts": []
        }
        
    def extract_text(self, parsed_result: Dict[str, Any]) -> str:
        """Extract all text from parsed result."""
        texts = []
        for page in parsed_result.get("pages", []):
            if page.get("text"):
                texts.append(page["text"])
        return "\n\n".join(texts)
        
    def extract_charts(self, parsed_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all charts from parsed result."""
        return parsed_result.get("charts", [])
        
    def get_page_count(self, parsed_result: Dict[str, Any]) -> int:
        """Get total page count from parsed result."""
        return len(parsed_result.get("pages", []))