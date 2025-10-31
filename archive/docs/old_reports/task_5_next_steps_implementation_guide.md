# Task 5 HITL Consultation - Next Steps Implementation Guide

**Date**: July 29, 2025  
**Purpose**: Technical roadmap for completing human-in-the-loop consultation system  
**Target Audience**: Development team, technical leads  

## 🚨 Critical Path: Human Interface Implementation

The HITL system backend is complete but lacks the essential human interaction pathway. This guide provides step-by-step implementation instructions to bridge this gap.

## Phase 1: Critical Bug Fixes (Days 1-3)

### 1.1 Fix Session ID Mismatch Bug

**Current Issue**: 
```
ERROR: Response session ID 1bbe716b-ed2a-4a35-b58b-1b7f113f9620 does not match c56f9c5e-50e8-4b20-93a7-a834a9f1e379
```

**Implementation**:

```python
# File: src/core/human_consultation.py
# Fix in HumanConsultationManager.request_consultation()

async def request_consultation(
    self,
    ctx: Context,
    consultation_event: ConsultationRequiredEvent,
    timeout_seconds: int | None = None
) -> HumanResponseEvent | ConsultationTimeoutEvent:
    # ... existing code ...
    
    # FIX: Ensure response validation uses correct session ID
    try:
        response_event = await asyncio.wait_for(
            ctx.wait_for_event(HumanResponseEvent),
            timeout=session.timeout_seconds
        )
        
        # FIXED: Validate both consultation_id AND session_id
        if (response_event.consultation_id != consultation_event.consultation_id or 
            response_event.session_id != session.session_id):
            self.logger.error(
                f"Response mismatch - Expected consultation: {consultation_event.consultation_id}, "
                f"session: {session.session_id}, got consultation: {response_event.consultation_id}, "
                f"session: {response_event.session_id}"
            )
            raise ValueError("Response ID mismatch - continuing with timeout")
            
        # ... rest of method
```

### 1.2 Fix File System Dependencies

**Current Issue**:
```
ERROR: [Errno 2] No such file or directory: 'logs/audit/gamp5_audit_20250729_001.jsonl'
```

**Implementation**:

```python
# File: src/core/human_consultation.py
# Add to HumanConsultationManager.__init__()

def __init__(self, config: Config | None = None):
    self.config = config or get_config()
    self.logger = logging.getLogger(f"{__name__}.HumanConsultationManager")

    # FIX: Ensure required directories exist
    self._ensure_directories()
    
    # Initialize compliance logger AFTER directory creation
    self.compliance_logger = GAMP5ComplianceLogger(self.config)
    # ... rest of init

def _ensure_directories(self) -> None:
    """Ensure all required directories exist for logging and audit."""
    from pathlib import Path
    
    # Create logging directory
    log_dir = Path(self.config.logging.log_directory)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create audit directory
    audit_dir = Path(self.config.gamp5_compliance.audit_log_directory)
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    self.logger.debug(f"Ensured directories: {log_dir}, {audit_dir}")
```

### 1.3 Fix Async Mock Integration

**Current Issue**:
```
RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
```

**Implementation**:

```python
# File: src/core/human_consultation.py
# Fix in request_consultation method

# BEFORE:
ctx.send_event(session_event)

# AFTER:
await self._safe_send_event(ctx, session_event)

async def _safe_send_event(self, ctx: Context, event) -> None:
    """Safely send event handling both real and mock contexts."""
    try:
        result = ctx.send_event(event)
        if hasattr(result, '__await__'):
            await result
    except Exception as e:
        self.logger.warning(f"Event send failed (may be expected in tests): {e}")
```

## Phase 2: Basic Human Interface (Days 4-10)

### 2.1 Command Line Interface

**Create**: `src/cli/consultation_cli.py`

