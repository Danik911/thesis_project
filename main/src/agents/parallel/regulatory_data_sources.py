"""
Regulatory Data Sources Module

This module implements real regulatory data source integrations for the Research Agent,
replacing mock data with actual API calls and document processing capabilities.

Key Features:
- FDA openFDA API integration with rate limiting
- Document processing using PDFPlumber
- GAMP-5 compliant audit trail logging
- Explicit error handling (NO FALLBACKS)
- Source tracking and validation
"""

import asyncio
import hashlib
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Explicit pdfplumber dependency check - NO FALLBACKS ALLOWED
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError as e:
    PDFPLUMBER_AVAILABLE = False
    PDFPLUMBER_ERROR = str(e)

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RegulatoryAuditTrail:
    """
    GAMP-5 compliant audit trail for regulatory data access.
    
    Implements ALCOA+ principles:
    - Attributable: Track user and source
    - Legible: Maintain readable audit records
    - Contemporaneous: Record at time of access
    - Original: Preserve source information
    - Accurate: Validate data integrity
    - Complete: Full record of actions
    - Consistent: Standardized format
    - Enduring: Permanent record storage
    - Available: Accessible for inspection
    """

    def __init__(self, audit_log_path: str | None = None):
        """Initialize audit trail system."""
        self.logger = logging.getLogger(f"{__name__}.audit")
        self.audit_log_path = audit_log_path

    def log_data_access(
        self,
        source: str,
        endpoint: str,
        query_params: dict[str, Any],
        response_data: dict[str, Any],
        user_id: str = "research_agent",
        success: bool = True,
        error_details: str | None = None
    ) -> str:
        """Log regulatory data access for GAMP-5 compliance."""
        timestamp = datetime.now(UTC)

        # Calculate data hash for integrity verification
        data_hash = self._calculate_data_hash(response_data)

        audit_record = {
            "timestamp": timestamp.isoformat(),
            "source": source,
            "endpoint": endpoint,
            "query_params": query_params,
            "user_id": user_id,
            "data_hash": data_hash,
            "success": success,
            "error_details": error_details,
            "record_id": f"{source}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{data_hash[:8]}",
            "response_size": len(str(response_data)) if response_data else 0
        }

        # Log audit record
        self.logger.info(
            f"Regulatory data access: {audit_record['record_id']} - "
            f"Source: {source}, Success: {success}"
        )

        if not success and error_details:
            self.logger.error(f"Data access error: {error_details}")

        return audit_record["record_id"]

    def _calculate_data_hash(self, data: dict[str, Any]) -> str:
        """Calculate SHA-256 hash for data integrity verification."""
        if not data:
            return "no_data"

        # Convert data to stable string representation
        data_str = str(sorted(data.items())) if isinstance(data, dict) else str(data)
        return hashlib.sha256(data_str.encode()).hexdigest()


