"""
Unified trace configuration for pharmaceutical workflow monitoring.
Ensures all trace data is stored in consistent locations for compliance.
"""

import os
from pathlib import Path


class TraceConfig:
    """Central configuration for all trace storage locations."""

    # Base directories
    BASE_LOG_DIR = Path("logs")
    BASE_MONITORING_DIR = Path("docs/reports/monitoring")

    # Primary trace storage (consolidate all traces here)
    PRIMARY_TRACE_DIR = BASE_LOG_DIR / "traces"

    # Phoenix export directory
    PHOENIX_EXPORT_DIR = BASE_MONITORING_DIR / "phoenix_data"

    # Event logs
    EVENT_LOG_DIR = BASE_LOG_DIR / "events"

    # Audit logs
    AUDIT_LOG_DIR = BASE_LOG_DIR / "audit"

    @classmethod
    def ensure_directories(cls):
        """Ensure all trace directories exist."""
        for dir_path in [
            cls.PRIMARY_TRACE_DIR,
            cls.PHOENIX_EXPORT_DIR,
            cls.EVENT_LOG_DIR,
            cls.AUDIT_LOG_DIR,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_trace_search_paths(cls) -> list[Path]:
        """Get all paths where traces might be stored."""
        return [
            cls.PRIMARY_TRACE_DIR,
            cls.PHOENIX_EXPORT_DIR,
            cls.EVENT_LOG_DIR,
        ]

    @classmethod
    def get_all_trace_files(cls, pattern: str = "*.jsonl") -> list[Path]:
        """Get all trace files from all possible locations."""
        trace_files = []
        for search_path in cls.get_trace_search_paths():
            if search_path.exists():
                trace_files.extend(search_path.glob(pattern))
        return sorted(trace_files)

    @classmethod
    def consolidate_traces(cls) -> dict:
        """Consolidate traces from all locations to primary directory."""
        consolidated = {
            "files_moved": 0,
            "files_found": 0,
            "errors": []
        }

        # Ensure primary directory exists
        cls.PRIMARY_TRACE_DIR.mkdir(parents=True, exist_ok=True)

        # Find all trace files not in primary directory
        for search_path in cls.get_trace_search_paths():
            if search_path == cls.PRIMARY_TRACE_DIR:
                continue

            if search_path.exists():
                for trace_file in search_path.glob("*.jsonl"):
                    consolidated["files_found"] += 1
                    try:
                        # Copy to primary directory with timestamp prefix
                        dest_file = cls.PRIMARY_TRACE_DIR / trace_file.name
                        if not dest_file.exists():
                            import shutil
                            shutil.copy2(trace_file, dest_file)
                            consolidated["files_moved"] += 1
                    except Exception as e:
                        consolidated["errors"].append({
                            "file": str(trace_file),
                            "error": str(e)
                        })

        return consolidated


# Environment variable overrides
if os.getenv("TRACE_PRIMARY_DIR"):
    TraceConfig.PRIMARY_TRACE_DIR = Path(os.getenv("TRACE_PRIMARY_DIR"))

if os.getenv("PHOENIX_EXPORT_DIR"):
    TraceConfig.PHOENIX_EXPORT_DIR = Path(os.getenv("PHOENIX_EXPORT_DIR"))