```python
"""Command line interface for human consultation system."""

import asyncio
import click
from typing import Optional
from src.core.human_consultation import HumanConsultationManager
from src.core.events import HumanResponseEvent
from src.shared.config import get_config

@click.group()
def pharma_consult():
    """Pharmaceutical consultation management CLI."""
    pass

@pharma_consult.command()
def list():
    """List pending consultations."""
    asyncio.run(_list_consultations())

async def _list_consultations():
    config = get_config()
    manager = HumanConsultationManager(config)
    
    if not manager.active_sessions:
        click.echo("No pending consultations.")
        return
    
    click.echo("\n🔔 Pending Consultations:")
    click.echo("=" * 50)
    
    for session_id, session in manager.active_sessions.items():
        event = session.consultation_event
        elapsed = (datetime.now(UTC) - session.created_at).total_seconds()
        remaining = session.timeout_seconds - elapsed
        
        click.echo(f"ID: {session_id}")
        click.echo(f"Type: {event.consultation_type}")
        click.echo(f"Urgency: {event.urgency}")
        click.echo(f"Required Expertise: {', '.join(event.required_expertise)}")
        click.echo(f"Time Remaining: {remaining:.0f}s")
        click.echo(f"Context: {event.context}")
        click.echo("-" * 30)

@pharma_consult.command()
@click.argument('session_id')
@click.option('--approve', is_flag=True, help='Approve the consultation')
@click.option('--reject', is_flag=True, help='Reject the consultation')
@click.option('--comment', type=str, help='Add comment to response')
def respond(session_id: str, approve: bool, reject: bool, comment: Optional[str]):
    """Respond to a consultation."""
    if approve and reject:
        click.echo("Error: Cannot both approve and reject")
        return
    
    if not (approve or reject):
        click.echo("Error: Must specify --approve or --reject")
        return
    
    asyncio.run(_respond_to_consultation(session_id, approve, comment))

async def _respond_to_consultation(session_id: str, approve: bool, comment: Optional[str]):
    config = get_config()
    manager = HumanConsultationManager(config)
    
    # Find session
    session_uuid = UUID(session_id)
    if session_uuid not in manager.active_sessions:
        click.echo(f"Error: Session {session_id} not found")
        return
    
    session = manager.active_sessions[session_uuid]
    
    # Create response event
    response = HumanResponseEvent(
        consultation_id=session.consultation_event.consultation_id,
        session_id=session_uuid,
        response_type="approval" if approve else "rejection",
        user_id="cli_user",  # TODO: Get from authentication
        user_role="validation_engineer",  # TODO: Get from authentication
        response_data={
            "decision": "approved" if approve else "rejected",
            "comment": comment or "",
            "timestamp": datetime.now(UTC).isoformat()
        },
        confidence_level=0.9,
        approval_level="standard"
    )
    
    # Add response to session
    try:
        await session.add_response(response)
        click.echo(f"✅ Response recorded for consultation {session_id}")
    except Exception as e:
        click.echo(f"❌ Error recording response: {e}")

if __name__ == '__main__':
    pharma_consult()
```

**Add to main.py**:

```python
# Add CLI option to main.py argument parser

parser.add_argument(
    "--consultation-cli",
    action="store_true", 
    help="Launch consultation CLI interface"
)

# Add to main() function
if args.consultation_cli:
    from src.cli.consultation_cli import pharma_consult
    pharma_consult()
    return 0
```

### 2.2 Simple Web API

**Create**: `src/api/consultation_api.py`

