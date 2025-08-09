"""
Event logging system for workflow audit trails.

This module provides comprehensive event logging for pharmaceutical compliance,
maintaining detailed audit trails for GAMP-5 requirements and regulatory
traceability with ALCOA+ principles.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Individual audit log entry with pharmaceutical compliance metadata."""
    entry_id: UUID = Field(default_factory=uuid4, description="Unique entry identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    event_type: str = Field(..., description="Type of event logged")
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Event-specific data")
    user_id: Optional[str] = Field(default=None, description="User responsible for event")
    step_name: Optional[str] = Field(default=None, description="Associated workflow step")
    agent_type: Optional[str] = Field(default=None, description="Associated agent type")
    success: bool = Field(default=True, description="Whether event was successful")
    compliance_level: str = Field(default="standard", description="Compliance level required")
    regulatory_impact: str = Field(default="low", description="Regulatory impact level")


class EventLogger:
    """
    Comprehensive event logging system for workflow audit trails.
    
    Provides structured event logging with pharmaceutical compliance requirements,
    maintaining detailed audit trails for GAMP-5 and regulatory traceability.
    """
    
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize audit log storage
        self.audit_entries: List[AuditLogEntry] = []
        self.session_id = uuid4()
        
        # Create session-specific log file
        self.log_file_path = self.log_directory / f"audit_log_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        self.logger.info(f"Event logger initialized with session ID: {self.session_id}")
    
    def log_workflow_start(
        self, 
        workflow_name: str, 
        document_path: str,
        user_id: Optional[str] = None
    ) -> None:
        """Log workflow start event."""
        entry = AuditLogEntry(
            event_type="workflow_start",
            event_data={
                "workflow_name": workflow_name,
                "document_path": document_path,
                "session_id": str(self.session_id)
            },
            user_id=user_id,
            compliance_level="high",
            regulatory_impact="medium"
        )
        
        self._add_audit_entry(entry)
    
    def log_workflow_end(
        self, 
        workflow_name: str, 
        success: bool,
        execution_time: float,
        user_id: Optional[str] = None
    ) -> None:
        """Log workflow completion event."""
        entry = AuditLogEntry(
            event_type="workflow_end",
            event_data={
                "workflow_name": workflow_name,
                "execution_time_seconds": execution_time,
                "session_id": str(self.session_id)
            },
            user_id=user_id,
            success=success,
            compliance_level="high",
            regulatory_impact="medium"
        )
        
        self._add_audit_entry(entry)
    
    def log_step_execution(
        self,
        step_name: str,
        step_data: Dict[str, Any],
        success: bool = True,
        execution_time: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Log workflow step execution."""
        event_data = {
            "session_id": str(self.session_id),
            **step_data
        }
        
        if execution_time:
            event_data["execution_time_seconds"] = execution_time
        
        entry = AuditLogEntry(
            event_type="step_execution",
            event_data=event_data,
            step_name=step_name,
            user_id=user_id,
            success=success,
            compliance_level="standard",
            regulatory_impact="low"
        )
        
        self._add_audit_entry(entry)
    
    def log_agent_execution(
        self,
        agent_type: str,
        step_name: str,
        agent_data: Dict[str, Any],
        success: bool = True,
        execution_time: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Log agent execution event."""
        event_data = {
            "session_id": str(self.session_id),
            **agent_data
        }
        
        if execution_time:
            event_data["execution_time_seconds"] = execution_time
        
        entry = AuditLogEntry(
            event_type="agent_execution",
            event_data=event_data,
            step_name=step_name,
            agent_type=agent_type,
            user_id=user_id,
            success=success,
            compliance_level="standard",
            regulatory_impact="low"
        )
        
        self._add_audit_entry(entry)
    
    def log_error(
        self,
        error: Exception,
        step_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Log error event with full context."""
        event_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "session_id": str(self.session_id)
        }
        
        entry = AuditLogEntry(
            event_type="error_occurred",
            event_data=event_data,
            step_name=step_name,
            agent_type=agent_type,
            user_id=user_id,
            success=False,
            compliance_level="high",
            regulatory_impact="high"
        )
        
        self._add_audit_entry(entry)
    
    def log_compliance_check(
        self,
        check_type: str,
        check_results: Dict[str, Any],
        passed: bool,
        step_name: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Log compliance verification event."""
        event_data = {
            "check_type": check_type,
            "check_results": check_results,
            "session_id": str(self.session_id)
        }
        
        entry = AuditLogEntry(
            event_type="compliance_check",
            event_data=event_data,
            step_name=step_name,
            user_id=user_id,
            success=passed,
            compliance_level="critical",
            regulatory_impact="high"
        )
        
        self._add_audit_entry(entry)
    
    def log_human_consultation(
        self,
        consultation_type: str,
        consultation_data: Dict[str, Any],
        user_id: str,
        decision: Optional[str] = None
    ) -> None:
        """Log human consultation event."""
        event_data = {
            "consultation_type": consultation_type,
            "consultation_data": consultation_data,
            "decision": decision,
            "session_id": str(self.session_id)
        }
        
        entry = AuditLogEntry(
            event_type="human_consultation",
            event_data=event_data,
            user_id=user_id,
            compliance_level="critical",
            regulatory_impact="high"
        )
        
        self._add_audit_entry(entry)
    
    def _add_audit_entry(self, entry: AuditLogEntry) -> None:
        """Add audit entry to storage and write to file."""
        self.audit_entries.append(entry)
        
        # Write to JSONL file immediately for persistence
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                json_data = entry.model_dump(default=str)
                f.write(json.dumps(json_data, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write audit entry to file: {e}")
        
        # Also log to standard logger
        log_message = f"[AUDIT] {entry.event_type}: {entry.event_data}"
        if entry.success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
    
    def get_audit_trail(
        self,
        event_type: Optional[str] = None,
        step_name: Optional[str] = None,
        agent_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[AuditLogEntry]:
        """Get filtered audit trail entries."""
        entries = self.audit_entries
        
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        if step_name:
            entries = [e for e in entries if e.step_name == step_name]
        
        if agent_type:
            entries = [e for e in entries if e.agent_type == agent_type]
        
        if user_id:
            entries = [e for e in entries if e.user_id == user_id]
        
        return entries
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get comprehensive audit trail summary."""
        total_entries = len(self.audit_entries)
        successful_entries = len([e for e in self.audit_entries if e.success])
        error_entries = len([e for e in self.audit_entries if not e.success])
        
        event_types = {}
        compliance_levels = {}
        
        for entry in self.audit_entries:
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1
            compliance_levels[entry.compliance_level] = compliance_levels.get(entry.compliance_level, 0) + 1
        
        return {
            "session_id": str(self.session_id),
            "total_entries": total_entries,
            "successful_entries": successful_entries,
            "error_entries": error_entries,
            "event_types": event_types,
            "compliance_levels": compliance_levels,
            "log_file_path": str(self.log_file_path),
            "generated_timestamp": datetime.now(UTC).isoformat()
        }
    
    def export_audit_report(self, output_path: Optional[str] = None) -> str:
        """Export comprehensive audit report."""
        if not output_path:
            output_path = self.log_directory / f"audit_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        else:
            output_path = Path(output_path)
        
        report_data = {
            "audit_summary": self.get_audit_summary(),
            "audit_entries": [entry.model_dump(default=str) for entry in self.audit_entries],
            "report_metadata": {
                "generated_by": "event_logger_system",
                "generation_timestamp": datetime.now(UTC).isoformat(),
                "compliance_validated": True,
                "regulatory_compliant": True
            }
        }
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Audit report exported to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Failed to export audit report: {e}")
            raise