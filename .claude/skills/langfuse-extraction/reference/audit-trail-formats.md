# ALCOA+ Audit Trail Formats

## Standard ALCOA+ Audit Trail (JSON)

```json
{
  "report_generated": "2025-01-17T10:30:00Z",
  "user_id": "user_35KgiAcvIC0tdtFvJUN1vDkrNYc",
  "session_id": "job_12345",
  "compliance_standard": "ALCOA+",
  "entries": [
    {
      "trace_id": "abc123",
      "timestamp": "2025-01-17T09:00:00Z",
      "duration_ms": 12450,
      "status": "COMPLETED",
      "compliance_check": {
        "attributable": true,
        "legible": true,
        "contemporaneous": true,
        "original": true,
        "accurate": true,
        "complete": true,
        "consistent": true,
        "enduring": true,
        "available": true,
        "gamp5_category": 5
      },
      "operations": [
        {"name": "gamp5-categorization", "timestamp": "2025-01-17T09:00:01Z", "duration_ms": 3200},
        {"name": "requirement-extraction", "timestamp": "2025-01-17T09:00:04Z", "duration_ms": 800},
        {"name": "test-generation", "timestamp": "2025-01-17T09:00:05Z", "duration_ms": 8450}
      ]
    }
  ]
}
```

## GAMP-5 Validation Report (CSV)

```csv
trace_id,timestamp,user_id,gamp5_category,validation_status,duration_ms
abc123,2025-01-17T09:00:00Z,user_xxx,5,PASSED,12450
def456,2025-01-17T10:00:00Z,user_xxx,5,PASSED,11230
```

## Cost and Token Usage Report

```json
{
  "report_period": "2025-01-01 to 2025-01-31",
  "total_cost_usd": 45.67,
  "total_input_tokens": 1234567,
  "total_output_tokens": 345678,
  "traces": [
    {
      "session_id": "job_123",
      "cost_usd": 2.34,
      "input_tokens": 56789,
      "output_tokens": 12345
    }
  ]
}
```

## Regulatory Compliance Summary

```json
{
  "compliance_assessment": {
    "standard": "21 CFR Part 11",
    "period": "Q1 2025",
    "total_traces": 1500,
    "compliant_traces": 1498,
    "compliance_rate": 99.87,
    "findings": [
      {
        "trace_id": "xyz789",
        "issue": "Missing user attribution",
        "severity": "HIGH"
      }
    ]
  }
}
```
