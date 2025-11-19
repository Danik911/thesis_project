# Phoenix Observability Issues - Resolution Guide

**Date**: November 2025
**Status**: ✅ RESOLVED
**Impact**: Critical - Affected workflow execution, regulatory compliance (ALCOA+), and Windows deployment

---

## Executive Summary

This document consolidates all Phoenix observability issues encountered during development, their root causes, implemented solutions, and best practices to prevent recurrence. Phoenix is the observability system for LLM trace monitoring in the pharmaceutical test generation workflow.

**Key Takeaway**: Phoenix should be treated as an **OPTIONAL** observability enhancement, not required infrastructure. The workflow must function correctly with or without Phoenix.

---

## Issues Encountered

### Issue #1: ALCOA+ Audit Trail Failure
**Severity**: 🔴 CRITICAL - Regulatory Compliance
**Symptom**: `name 'execution_start' is not defined`

**Impact**:
- Broke 21 CFR Part 11 compliance (audit trail incomplete)
- ALCOA+ principle "Attributable" violated
- Workflow continued but audit records incomplete

**Root Cause**:
- Variable name mismatch in `unified_workflow.py` line 2102
- Code referenced `execution_start` but workflow tracked `workflow_start_time`
- Copy-paste error during refactoring

**Solution**:
```python
# File: main/src/core/unified_workflow.py
# Lines: 2102-2103

# BEFORE
"execution_start": execution_start.isoformat() if execution_start else None,

# AFTER
"execution_start": workflow_start_time.isoformat() if workflow_start_time else None,
```

**Prevention**:
- Use consistent variable naming across workflow
- Add type hints for workflow state variables
- Include execution timestamp in workflow initialization tests

---

### Issue #2: Phoenix Dashboard Closes After Workflow
**Severity**: 🟡 MEDIUM - Observability Loss
**Symptom**: Phoenix UI becomes inaccessible after workflow completion

**Impact**:
- Observability data lost for post-workflow analysis
- Regulatory review requires trace access
- Debugging difficult without historical traces

**Root Cause**:
- `shutdown()` method called `session.close()` which terminated Phoenix UI
- Intended to close tracer, but closed entire Phoenix application
- Windows file locks persisted, preventing database cleanup

**Solution**:
```python
# File: main/src/monitoring/phoenix_config.py
# Lines: 607-615

# BEFORE
if hasattr(self.phoenix_session, 'close'):
    self.phoenix_session.close()

# AFTER
# DO NOT close Phoenix session - keep UI accessible
logger.info("[PHOENIX] Session maintained - UI remains accessible")
logger.info(f"[PHOENIX] Dashboard accessible at: {getattr(self.phoenix_session, 'url', 'http://localhost:6006')}")
```

**Additional Fix - Windows Database Lock Delay**:
```python
# Lines: 600-602
# Increased from 0.5s to 2.0s for Windows file system lock release
time.sleep(2.0)
logger.debug("[WINDOWS] Database lock release delay completed (2.0s)")
```

**Prevention**:
- Separate concerns: tracer shutdown ≠ Phoenix UI shutdown
- Keep Phoenix UI running for observability data access
- Document Phoenix lifecycle management clearly

---

### Issue #3: Duplicate Phoenix Launch (Temp Directory Database)
**Severity**: 🔴 CRITICAL - Windows PermissionError
**Symptom**: `PermissionError: [WinError 32] phoenix.db` in temp directory

**Impact**:
- Multiple Phoenix instances launched
- Database locked in temp directory
- Shutdown failed with PermissionError
- Confusing for users (which Phoenix to access?)

