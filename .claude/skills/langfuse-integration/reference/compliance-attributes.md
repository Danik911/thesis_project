# Compliance Attributes Reference

**Purpose**: Standard GAMP-5, ALCOA+, and 21 CFR Part 11 attribute schemas for pharmaceutical traceability.

---

## GAMP-5 Software Categorization Attributes

```python
gamp5_attributes = {
    "compliance.gamp5.applicable": True,
    "compliance.gamp5.category": 5,  # 1-5
    "compliance.gamp5.confidence": 0.95,  # 0.0-1.0
    "compliance.gamp5.rationale": "Custom developed software with high compliance impact",
    "compliance.standard": "GAMP-5",
    "compliance.version": "2nd Edition (2022)"
}
```

**Category Definitions**:
- **Category 1**: Infrastructure (OS, databases) - Low validation burden
- **Category 2**: Non-configured products (Excel, Word) - Low validation burden
- **Category 3**: Configured products (LIMS, ERP) - Medium validation burden
- **Category 4**: Configured bespoke (customized COTS) - Medium-high validation burden
- **Category 5**: Custom developed (bespoke) - **Highest validation burden** (this project)

---

## ALCOA+ Principles

```python
alcoa_plus_attributes = {
    "compliance.alcoa_plus.attributable": True,  # Who performed action
    "compliance.alcoa_plus.legible": True,  # Human readable
    "compliance.alcoa_plus.contemporaneous": True,  # Real-time recording
    "compliance.alcoa_plus.original": True,  # First recording
    "compliance.alcoa_plus.accurate": True,  # Correct and truthful
    "compliance.alcoa_plus.complete": True,  # All data present
    "compliance.alcoa_plus.consistent": True,  # Chronological, logical
    "compliance.alcoa_plus.enduring": True,  # Preserved for retention period
    "compliance.alcoa_plus.available": True,  # Accessible for review/audit

    # User attribution (Attributable)
    "user.id": "user_35KgiAcvIC0tdtFvJUN1vDkrNYc",
    "user.clerk_id": "user_35KgiAcvIC0tdtFvJUN1vDkrNYc",
    "user.email": "engineer@pharma.com",

    # Session traceability (Contemporaneous, Complete)
    "session.id": "job_12345",
    "session.timestamp": "2025-01-17T10:30:00Z",

    # Audit trail (Enduring, Available)
    "audit.trail.required": True,
    "audit.retention_years": 7
}
```

---

## 21 CFR Part 11 (Electronic Records)

```python
cfr_part11_attributes = {
    "compliance.21cfr_part11.applicable": True,
    "compliance.21cfr_part11.section_11_10": True,  # Controls for closed systems
    "compliance.21cfr_part11.section_11_50": False,  # Signature manifestations (if e-signatures used)
    "compliance.21cfr_part11.section_11_70": False,  # Signature/record linking (if e-signatures used)

    # Validation
    "compliance.validation.required": True,
    "compliance.validation.status": "IQ/OQ Complete",  # IQ/OQ/PQ stages

    # Audit trail
    "audit.secure": True,  # Computer-generated, time-stamped
    "audit.independent_copy": True,  # Separate from operational records
    "audit.human_readable": True
}
```

---

## Data Residency and Privacy

```python
data_residency_attributes = {
    "compliance.data_residency": "EU",  # eu-west-2 (London)
    "compliance.region": "eu-west-2",
    "compliance.gdpr_compliant": True,
    "compliance.data_processor": "Langfuse Cloud",
    "compliance.dpa_signed": True  # Data Processing Agreement
}
```

---

## Complete Trace-Level Attribute Template

```python
from langfuse import get_current_trace
from datetime import datetime, timezone

def set_pharmaceutical_compliance_attributes(
    user_id: str,
    session_id: str,
    gamp5_category: int
):
    """Set complete compliance attributes at trace root."""
    trace = get_current_trace()
    if not trace:
        return

    trace.update(
        user_id=user_id,
        session_id=session_id,
        tags=["pharmaceutical", "gamp5", f"category-{gamp5_category}", "alcoa-plus"],
        metadata={
            # GAMP-5
            "compliance.gamp5.applicable": True,
            "compliance.gamp5.category": gamp5_category,
            "compliance.standard": "GAMP-5",

            # ALCOA+
            "compliance.alcoa_plus.attributable": True,
            "compliance.alcoa_plus.contemporaneous": True,
            "compliance.alcoa_plus.original": True,
            "compliance.alcoa_plus.accurate": True,
            "compliance.alcoa_plus.complete": True,

            # User attribution
            "user.clerk_id": user_id,
            "session.id": session_id,
            "session.timestamp": datetime.now(timezone.utc).isoformat(),

            # CFR Part 11
            "compliance.21cfr_part11.applicable": True,
            "audit.trail.required": True,
            "audit.retention_years": 7,

            # Data residency
            "compliance.data_residency": "EU",
            "compliance.gdpr_compliant": True,
            "compliance.region": "eu-west-2"
        }
    )
```

---

## Span-Level GAMP-5 Category Assignment

```python
from langfuse import observe, get_current_observation

@observe(name="gamp5-categorization")
async def categorize_software(urs_content: str) -> dict:
    """Assign GAMP-5 category with confidence."""
    category = await classify(urs_content)
    confidence = calculate_confidence(category)

    obs = get_current_observation()
    if obs:
        obs.update(metadata={
            "compliance.gamp5.category": category,
            "compliance.gamp5.confidence": confidence,
            "compliance.gamp5.timestamp": datetime.now(timezone.utc).isoformat(),
            "compliance.gamp5.method": "llm-classification",
            "compliance.gamp5.model": "deepseek-v3"
        })

    return {"category": category, "confidence": confidence}
```

---

**Reference Version**: 1.0.0
**Last Updated**: 2025-01-17
**Standards**: GAMP-5 (2022), ALCOA+, 21 CFR Part 11
