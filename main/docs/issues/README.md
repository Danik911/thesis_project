# Issues Documentation Index

**Last Updated**: August 6, 2025  
**Total Issues Documented**: 6

This directory contains detailed documentation of issues encountered during the development and deployment of the pharmaceutical test generation system. Each issue includes root cause analysis, solutions, and prevention strategies.

## 📋 Issues by Status

### ✅ RESOLVED (2)
- [ISSUE_003: Model Name Confusion (o1 vs o3)](ISSUE_003_model_confusion_o1_vs_o3.md)
- [ISSUE_005: Consultation Event Sensitivity](ISSUE_005_consultation_event_sensitivity.md)

### 📝 DOCUMENTED (3)
- [ISSUE_001: Monitoring Report Accuracy](ISSUE_001_monitoring_report_accuracy.md)
- [ISSUE_002: API Key Error Confusion](ISSUE_002_api_key_error_confusion.md)
- [ISSUE_004: Progressive Generation Logic](ISSUE_004_progressive_generation_logic.md)

### ⚠️ ONGOING (1)
- [ISSUE_006: Windows-Specific Issues](ISSUE_006_windows_specific_issues.md)

## 🎯 Issues by Severity

### 🔴 CRITICAL (1)
- [ISSUE_003: Model Name Confusion](ISSUE_003_model_confusion_o1_vs_o3.md) - **RESOLVED**
  - Caused complete OQ generation failures
  - Fixed by standardizing to o3-mini for all categories

### 🟠 HIGH (2)
- [ISSUE_002: API Key Error Confusion](ISSUE_002_api_key_error_confusion.md)
  - Most frustrating user issue
  - Misleading "pdfplumber" error when API key missing
  
- [ISSUE_005: Consultation Event Sensitivity](ISSUE_005_consultation_event_sensitivity.md) - **RESOLVED**
  - Blocked workflow automation
  - Fixed by adjusting validation thresholds

### 🟡 MEDIUM (3)
- [ISSUE_001: Monitoring Report Accuracy](ISSUE_001_monitoring_report_accuracy.md)
  - Timing discrepancies in reports
  - Metrics incorrectly calculated
  
- [ISSUE_004: Progressive Generation Logic](ISSUE_004_progressive_generation_logic.md)
  - Working but needs documentation
  - Triggers at >10 tests for o3 models
  
- [ISSUE_006: Windows-Specific Issues](ISSUE_006_windows_specific_issues.md)
  - Unicode encoding errors
  - Environment variable handling
  - Path separator confusion

## 🔍 Issues by Component

### OQ Test Generator
- [ISSUE_003: Model Configuration](ISSUE_003_model_confusion_o1_vs_o3.md)
- [ISSUE_004: Progressive Generation](ISSUE_004_progressive_generation_logic.md)
- [ISSUE_005: Quality Validation](ISSUE_005_consultation_event_sensitivity.md)

### Monitoring & Observability
- [ISSUE_001: Report Accuracy](ISSUE_001_monitoring_report_accuracy.md)

### System & Environment
- [ISSUE_002: API Key Errors](ISSUE_002_api_key_error_confusion.md)
- [ISSUE_006: Windows Issues](ISSUE_006_windows_specific_issues.md)

## 💡 Key Lessons Learned

### 1. **Error Messages Must Be Clear**
The API key issue (#002) shows how misleading errors waste enormous amounts of time. Always validate prerequisites and show clear, actionable error messages.

### 2. **Model Configuration Consistency**
The o1/o3 confusion (#003) demonstrates the importance of consistent naming and validation. Use one model for similar operations.

### 3. **Validation Balance**
The consultation sensitivity issue (#005) shows that overly strict validation hinders automation. Start lenient and tighten gradually.

### 4. **Cross-Platform Testing**
Windows issues (#006) highlight the need for regular testing on all target platforms, not just development environment.

### 5. **Monitoring Accuracy**
Report discrepancies (#001) show that monitoring systems need validation against ground truth.

## 🛠️ Quick Fixes Reference

### Missing API Key?
```bash
# Check Issue #002
for /f "tokens=1,2 delims==" %a in ('findstr "OPENAI_API_KEY" "..\\.env"') do set OPENAI_API_KEY=%b
```

### o3 Model Not Working?
```python
# Check Issue #003 - Must use o3-mini with reasoning_effort
reasoning_effort = "high"  # for Category 5
```

### Workflow Blocked by Consultation?
```python
# Check Issue #005 - Validation thresholds adjusted
# Requirements coverage and compliance flags now properly initialized
```

### Unicode Errors in Windows?
```python
# Check Issue #006
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

## 📊 Issue Statistics

- **Total Issues**: 6
- **Resolved**: 2 (33%)
- **Documented**: 3 (50%)
- **Ongoing**: 1 (17%)
- **Average Resolution Time**: ~1 day for critical issues

## 🔄 Issue Workflow

1. **Discovery**: Issue encountered during development/testing
2. **Documentation**: Create detailed issue file with template
3. **Root Cause Analysis**: Investigate and document cause
4. **Solution Development**: Implement and test fix
5. **Verification**: Confirm fix works in production
6. **Prevention**: Add checks to prevent recurrence

## 📝 Issue Template

When documenting new issues, use this template:

```markdown
# Issue #XXX: [Title]

**Status**: [Documented/Resolved/Ongoing]
**Severity**: [Critical/High/Medium/Low]
**First Observed**: [Date]
**Components Affected**: [List components]

## Problem Description
[Clear description of the issue]

## Root Cause Analysis
[Investigation findings]

## Evidence
[Code snippets, error messages, logs]

## Impact
[How this affects users/system]

## Solution/Workaround
[How to fix or work around]

## Prevention
[How to prevent recurrence]

## Related Issues
[Links to related issues]

## References
[External documentation, code locations]

## Notes
[Additional observations]
```

## 🚀 Next Steps

1. **Implement permanent fixes** for documented issues
2. **Add automated tests** to prevent regression
3. **Update error handling** to provide clearer messages
4. **Create validation scripts** for common issues
5. **Monitor for new issues** during production use

---

For questions or to report new issues, please create a new issue file following the template above.