```python
"""FastAPI endpoints for consultation management."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
import asyncio

from src.core.human_consultation import HumanConsultationManager
from src.core.events import HumanResponseEvent
from src.shared.config import get_config

app = FastAPI(title="Pharmaceutical Consultation API")
security = HTTPBearer()

class ConsultationResponse(BaseModel):
    session_id: str
    consultation_type: str
    urgency: str
    required_expertise: List[str]
    context: dict
    time_remaining_seconds: float
    created_at: str

class SubmitResponseRequest(BaseModel):
    response_type: str  # "approval", "rejection", "request_more_info"
    comment: str
    confidence_level: float = 0.8
    approval_level: str = "standard"

# Global consultation manager
consultation_manager = None

def get_consultation_manager() -> HumanConsultationManager:
    global consultation_manager
    if consultation_manager is None:
        consultation_manager = HumanConsultationManager(get_config())
    return consultation_manager

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify authentication token - simplified for now."""
    # TODO: Implement proper token validation
    return "cli_user"

@app.get("/consultations/pending", response_model=List[ConsultationResponse])
async def list_pending_consultations(user_id: str = Depends(verify_token)):
    """List all pending consultations."""
    manager = get_consultation_manager()
    consultations = []
    
    for session_id, session in manager.active_sessions.items():
        elapsed = (datetime.now(UTC) - session.created_at).total_seconds()
        remaining = max(0, session.timeout_seconds - elapsed)
        
        consultations.append(ConsultationResponse(
            session_id=str(session_id),
            consultation_type=session.consultation_event.consultation_type,
            urgency=session.consultation_event.urgency,
            required_expertise=session.consultation_event.required_expertise,
            context=session.consultation_event.context,
            time_remaining_seconds=remaining,
            created_at=session.created_at.isoformat()
        ))
    
    return consultations

@app.post("/consultations/{session_id}/respond")
async def respond_to_consultation(
    session_id: str,
    response: SubmitResponseRequest,
    user_id: str = Depends(verify_token)
):
    """Submit response to a consultation."""
    manager = get_consultation_manager()
    
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    
    if session_uuid not in manager.active_sessions:
        raise HTTPException(status_code=404, detail="Consultation session not found")
    
    session = manager.active_sessions[session_uuid]
    
    # Create response event
    response_event = HumanResponseEvent(
        consultation_id=session.consultation_event.consultation_id,
        session_id=session_uuid,
        response_type=response.response_type,
        user_id=user_id,
        user_role="validation_engineer",  # TODO: Get from user context
        response_data={
            "decision": response.response_type,
            "comment": response.comment,
            "timestamp": datetime.now(UTC).isoformat()
        },
        confidence_level=response.confidence_level,
        approval_level=response.approval_level
    )
    
    try:
        await session.add_response(response_event)
        return {"status": "success", "message": "Response recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording response: {e}")

@app.get("/consultations/statistics")
async def get_consultation_statistics(user_id: str = Depends(verify_token)):
    """Get consultation system statistics."""
    manager = get_consultation_manager()
    return manager.get_manager_statistics()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2.3 Integration Testing Framework

**Create**: `tests/integration/test_hitl_end_to_end.py`

```python
"""End-to-end integration tests for HITL consultation system."""

import asyncio
import pytest
from uuid import uuid4
from datetime import datetime, UTC

from src.core.human_consultation import HumanConsultationManager
from src.core.events import ConsultationRequiredEvent, HumanResponseEvent
from src.shared.config import get_config
from tests.conftest import TestContext

