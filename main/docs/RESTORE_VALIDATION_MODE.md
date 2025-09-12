# Restore VALIDATION_MODE After Demo

## Current Status
- **VALIDATION_MODE**: Currently set to `false` in .env file
- **Purpose**: Enabled human consultation for viva demonstration
- **Date Modified**: 2025-08-28

## To Restore for Automated Testing

If you need to run automated tests without human consultation prompts:

```bash
# Option 1: Edit .env file
notepad C:\Users\anteb\Desktop\Courses\Projects\thesis_project\.env
# Change line 75: VALIDATION_MODE=true

# Option 2: Set environment variable temporarily
set VALIDATION_MODE=true
python main.py [your_test_file]

# Option 3: Use in Python script
import os
os.environ['VALIDATION_MODE'] = 'true'
```

## Current Settings for Demo
- `VALIDATION_MODE=false` - Allows human consultation to trigger
- Confidence threshold: 0.40-0.60 (depending on configuration)
- Timeout: 30-60 seconds for human response
- Conservative default: Category 5 on timeout

## When to Keep false (Human Consultation Enabled)
- Viva demonstrations
- Testing human-in-the-loop features
- Validating consultation triggers
- Compliance demonstrations

## When to Set true (Bypass Consultation)
- Automated CI/CD pipelines
- Batch testing
- Performance benchmarking
- Regression testing

## Verification
```bash
# Check current setting
type ..\\.env | findstr VALIDATION_MODE

# Check if consultation is bypassed in logs
type main\logs\validation\bypassed_consultations\*.json
```

**Note**: Remember to set back to `true` after viva demonstration if running automated tests.