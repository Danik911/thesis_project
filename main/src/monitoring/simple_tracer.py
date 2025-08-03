"""
Simple file-based tracing for pharmaceutical workflow monitoring.
Provides immediate visibility without complex infrastructure.
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class SimpleTracer:
    """Direct file-based tracing for debugging and monitoring."""
    
    def __init__(self, trace_dir: str = "logs/traces"):
        self.trace_dir = Path(trace_dir)
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.trace_dir / f"trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        self.current_trace = {}
        
    def start_workflow(self, workflow_name: str, document: str):
        """Start workflow trace."""
        self.current_trace = {
            "workflow": workflow_name,
            "document": document,
            "start_time": time.time(),
            "steps": []
        }
        self._write_event("workflow_start", {"workflow": workflow_name, "document": document})
        
    def log_step(self, step_name: str, data: Dict[str, Any]):
        """Log a workflow step."""
        step_data = {
            "step": step_name,
            "timestamp": time.time(),
            "data": data
        }
        self.current_trace.setdefault("steps", []).append(step_data)
        self._write_event("step", step_data)
        
    def log_api_call(self, service: str, endpoint: str, duration: float, success: bool, details: Optional[Dict] = None):
        """Log API call details."""
        api_data = {
            "service": service,
            "endpoint": endpoint,
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
            "details": details or {}
        }
        self._write_event("api_call", api_data)
        print(f"🌐 API Call: {service} - {endpoint} - {duration:.2f}s - {'✅' if success else '❌'}")
        
    def log_agent_execution(self, agent_type: str, start_time: float, result: Any, error: Optional[str] = None):
        """Log agent execution details."""
        duration = time.time() - start_time
        agent_data = {
            "agent": agent_type,
            "duration": duration,
            "success": error is None,
            "error": error,
            "result_summary": str(result)[:200] if result else None,
            "timestamp": time.time()
        }
        self._write_event("agent", agent_data)
        status = "✅" if error is None else "❌"
        print(f"🤖 Agent: {agent_type} - {duration:.2f}s - {status}")
        
    def log_error(self, component: str, error: Exception):
        """Log error with full stack trace."""
        error_data = {
            "component": component,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": traceback.format_exc(),
            "timestamp": time.time()
        }
        self._write_event("error", error_data)
        print(f"❌ Error in {component}: {error}")
        
    def end_workflow(self, success: bool, results: Optional[Dict] = None):
        """End workflow trace."""
        self.current_trace["end_time"] = time.time()
        self.current_trace["duration"] = self.current_trace["end_time"] - self.current_trace.get("start_time", 0)
        self.current_trace["success"] = success
        self.current_trace["results"] = results
        self._write_event("workflow_end", {
            "success": success,
            "duration": self.current_trace["duration"],
            "step_count": len(self.current_trace.get("steps", []))
        })
        
    def _write_event(self, event_type: str, data: Dict[str, Any]):
        """Write event to JSONL file."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        with open(self.session_file, "a") as f:
            f.write(json.dumps(event) + "\n")
            
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of current trace."""
        if not self.session_file.exists():
            return {"error": "No trace file found"}
            
        events = []
        with open(self.session_file, "r") as f:
            for line in f:
                events.append(json.loads(line))
                
        api_calls = [e for e in events if e["event_type"] == "api_call"]
        agents = [e for e in events if e["event_type"] == "agent"]
        errors = [e for e in events if e["event_type"] == "error"]
        
        return {
            "total_events": len(events),
            "api_calls": {
                "count": len(api_calls),
                "successful": sum(1 for e in api_calls if e["data"]["success"]),
                "total_duration": sum(e["data"]["duration"] for e in api_calls)
            },
            "agents": {
                "count": len(agents),
                "successful": sum(1 for e in agents if e["data"]["success"]),
                "by_type": {}  # Could aggregate by agent type
            },
            "errors": len(errors),
            "trace_file": str(self.session_file)
        }


# Global tracer instance
_tracer: Optional[SimpleTracer] = None


def get_tracer() -> SimpleTracer:
    """Get or create global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = SimpleTracer()
    return _tracer