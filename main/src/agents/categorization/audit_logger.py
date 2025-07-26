"""
Audit log persistence for GAMP-5 categorization error handling.

Provides file-based audit logging with rotation and regulatory compliance features.
"""

import json
import os
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
import threading
from dataclasses import asdict

from main.src.agents.categorization.error_handler import AuditLogEntry


class AuditLogPersistence:
    """
    Manages persistent audit logging for categorization errors.
    
    Features:
    - JSON file-based storage
    - Automatic rotation by size/date
    - Thread-safe operations
    - Regulatory compliance formatting
    """
    
    def __init__(
        self,
        log_dir: str = "logs/categorization",
        max_file_size_mb: int = 10,
        max_files: int = 10,
        enable_rotation: bool = True
    ):
        """
        Initialize audit log persistence.
        
        Args:
            log_dir: Directory for audit log files
            max_file_size_mb: Maximum size per log file in MB
            max_files: Maximum number of log files to keep
            enable_rotation: Enable automatic log rotation
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.max_files = max_files
        self.enable_rotation = enable_rotation
        
        # Thread lock for file operations
        self._lock = threading.Lock()
        
        # Current log file
        self._current_file = self._get_current_log_file()
        
    def _get_current_log_file(self) -> Path:
        """Get or create the current log file."""
        today = datetime.now(UTC).strftime("%Y%m%d")
        base_name = f"gamp5_audit_{today}"
        
        # Find the latest file for today
        existing_files = list(self.log_dir.glob(f"{base_name}_*.json"))
        
        if not existing_files:
            # Create first file of the day
            return self.log_dir / f"{base_name}_001.json"
        
        # Get the latest file
        existing_files.sort()
        latest_file = existing_files[-1]
        
        # Check if rotation needed
        if self.enable_rotation and latest_file.stat().st_size >= self.max_file_size:
            # Extract number and increment
            parts = latest_file.stem.split('_')
            num = int(parts[-1])
            new_num = str(num + 1).zfill(3)
            return self.log_dir / f"{base_name}_{new_num}.json"
        
        return latest_file
        
    def write_entry(self, entry: AuditLogEntry) -> bool:
        """
        Write an audit log entry to persistent storage.
        
        Args:
            entry: Audit log entry to persist
            
        Returns:
            bool: True if successful
        """
        try:
            with self._lock:
                # Convert entry to dict
                entry_dict = self._entry_to_dict(entry)
                
                # Check if rotation needed
                if self.enable_rotation:
                    self._check_rotation()
                
                # Append to current file
                with open(self._current_file, 'a') as f:
                    json.dump(entry_dict, f)
                    f.write('\n')  # Newline-delimited JSON
                    
                return True
                
        except Exception as e:
            print(f"Error writing audit log: {e}")
            return False
            
    def write_batch(self, entries: List[AuditLogEntry]) -> int:
        """
        Write multiple audit log entries.
        
        Args:
            entries: List of audit log entries
            
        Returns:
            int: Number of successfully written entries
        """
        success_count = 0
        
        with self._lock:
            for entry in entries:
                if self.write_entry(entry):
                    success_count += 1
                    
        return success_count
        
    def read_entries(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Read audit log entries from persistent storage.
        
        Args:
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            limit: Maximum entries to return
            
        Returns:
            List of audit log entries as dictionaries
        """
        entries = []
        
        # Get all log files
        log_files = sorted(self.log_dir.glob("gamp5_audit_*.json"))
        
        for log_file in log_files:
            if len(entries) >= limit:
                break
                
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if len(entries) >= limit:
                            break
                            
                        entry = json.loads(line.strip())
                        
                        # Apply date filters
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        
                        if start_date and entry_time < start_date:
                            continue
                        if end_date and entry_time > end_date:
                            continue
                            
                        entries.append(entry)
                        
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
                
        return entries
        
    def _entry_to_dict(self, entry: AuditLogEntry) -> Dict[str, Any]:
        """Convert AuditLogEntry to dictionary for JSON serialization."""
        # Convert dataclass to dict
        entry_dict = asdict(entry)
        
        # Handle special types
        if entry.timestamp:
            entry_dict['timestamp'] = entry.timestamp.isoformat()
            
        if entry.original_category:
            entry_dict['original_category'] = entry.original_category.value
            
        if entry.fallback_category:
            entry_dict['fallback_category'] = entry.fallback_category.value
            
        # Handle nested error object
        if entry.error:
            error_dict = asdict(entry.error)
            error_dict['error_type'] = entry.error.error_type.value
            error_dict['severity'] = entry.error.severity.value
            error_dict['timestamp'] = entry.error.timestamp.isoformat()
            entry_dict['error'] = error_dict
            
        return entry_dict
        
    def _check_rotation(self):
        """Check if log rotation is needed."""
        if not self._current_file.exists():
            return
            
        # Check file size
        if self._current_file.stat().st_size >= self.max_file_size:
            self._current_file = self._get_current_log_file()
            
        # Clean old files if needed
        self._clean_old_files()
        
    def _clean_old_files(self):
        """Remove old log files beyond max_files limit."""
        log_files = sorted(self.log_dir.glob("gamp5_audit_*.json"))
        
        if len(log_files) > self.max_files:
            # Remove oldest files
            for old_file in log_files[:-self.max_files]:
                try:
                    old_file.unlink()
                except Exception as e:
                    print(f"Error removing old log file {old_file}: {e}")
                    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        total_entries = 0
        total_size = 0
        file_count = 0
        
        for log_file in self.log_dir.glob("gamp5_audit_*.json"):
            file_count += 1
            total_size += log_file.stat().st_size
            
            # Count entries
            try:
                with open(log_file, 'r') as f:
                    total_entries += sum(1 for _ in f)
            except:
                pass
                
        return {
            "total_entries": total_entries,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "log_directory": str(self.log_dir),
            "max_file_size_mb": self.max_file_size // (1024 * 1024),
            "max_files": self.max_files
        }
        

