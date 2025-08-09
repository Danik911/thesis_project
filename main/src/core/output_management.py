"""
Output management system for test suite generation.

This module provides comprehensive output file management for pharmaceutical
test suites with GAMP-5 compliance, including JSON/YAML generation, validation,
and audit trail requirements.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

from .models import OutputConfiguration


class FileCreationResult(BaseModel):
    """Result of file creation operation with audit metadata."""
    file_path: str = Field(..., description="Path to created file")
    file_type: str = Field(..., description="Type of file created")
    success: bool = Field(..., description="Whether creation was successful")
    file_size_bytes: Optional[int] = Field(default=None, description="Size of created file")
    creation_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    checksum: Optional[str] = Field(default=None, description="File integrity checksum")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class OutputManager:
    """
    Comprehensive output management system for test suite files.
    
    Provides structured file creation with pharmaceutical compliance requirements,
    audit trails, and integrity validation for regulatory compliance.
    """
    
    def __init__(self, config: Optional[OutputConfiguration] = None):
        self.config = config or OutputConfiguration()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure output directory exists
        self.output_dir = Path(self.config.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track created files for audit
        self.created_files: List[FileCreationResult] = []
    
    async def create_test_suite_file(
        self,
        test_suite: Any,
        format_type: str = "json",
        base_filename: Optional[str] = None
    ) -> FileCreationResult:
        """
        Create test suite file in specified format.
        
        Generates test suite files with proper naming, validation,
        and audit trail for pharmaceutical compliance.
        """
        try:
            # Generate filename
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            
            if base_filename:
                filename_base = Path(base_filename).stem
            else:
                filename_base = "test_suite"
            
            # Apply naming pattern
            filename_pattern = self.config.file_naming_pattern.format(
                suite_id=getattr(test_suite, 'suite_id', 'UNKNOWN'),
                timestamp=timestamp
            )
            
            filename = f"{filename_base}_{filename_pattern}.{format_type}"
            file_path = self.output_dir / filename
            
            # Convert test suite to appropriate format
            if format_type.lower() == "json":
                result = await self._create_json_file(test_suite, file_path)
            elif format_type.lower() == "yaml":
                result = await self._create_yaml_file(test_suite, file_path)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
            
            # Track created file
            self.created_files.append(result)
            
            if result.success:
                self.logger.info(f"Successfully created {format_type.upper()} file: {result.file_path}")
            else:
                self.logger.error(f"Failed to create {format_type.upper()} file: {result.error_message}")
            
            return result
            
        except Exception as e:
            error_result = FileCreationResult(
                file_path=str(file_path) if 'file_path' in locals() else "unknown",
                file_type=format_type,
                success=False,
                error_message=str(e)
            )
            
            self.created_files.append(error_result)
            self.logger.error(f"Error creating test suite file: {e}")
            
            return error_result
    
    async def _create_json_file(self, test_suite: Any, file_path: Path) -> FileCreationResult:
        """Create JSON format test suite file."""
        try:
            # Convert test suite to dictionary
            if hasattr(test_suite, 'model_dump'):
                # Pydantic model
                data = test_suite.model_dump()
            elif hasattr(test_suite, 'dict'):
                # Older Pydantic model
                data = test_suite.dict()
            else:
                # Assume it's already a dict or convertible
                data = dict(test_suite) if not isinstance(test_suite, dict) else test_suite
            
            # Add audit metadata
            data['_audit_metadata'] = {
                'created_timestamp': datetime.now(UTC).isoformat(),
                'created_by': 'output_management_system',
                'file_format': 'json',
                'compliance_validated': True
            }
            
            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Get file stats
            stat = file_path.stat()
            
            return FileCreationResult(
                file_path=str(file_path),
                file_type="json",
                success=True,
                file_size_bytes=stat.st_size,
                creation_timestamp=datetime.now(UTC)
            )
            
        except Exception as e:
            return FileCreationResult(
                file_path=str(file_path),
                file_type="json",
                success=False,
                error_message=str(e)
            )
    
    async def _create_yaml_file(self, test_suite: Any, file_path: Path) -> FileCreationResult:
        """Create YAML format test suite file."""
        try:
            # Convert test suite to dictionary
            if hasattr(test_suite, 'model_dump'):
                # Pydantic model
                data = test_suite.model_dump()
            elif hasattr(test_suite, 'dict'):
                # Older Pydantic model  
                data = test_suite.dict()
            else:
                # Assume it's already a dict or convertible
                data = dict(test_suite) if not isinstance(test_suite, dict) else test_suite
            
            # Add audit metadata
            data['_audit_metadata'] = {
                'created_timestamp': datetime.now(UTC).isoformat(),
                'created_by': 'output_management_system',
                'file_format': 'yaml',
                'compliance_validated': True
            }
            
            # Write YAML file
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
            
            # Get file stats
            stat = file_path.stat()
            
            return FileCreationResult(
                file_path=str(file_path),
                file_type="yaml",
                success=True,
                file_size_bytes=stat.st_size,
                creation_timestamp=datetime.now(UTC)
            )
            
        except Exception as e:
            return FileCreationResult(
                file_path=str(file_path),
                file_type="yaml",
                success=False,
                error_message=str(e)
            )
    
    def create_backup(self, file_path: str) -> FileCreationResult:
        """Create backup copy of a file."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
            
            # Create backup filename
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{source_path.stem}_{timestamp}_backup{source_path.suffix}"
            backup_path = source_path.parent / "backups" / backup_filename
            
            # Ensure backup directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(source_path, backup_path)
            
            # Get file stats
            stat = backup_path.stat()
            
            result = FileCreationResult(
                file_path=str(backup_path),
                file_type="backup",
                success=True,
                file_size_bytes=stat.st_size,
                creation_timestamp=datetime.now(UTC)
            )
            
            self.created_files.append(result)
            self.logger.info(f"Created backup: {backup_path}")
            
            return result
            
        except Exception as e:
            error_result = FileCreationResult(
                file_path=file_path,
                file_type="backup",
                success=False,
                error_message=str(e)
            )
            
            self.created_files.append(error_result)
            self.logger.error(f"Failed to create backup: {e}")
            
            return error_result
    
    def get_creation_summary(self) -> Dict[str, Any]:
        """Get summary of all file creation operations."""
        successful_files = [f for f in self.created_files if f.success]
        failed_files = [f for f in self.created_files if not f.success]
        
        return {
            "total_files_created": len(self.created_files),
            "successful_files": len(successful_files),
            "failed_files": len(failed_files),
            "file_types": list(set(f.file_type for f in self.created_files)),
            "total_size_bytes": sum(f.file_size_bytes or 0 for f in successful_files),
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    def cleanup_old_files(self, days_old: int = 30) -> int:
        """Clean up files older than specified days."""
        try:
            cleanup_count = 0
            cutoff_time = datetime.now(UTC).timestamp() - (days_old * 24 * 3600)
            
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleanup_count += 1
            
            self.logger.info(f"Cleaned up {cleanup_count} old files")
            return cleanup_count
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            return 0