class TestHITLEndToEnd:
    """Test complete HITL consultation workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_consultation_workflow(self):
        """Test full consultation workflow from request to response."""
        # Setup
        config = get_config()
        manager = HumanConsultationManager(config)
        ctx = TestContext()
        
        # Create consultation request
        consultation = ConsultationRequiredEvent(
            consultation_type="categorization_failure",
            context={"error": "Unable to determine GAMP category"},
            urgency="high",
            required_expertise=["gamp_specialist"],
            triggering_step="gamp_categorization"
        )
        
        # Start consultation in background
        consultation_task = asyncio.create_task(
            manager.request_consultation(ctx, consultation, timeout_seconds=5)
        )
        
        # Wait for session to be created
        await asyncio.sleep(0.1)
        assert len(manager.active_sessions) == 1
        
        session = next(iter(manager.active_sessions.values()))
        
        # Simulate human response
        human_response = HumanResponseEvent(
            consultation_id=consultation.consultation_id,
            session_id=session.session_id,
            response_type="approval",
            user_id="test_expert",
            user_role="gamp_specialist",
            response_data={"decision": "category_5", "rationale": "Custom application"}
        )
        
        # Send response via context
        ctx.send_event(human_response)
        
        # Wait for consultation to complete
        result = await consultation_task
        
        # Verify results
        assert isinstance(result, HumanResponseEvent)
        assert result.response_type == "approval"
        assert manager.successful_consultations == 1
        assert len(manager.active_sessions) == 0
    
    @pytest.mark.asyncio
    async def test_consultation_timeout_with_defaults(self):
        """Test consultation timeout with conservative defaults."""
        config = get_config()
        manager = HumanConsultationManager(config)
        ctx = TestContext()
        
        consultation = ConsultationRequiredEvent(
            consultation_type="categorization_failure",
            context={"error": "Unable to determine GAMP category"},
            urgency="high",
            required_expertise=["gamp_specialist"],
            triggering_step="gamp_categorization"
        )
        
        # Request consultation with very short timeout
        result = await manager.request_consultation(ctx, consultation, timeout_seconds=0.1)
        
        # Verify timeout handling
        assert hasattr(result, 'timeout_duration_seconds')
        assert result.escalation_required is True
        assert "category 5" in result.conservative_action.lower()
        assert manager.timed_out_consultations == 1

class TestContext:
    """Test context that simulates LlamaIndex Context behavior."""
    
    def __init__(self):
        self.events = []
        self.waiters = []
    
    def send_event(self, event):
        """Send event to waiting consumers."""
        self.events.append(event)
        # Notify any waiters
        for waiter in self.waiters:
            if not waiter.done():
                waiter.set_result(event)
    
    async def wait_for_event(self, event_type):
        """Wait for specific event type."""
        # Check if event already exists
        for event in self.events:
            if isinstance(event, event_type):
                return event
        
        # Create future to wait for event
        future = asyncio.Future()
        self.waiters.append(future)
        return await future
```

## Phase 3: Web Interface Development (Days 11-17)

### 3.1 React Frontend Structure

**Create**: `src/web/consultation-ui/`

```bash
mkdir -p src/web/consultation-ui/src/components
mkdir -p src/web/consultation-ui/src/services
mkdir -p src/web/consultation-ui/src/types
```

**File**: `src/web/consultation-ui/src/types/consultation.ts`

```typescript
export interface ConsultationRequest {
  session_id: string;
  consultation_type: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  required_expertise: string[];
  context: Record<string, any>;
  time_remaining_seconds: number;
  created_at: string;
}

export interface ConsultationResponse {
  response_type: 'approval' | 'rejection' | 'request_more_info';
  comment: string;
  confidence_level: number;
  approval_level: string;
}

export interface ConsultationStats {
  total_consultations: number;
  successful_consultations: number;
  timed_out_consultations: number;
  active_sessions: number;
  success_rate: number;
}
```

**File**: `src/web/consultation-ui/src/services/consultationService.ts`

```typescript
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000';

export class ConsultationService {
  private token: string | null = null;

  setAuthToken(token: string) {
    this.token = token;
  }

  private getHeaders() {
    return {
      'Content-Type': 'application/json',
      ...(this.token && { 'Authorization': `Bearer ${this.token}` })
    };
  }

  async getPendingConsultations(): Promise<ConsultationRequest[]> {
    const response = await fetch(`${API_BASE}/consultations/pending`, {
      headers: this.getHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch consultations');
    }
    
    return response.json();
  }

  async submitResponse(sessionId: string, response: ConsultationResponse): Promise<void> {
    const result = await fetch(`${API_BASE}/consultations/${sessionId}/respond`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(response)
    });
    
    if (!result.ok) {
      throw new Error('Failed to submit response');
    }
  }

  async getStatistics(): Promise<ConsultationStats> {
    const response = await fetch(`${API_BASE}/consultations/statistics`, {
      headers: this.getHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch statistics');
    }
    
    return response.json();
  }
}

export const consultationService = new ConsultationService();
```

### 3.2 Main Dashboard Component

**File**: `src/web/consultation-ui/src/components/ConsultationDashboard.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import { ConsultationRequest, ConsultationStats } from '../types/consultation';
import { consultationService } from '../services/consultationService';
import ConsultationCard from './ConsultationCard';
import StatisticsPanel from './StatisticsPanel';

const ConsultationDashboard: React.FC = () => {
  const [consultations, setConsultations] = useState<ConsultationRequest[]>([]);
  const [statistics, setStatistics] = useState<ConsultationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [consultationsData, statsData] = await Promise.all([
        consultationService.getPendingConsultations(),
        consultationService.getStatistics()
      ]);
      
      setConsultations(consultationsData);
      setStatistics(statsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleResponseSubmitted = (sessionId: string) => {
    // Remove consultation from list and refresh data
    setConsultations(prev => prev.filter(c => c.session_id !== sessionId));
    loadData(); // Refresh statistics
  };

  if (loading && consultations.length === 0) {
    return <div className="loading">Loading consultations...</div>;
  }

  return (
    <div className="consultation-dashboard">
      <header className="dashboard-header">
        <h1>🏥 Pharmaceutical Consultation System</h1>
        <button onClick={loadData} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </header>

      {error && (
        <div className="error-banner">
          ❌ Error: {error}
        </div>
      )}

      <div className="dashboard-content">
        <div className="statistics-section">
          {statistics && <StatisticsPanel statistics={statistics} />}
        </div>

        <div className="consultations-section">
          <h2>Pending Consultations ({consultations.length})</h2>
          
          {consultations.length === 0 ? (
            <div className="no-consultations">
              ✅ No pending consultations
            </div>
          ) : (
            <div className="consultations-grid">
              {consultations.map(consultation => (
                <ConsultationCard
                  key={consultation.session_id}
                  consultation={consultation}
                  onResponseSubmitted={handleResponseSubmitted}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConsultationDashboard;
```

## Phase 4: Production Readiness (Days 18-21)

### 4.1 Docker Configuration

**Create**: `docker/Dockerfile.consultation-api`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY tests/ ./tests/

# Create required directories
RUN mkdir -p logs/audit

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.api.consultation_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4.2 Monitoring and Health Checks

**Add to**: `src/api/consultation_api.py`

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    manager = get_consultation_manager()
    stats = manager.get_manager_statistics()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "active_sessions": stats["active_sessions"],
        "total_consultations": stats["total_consultations"],
        "success_rate": stats["success_rate"]
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    manager = get_consultation_manager()
    stats = manager.get_manager_statistics()
    
    metrics = [
        f"consultation_total_count {stats['total_consultations']}",
        f"consultation_success_count {stats['successful_consultations']}",
        f"consultation_timeout_count {stats['timed_out_consultations']}",
        f"consultation_active_sessions {stats['active_sessions']}",
        f"consultation_success_rate {stats['success_rate']}"
    ]
    
    return Response(
        content="\n".join(metrics),
        media_type="text/plain"
    )
```

## 📋 Implementation Checklist

### Phase 1: Critical Fixes ✅
- [ ] Fix session ID mismatch bug in `request_consultation()`
- [ ] Add directory creation in `HumanConsultationManager.__init__()`
- [ ] Fix async event sending with `_safe_send_event()`
- [ ] Update test fixtures for proper async mocking
- [ ] Verify all 23 tests pass

### Phase 2: Basic Interface ✅
- [ ] Implement CLI with `list`, `respond`, `status` commands
- [ ] Create FastAPI endpoints for consultation management
- [ ] Add authentication middleware (simplified)
- [ ] Create integration test suite
- [ ] Add API documentation with OpenAPI/Swagger

### Phase 3: Web Interface ✅
- [ ] Set up React TypeScript project
- [ ] Implement consultation dashboard component
- [ ] Add real-time updates with WebSocket/polling
- [ ] Create consultation response forms
- [ ] Add user authentication UI

### Phase 4: Production ✅
- [ ] Containerize with Docker
- [ ] Add health check and metrics endpoints
- [ ] Implement proper logging and monitoring
- [ ] Security hardening and testing
- [ ] Documentation and deployment guides

## 🎯 Success Criteria

### Technical Validation
- [ ] All tests pass (>95% coverage)
- [ ] API response time <100ms
- [ ] Frontend loads in <2 seconds
- [ ] Zero critical security vulnerabilities

### Functional Validation
- [ ] Human can discover pending consultations
- [ ] Human can submit responses within 60 seconds
- [ ] System properly handles timeouts with conservative defaults
- [ ] Audit trail captures all interactions

### Compliance Validation
- [ ] Digital signatures properly recorded
- [ ] All interactions have full audit trails
- [ ] Conservative defaults meet pharmaceutical standards
- [ ] Escalation procedures function correctly

---

**Next Review**: August 1, 2025  
**Estimated Completion**: August 12, 2025  
**Team Assignment**: 2 developers, 1 QA engineer, 1 regulatory specialist