def create_regulatory_report(
    log_dir: str = "logs/categorization",
    output_file: str = "categorization_audit_report.txt"
) -> str:
    """
    Generate a regulatory compliance report from audit logs.
    
    Args:
        log_dir: Directory containing audit logs
        output_file: Output file for the report
        
    Returns:
        str: Path to generated report
    """
    persistence = AuditLogPersistence(log_dir=log_dir)
    
    # Read all entries
    entries = persistence.read_entries(limit=10000)
    
    # Generate report
    report_lines = [
        "GAMP-5 CATEGORIZATION AUDIT REPORT",
        "=" * 60,
        f"Generated: {datetime.now(UTC).isoformat()}",
        f"Total Entries: {len(entries)}",
        "",
        "21 CFR PART 11 COMPLIANCE SUMMARY",
        "-" * 60,
        ""
    ]
    
    # Analyze entries
    error_types = {}
    fallback_count = 0
    documents_processed = set()
    
    for entry in entries:
        if entry.get('action') == 'FALLBACK_CATEGORIZATION':
            fallback_count += 1
            
        if entry.get('error_type'):
            error_types[entry['error_type']] = error_types.get(entry['error_type'], 0) + 1
            
        documents_processed.add(entry.get('document_name', 'Unknown'))
        
    # Add summary
    report_lines.extend([
        f"Documents Processed: {len(documents_processed)}",
        f"Fallback Events: {fallback_count}",
        f"Error Types Encountered: {len(error_types)}",
        "",
        "ERROR DISTRIBUTION:",
        "-" * 30
    ])
    
    for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
        report_lines.append(f"  {error_type}: {count}")
        
    # Add detailed entries
    report_lines.extend([
        "",
        "",
        "DETAILED AUDIT TRAIL",
        "=" * 60,
        ""
    ])
    
    for entry in entries[-100:]:  # Last 100 entries
        report_lines.extend([
            f"Entry ID: {entry.get('entry_id', 'Unknown')}",
            f"Timestamp: {entry.get('timestamp', 'Unknown')}",
            f"Document: {entry.get('document_name', 'Unknown')}",
            f"Action: {entry.get('action', 'Unknown')}",
            f"Decision: {entry.get('decision_rationale', 'Unknown')[:100]}...",
            "-" * 40,
            ""
        ])
        
    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))
        
    return output_file