**Root Cause**:
Phoenix health check failed to detect existing Docker Phoenix instance because:
1. **Phoenix has NO health check endpoint** (GitHub Issue #2120 - closed, not implemented)
2. Health check tested non-existent endpoints (`/healthz`, `/health`, `/api/health`)
3. All health checks failed → `px.launch_app()` called → duplicate Phoenix in temp directory

**Research Finding**:
GitHub Issue #2120 requested health check endpoint, but Phoenix maintainers **declined to implement it**. Available endpoints:
- ✅ `/v1/projects` (REST API endpoint)
- ✅ `/` (UI root)
- ❌ `/healthz`, `/health`, `/api/health` (DO NOT EXIST)

**Solution**:
```python
# File: main/src/monitoring/phoenix_config.py
# Method: _check_existing_phoenix()

# Test real endpoints that exist
health_endpoints = ["/", "/v1/projects"]  # NOT /healthz, /health

# Improved retry logic
max_retries = 3
retry_delay = 1.0
timeout = 5  # Increased from 2s

# Accept 2xx and 3xx status codes
if 200 <= response.status_code < 400:
    # Phoenix found - use it
```

**Environment Variable Control** (User Override):
```bash
# Skip health check, assume external Phoenix
export PHOENIX_SKIP_LOCAL_LAUNCH=true

# Force local Phoenix launch (ignore health check)
export PHOENIX_FORCE_LOCAL_LAUNCH=true
```

**Permanent Working Directory** (Avoid Temp):
```python
# Set permanent directory before launch
os.environ["PHOENIX_WORKING_DIR"] = str(Path.home() / ".phoenix")
self.phoenix_session = px.launch_app()
```

**Prevention**:
- Test ONLY endpoints that actually exist in Phoenix
- Provide environment variables for explicit user control
- Use permanent working directory, not temp
- Document Phoenix has no standard health check

---

### Issue #4: Continuous ConnectionRefusedError (Critical)
**Severity**: 🔴 CRITICAL - Workflow Performance Degradation
**Symptom**: `ConnectionError: Max retries exceeded with url: /v1/traces` every 15 seconds

**Impact**:
- Log spam (100KB+ truncated output)
- Performance degradation (continuous retry attempts)
- Workflow completed but with degraded quality
- No observability data captured
- Confusing error messages for users

**Root Cause**:
With `PHOENIX_SKIP_LOCAL_LAUNCH=true`:
1. ✅ Health check skipped (as intended)
2. ✅ MockSession created pointing to localhost:6006
3. ❌ **BUT** Docker Phoenix NOT running
4. ❌ Tracer setup **ALWAYS** occurred, creating OTLP exporter
5. ❌ BatchSpanProcessor tried to export spans every 15s → ConnectionRefusedError

**Architectural Problem**: Phoenix treated as REQUIRED infrastructure when it should be OPTIONAL.

**Solution - Graceful Degradation**:

**1. Connection Validation Before Tracer Setup**:
```python
# File: main/src/monitoring/phoenix_config.py
# Method: _validate_phoenix_connection()

def _validate_phoenix_connection(self) -> bool:
    """Validate Phoenix is accessible before creating tracer."""
    try:
        # Test actual OTLP endpoint tracer will use
        otlp_url = f"http://{self.config.phoenix_host}:{self.config.phoenix_port}/v1/traces"
        response = requests.post(otlp_url, json=[], timeout=2)

        # Accept any non-server-error status
        return response.status_code < 500
    except Exception as e:
        logger.debug(f"[PHOENIX] Connection validation failed: {e}")
        return False
```

**2. Conditional Tracer Setup**:
```python
# Method: _setup_tracer()

def _setup_tracer(self) -> None:
    """Set up tracer only if Phoenix accessible."""

    # Validate BEFORE creating OTLP exporter
    if not self._validate_phoenix_connection():
        logger.warning("⚠️  [PHOENIX] Phoenix not accessible - disabling observability")
        logger.info("[PHOENIX] Workflow will continue without observability")
        self.tracer_provider = None  # Disable tracer
        return

    # Phoenix accessible - proceed normally
    logger.info("✅ [PHOENIX] Connection validated - observability enabled")
    self._setup_manual_tracer()
```

**3. Null-Safe Tracer Access**:
```python
# Method: get_tracer()

def get_tracer(self, name: str) -> trace.Tracer:
    """Get tracer, handling None gracefully."""
    if not self.tracer_provider:
        logger.debug(f"[PHOENIX] Tracer request for '{name}' - observability disabled")
        return trace.NoOpTracer()  # Return no-op tracer

    return self.tracer_provider.get_tracer(name)
```

**Result**:
- ✅ No ConnectionRefusedError when Phoenix unavailable
- ✅ Workflow continues cleanly without errors
- ✅ Clear messaging about Phoenix status
- ✅ ALCOA+ audit trail works independently (local files, not Phoenix)

**Prevention**:
- Treat observability tools as OPTIONAL enhancements
- Validate connections BEFORE creating exporters
- Provide graceful degradation for all external services
- Keep core business logic independent of monitoring tools

---

## Best Practices - Phoenix Observability

### 1. Phoenix Lifecycle Management

**Docker Phoenix (Recommended for Production)**:
```bash
# Start Phoenix container
docker run -d -p 6006:6006 --name phoenix arizephoenix/phoenix

# Verify running
docker ps | grep phoenix

# Access UI
open http://localhost:6006/

# Stop (preserves data)
docker stop phoenix

# Restart
docker start phoenix

# Remove completely
docker rm phoenix
```

**Local Phoenix (Development Only)**:
```python
# Let application launch Phoenix automatically
# No PHOENIX_SKIP_LOCAL_LAUNCH variable needed
python main.py document.md
```

### 2. Environment Variables

| Variable | Purpose | When to Use |
|----------|---------|-------------|
| `PHOENIX_SKIP_LOCAL_LAUNCH=true` | Assume external Phoenix exists | Docker/production deployments |
| `PHOENIX_FORCE_LOCAL_LAUNCH=true` | Always launch local Phoenix | Development without Docker |
| `PHOENIX_WORKING_DIR=/path` | Set permanent database location | Avoid temp directory issues |
| `PHOENIX_HOST=hostname` | Phoenix hostname | Non-localhost deployments |
| `PHOENIX_PORT=6006` | Phoenix port | Custom port configurations |

### 3. Troubleshooting Checklist

**Issue**: Phoenix not accessible / ConnectionRefusedError

```bash
# 1. Check if Phoenix running
docker ps | grep phoenix
# OR
curl http://localhost:6006/

# 2. Check environment variables
echo $PHOENIX_SKIP_LOCAL_LAUNCH
echo $PHOENIX_FORCE_LOCAL_LAUNCH

# 3. Check logs
docker logs phoenix  # If using Docker
# OR check application logs for Phoenix status

# 4. Restart Phoenix
docker restart phoenix
# OR remove environment variables and rerun workflow
```

**Issue**: Duplicate Phoenix instances

```bash
# 1. Stop all Phoenix containers
docker stop $(docker ps -q --filter ancestor=arizephoenix/phoenix)

# 2. Remove stopped containers
docker rm phoenix

# 3. Clean environment
unset PHOENIX_SKIP_LOCAL_LAUNCH
unset PHOENIX_FORCE_LOCAL_LAUNCH

# 4. Restart fresh
docker run -d -p 6006:6006 --name phoenix arizephoenix/phoenix
```

**Issue**: Windows PermissionError on phoenix.db

```bash
# 1. Close all Phoenix instances
docker stop phoenix
# Kill any local Phoenix processes

# 2. Wait for file locks to release (2-5 seconds)
timeout /t 5

# 3. Delete temp directories if needed
# Check: C:\Users\<user>\AppData\Local\Temp\tmp*\phoenix.db

# 4. Set permanent working directory
export PHOENIX_WORKING_DIR=~/.phoenix

# 5. Restart Phoenix
docker start phoenix
```

### 4. Development Workflow

**Recommended Setup**:
```bash
# 1. Start Docker Phoenix once
docker run -d -p 6006:6006 --name phoenix arizephoenix/phoenix

# 2. Don't set any environment variables
# (Let application auto-detect Phoenix)

# 3. Run workflow
python main.py document.md

# 4. Access traces in browser
open http://localhost:6006/

# 5. Keep Phoenix running between workflow executions
# (No need to restart)
```

### 5. Testing Scenarios

**Test Case 1: Phoenix Available (Normal Operation)**
```bash
docker run -d -p 6006:6006 --name phoenix arizephoenix/phoenix
python main.py document.md
# Expected: Observability enabled, traces visible in UI
```

**Test Case 2: Phoenix Unavailable (Graceful Degradation)**
```bash
docker stop phoenix
python main.py document.md
# Expected: Warning logged, workflow continues without errors
```

**Test Case 3: External Phoenix (Production)**
```bash
export PHOENIX_SKIP_LOCAL_LAUNCH=true
# Assumes Phoenix running at localhost:6006
python main.py document.md
# Expected: Connects to external Phoenix, no duplicate launch
```

### 6. Code Review Checklist

When modifying Phoenix-related code:

- [ ] Phoenix connection validated BEFORE tracer setup
- [ ] Graceful degradation implemented for connection failures
- [ ] Clear logging of Phoenix status (enabled/disabled)
- [ ] No hardcoded endpoints (use configuration)
- [ ] Tracer provider nullable throughout codebase
- [ ] Span creation handles None tracer gracefully
- [ ] Windows-specific handling for file locks
- [ ] Environment variable overrides documented
- [ ] Tests cover both Phoenix available and unavailable scenarios
- [ ] ALCOA+ audit trail independent of Phoenix

---

## Compliance Impact

### GAMP-5 Compliance
- ✅ **CRITICAL**: ALCOA+ audit trail restored (workflow_id traceability)
- ✅ **ENHANCED**: Observability data preserved for regulatory review
- ✅ **IMPROVED**: System reliability in GxP environments

### 21 CFR Part 11
- ✅ Complete audit trail preservation (local files, NOT dependent on Phoenix)
- ✅ Electronic signatures maintained independently
- ✅ Data integrity (ALCOA+ principles) enforced

### ALCOA+ Principles
| Principle | Phoenix Impact | Mitigation |
|-----------|----------------|------------|
| **Attributable** | Traces show operator actions | Audit trail in local files |
| **Legible** | Traces visualize workflow | JSON logs always readable |
| **Contemporaneous** | Timestamps in traces | Timestamps in audit records |
| **Original** | Trace data immutable | WORM storage for audit trail |
| **Accurate** | Trace validation | Test suite validation |

**Key Point**: ALCOA+ compliance does NOT depend on Phoenix. Audit trail is maintained in local files (`main/logs/audit/`) regardless of Phoenix availability.

---

## NO FALLBACKS Principle Compliance

### Why Phoenix Graceful Degradation IS NOT a Fallback

**Fallback** (NOT ALLOWED):
- Masking business logic failures with fake data
- Providing artificial confidence scores
- Hiding errors from users
- Deceptive system behavior

**Graceful Degradation** (ALLOWED):
- Phoenix is OPTIONAL observability enhancement
- Failure is EXPLICIT (warning logged, status clear)
- User is INFORMED (clear messages)
- NO MASKING (no fake traces, no hidden errors)

**Core Business Logic Still Strict**:
- ❌ Categorization agent has NO fallbacks (must return valid category or fail)
- ❌ Test generation has NO fallbacks (must meet quality thresholds or fail)
- ❌ ALCOA+ audit trail has NO fallbacks (complete data required)
- ✅ Phoenix observability has graceful degradation (supplementary, not core)

---

## Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `main/src/core/unified_workflow.py` | 5 | Fix execution_start variable |
| `main/src/monitoring/phoenix_config.py` | 180 | All Phoenix lifecycle fixes |
| `main/src/agents/oq_generator/models.py` | 1 | Fix Pydantic schema warning |

**Total**: 3 files, ~186 lines modified

---

## Testing Validation

All fixes have been validated with comprehensive testing:

✅ **ALCOA+ Audit Trail**: No AttributeErrors, complete audit records
✅ **Phoenix Shutdown**: UI remains accessible after workflow
✅ **Windows Database Locks**: No PermissionError on repeated launches
✅ **Health Check**: Connects to Docker Phoenix, avoids duplicate launch
✅ **Graceful Degradation**: No errors when Phoenix unavailable
✅ **Workflow Completion**: All tests pass with/without Phoenix

---

## Documentation References

- **Phoenix Official Docs**: https://docs.arize.com/phoenix
- **Phoenix GitHub**: https://github.com/Arize-ai/phoenix
- **Docker Phoenix**: https://hub.docker.com/r/arizephoenix/phoenix
- **OpenTelemetry**: https://opentelemetry.io/docs/
- **GAMP-5 Guidelines**: https://ispe.org/publications/guidance-documents/gamp-5
- **21 CFR Part 11**: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/part-11-electronic-records-electronic-signatures-scope-and-application

---

## Conclusion

Phoenix observability issues have been comprehensively resolved with:
1. **ALCOA+ compliance restored** (regulatory requirement)
2. **Phoenix UI persistence** (observability requirement)
3. **Graceful degradation** (reliability requirement)
4. **Windows compatibility** (deployment requirement)

**Key Takeaway**: Phoenix is now correctly implemented as an OPTIONAL observability enhancement that provides value when available but doesn't break the workflow when unavailable.

**For Future Development**:
- Keep Phoenix independent of core business logic
- Validate external service connections before use
- Provide clear status messaging
- Test with and without external services
- Document environment variable overrides

---

**Last Updated**: November 2025
**Author**: Pharmaceutical Test Generation System Team
**Review Status**: ✅ Validated with end-to-end testing