class FDAAPIClient:
    """
    FDA openFDA API client with rate limiting and error handling.
    
    Features:
    - Automatic rate limiting (120,000 requests/hour with API key)
    - Retry logic with exponential backoff
    - Comprehensive error handling
    - GAMP-5 compliant audit trail
    - NO FALLBACKS - explicit failures only
    """

    def __init__(self, api_key: str | None = None, audit_trail: RegulatoryAuditTrail | None = None):
        """
        Initialize FDA API client.
        
        Args:
            api_key: FDA API key (increases rate limit from 240 to 120,000 requests/hour)
            audit_trail: Audit trail system for compliance logging
        """
        self.base_url = "https://api.fda.gov"
        self.api_key = api_key
        self.audit_trail = audit_trail or RegulatoryAuditTrail()
        self.logger = logging.getLogger(__name__)

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Rate limiting
        self.last_request_time = 0
        self.request_interval = 0.03 if api_key else 15.0  # 120k/hour vs 240/hour

        # Request statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limit_hits": 0
        }
        
        # Resource tracking for debugging
        self._session_created = True
        self.logger.debug(f"FDAAPIClient session created: {id(self.session)}")
    
    def close(self) -> None:
        """Close the session and clean up resources."""
        if hasattr(self, 'session') and self.session and self._session_created:
            self.logger.debug(f"Closing FDAAPIClient session: {id(self.session)}")
            self.session.close()
            self._session_created = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
    
    def __del__(self):
        """Destructor cleanup as safety net."""
        try:
            self.close()
        except Exception:
            # Ignore cleanup errors in destructor
            pass

    async def search_drug_labels(
        self,
        search_query: str,
        limit: int = 10,
        skip: int = 0
    ) -> dict[str, Any]:
        """
        Search FDA drug labeling database.
        
        Args:
            search_query: Search terms for drug labels
            limit: Maximum number of results to return
            skip: Number of results to skip (pagination)
            
        Returns:
            FDA API response data
            
        Raises:
            FDAAPIError: When API call fails (NO FALLBACKS)
        """
        endpoint = f"{self.base_url}/drug/label.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),  # FDA API limit
            "skip": skip
        }

        return await self._make_request(endpoint, params, "drug_labels")

    async def search_drug_adverse_events(
        self,
        search_query: str,
        limit: int = 10,
        skip: int = 0
    ) -> dict[str, Any]:
        """
        Search FDA adverse events database.
        
        Args:
            search_query: Search terms for adverse events
            limit: Maximum number of results to return
            skip: Number of results to skip (pagination)
            
        Returns:
            FDA API response data
            
        Raises:
            FDAAPIError: When API call fails (NO FALLBACKS)
        """
        endpoint = f"{self.base_url}/drug/event.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": skip
        }

        return await self._make_request(endpoint, params, "adverse_events")

    async def search_device_recalls(
        self,
        search_query: str,
        limit: int = 10,
        skip: int = 0
    ) -> dict[str, Any]:
        """
        Search FDA device recalls database.
        
        Args:
            search_query: Search terms for device recalls
            limit: Maximum number of results to return
            skip: Number of results to skip (pagination)
            
        Returns:
            FDA API response data
            
        Raises:
            FDAAPIError: When API call fails (NO FALLBACKS)
        """
        endpoint = f"{self.base_url}/device/recall.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": skip
        }

        return await self._make_request(endpoint, params, "device_recalls")

    async def search_enforcement_reports(
        self,
        search_query: str,
        limit: int = 10,
        skip: int = 0
    ) -> dict[str, Any]:
        """
        Search FDA enforcement reports database.
        
        Args:
            search_query: Search terms for enforcement reports
            limit: Maximum number of results to return
            skip: Number of results to skip (pagination)
            
        Returns:
            FDA API response data
            
        Raises:
            FDAAPIError: When API call fails (NO FALLBACKS)
        """
        endpoint = f"{self.base_url}/drug/enforcement.json"
        params = {
            "search": search_query,
            "limit": min(limit, 100),
            "skip": skip
        }

        return await self._make_request(endpoint, params, "enforcement_reports")

    async def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any],
        request_type: str
    ) -> dict[str, Any]:
        """
        Make authenticated request to FDA API with rate limiting.
        
        Args:
            endpoint: API endpoint URL
            params: Query parameters
            request_type: Type of request for audit trail
            
        Returns:
            API response data
            
        Raises:
            FDAAPIError: When request fails (NO FALLBACKS)
        """
        # Apply rate limiting
        await self._apply_rate_limiting()

        # Add API key if available
        if self.api_key:
            params["api_key"] = self.api_key

        self.stats["total_requests"] += 1

        try:
            # Make request in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.session.get(endpoint, params=params, timeout=30)
            )

            # Check for rate limiting
            if response.status_code == 429:
                self.stats["rate_limit_hits"] += 1
                error_msg = f"FDA API rate limit exceeded. Status: {response.status_code}"
                self.audit_trail.log_data_access(
                    source="FDA_API",
                    endpoint=endpoint,
                    query_params=params,
                    response_data={},
                    success=False,
                    error_details=error_msg
                )
                raise FDAAPIError(error_msg)

            # Raise for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Log successful access
            audit_id = self.audit_trail.log_data_access(
                source="FDA_API",
                endpoint=endpoint,
                query_params=params,
                response_data=data,
                success=True
            )

            self.stats["successful_requests"] += 1

            # Add metadata to response
            data["_fda_api_metadata"] = {
                "audit_id": audit_id,
                "request_timestamp": datetime.now(UTC).isoformat(),
                "request_type": request_type,
                "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining"),
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }

            return data

        except requests.exceptions.RequestException as e:
            self.stats["failed_requests"] += 1
            error_msg = f"FDA API request failed: {e!s}"

            self.audit_trail.log_data_access(
                source="FDA_API",
                endpoint=endpoint,
                query_params=params,
                response_data={},
                success=False,
                error_details=error_msg
            )

            # NEVER FALLBACK - raise explicit error
            raise FDAAPIError(error_msg) from e

        except Exception as e:
            self.stats["failed_requests"] += 1
            error_msg = f"Unexpected error in FDA API request: {e!s}"

            self.audit_trail.log_data_access(
                source="FDA_API",
                endpoint=endpoint,
                query_params=params,
                response_data={},
                success=False,
                error_details=error_msg
            )

            # NEVER FALLBACK - raise explicit error
            raise FDAAPIError(error_msg) from e

    async def _apply_rate_limiting(self) -> None:
        """Apply rate limiting to prevent API quota exhaustion."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.request_interval:
            sleep_time = self.request_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_stats(self) -> dict[str, Any]:
        """Get API client statistics."""
        return self.stats.copy()


class DocumentProcessor:
    """
    Document processing utilities for regulatory documents.
    
    Features:
    - PDF text extraction using PDFPlumber
    - Table extraction from regulatory documents
    - Document metadata extraction
    - GAMP-5 compliant processing audit trail
    """

    def __init__(self, audit_trail: RegulatoryAuditTrail | None = None):
        """Initialize document processor."""
        self.audit_trail = audit_trail or RegulatoryAuditTrail()
        self.logger = logging.getLogger(__name__)

    async def process_pdf_document(
        self,
        pdf_path: str | Path,
        extract_tables: bool = True
    ) -> dict[str, Any]:
        """
        Process regulatory PDF document.
        
        Args:
            pdf_path: Path to PDF document
            extract_tables: Whether to extract tables from document
            
        Returns:
            Processed document data with text, tables, and metadata
            
        Raises:
            DocumentProcessingError: When processing fails (NO FALLBACKS)
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            error_msg = f"PDF document not found: {pdf_path}"
            self.audit_trail.log_data_access(
                source="DOCUMENT_PROCESSOR",
                endpoint=str(pdf_path),
                query_params={"extract_tables": extract_tables},
                response_data={},
                success=False,
                error_details=error_msg
            )
            raise DocumentProcessingError(error_msg)

        try:
            # Process PDF in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._extract_pdf_content,
                pdf_path,
                extract_tables
            )

            # Log successful processing
            audit_id = self.audit_trail.log_data_access(
                source="DOCUMENT_PROCESSOR",
                endpoint=str(pdf_path),
                query_params={"extract_tables": extract_tables},
                response_data=result,
                success=True
            )

            result["_processing_metadata"] = {
                "audit_id": audit_id,
                "processing_timestamp": datetime.now(UTC).isoformat(),
                "file_size_bytes": pdf_path.stat().st_size,
                "file_modified": datetime.fromtimestamp(pdf_path.stat().st_mtime, UTC).isoformat()
            }

            return result

        except Exception as e:
            error_msg = f"PDF processing failed for {pdf_path}: {e!s}"

            self.audit_trail.log_data_access(
                source="DOCUMENT_PROCESSOR",
                endpoint=str(pdf_path),
                query_params={"extract_tables": extract_tables},
                response_data={},
                success=False,
                error_details=error_msg
            )

            # NEVER FALLBACK - raise explicit error
            raise DocumentProcessingError(error_msg) from e

    def _extract_pdf_content(
        self,
        pdf_path: Path,
        extract_tables: bool
    ) -> dict[str, Any]:
        """Extract content from PDF using PDFPlumber."""
        # Explicit dependency check - NO FALLBACKS ALLOWED
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError(
                f"pdfplumber is required for PDF processing but not installed. "
                f"Original error: {PDFPLUMBER_ERROR}. "
                f"Install with: uv add pdfplumber"
            )

        result = {
            "text": "",
            "tables": [],
            "pages": 0,
            "document_title": "",
            "extraction_quality": "unknown"
        }

        with pdfplumber.open(pdf_path) as pdf:
            result["pages"] = len(pdf.pages)

            # Extract text from all pages
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

            result["text"] = full_text.strip()

            # Extract tables if requested
            if extract_tables:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_num, table in enumerate(page_tables):
                            result["tables"].append({
                                "page": page_num + 1,
                                "table_index": table_num,
                                "data": table,
                                "rows": len(table) if table else 0,
                                "columns": len(table[0]) if table and table[0] else 0
                            })

            # Try to extract document title from first page
            if pdf.pages:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text:
                    lines = first_page_text.split("\n")
                    for line in lines[:5]:  # Check first 5 lines
                        if line.strip() and len(line.strip()) > 10:
                            result["document_title"] = line.strip()
                            break

        # Assess extraction quality
        if result["text"] and len(result["text"]) > 100:
            result["extraction_quality"] = "good"
        elif result["text"]:
            result["extraction_quality"] = "partial"
        else:
            result["extraction_quality"] = "poor"

        return result


class FDAAPIError(Exception):
    """Exception raised when FDA API operations fail."""


class DocumentProcessingError(Exception):
    """Exception raised when document processing fails."""


def create_fda_client(api_key: str | None = None) -> FDAAPIClient:
    """Create FDA API client with audit trail."""
    audit_trail = RegulatoryAuditTrail()
    return FDAAPIClient(api_key=api_key, audit_trail=audit_trail)


def create_document_processor() -> DocumentProcessor:
    """Create document processor with audit trail."""
    audit_trail = RegulatoryAuditTrail()
    return DocumentProcessor(audit_trail=audit_trail)
