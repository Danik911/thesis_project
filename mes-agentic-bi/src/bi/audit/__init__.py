"""ALCOA+ Audit Trail package for MES Agentic BI."""

from src.bi.audit.models import ALCOAPlusFields, AuditEvent, AuditEventType

__all__ = [
    "ALCOAPlusFields",
    "AuditEvent",
    "AuditEventType",
    "get_audit_logger",
]


def get_audit_logger():
    """Return the singleton AuditLogger instance.

    Raises RuntimeError if the logger has not been initialized
    via AuditLogger.initialize() at app startup.
    """
    from src.bi.audit.logger import AuditLogger

    return AuditLogger.get_instance()
