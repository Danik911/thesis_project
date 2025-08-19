# OQ Agent Traceability and Implementation Patterns Research

## Research and Context (by context-collector)

This document provides comprehensive research on adding detailed traceability to the OQ (Operational Qualification) test generation agent to debug the critical reliability issue where the agent "works once then fails on subsequent runs."

### Code Examples and Patterns

#### 1. LlamaIndex Workflow Comprehensive Tracing

Based on LlamaIndex 0.12.0+ documentation and best practices, here are the key tracing patterns:

```python
from llama_index.core.workflow import WorkflowCheckpointer
from llama_index.utils.workflow import draw_most_recent_execution, draw_all_possible_flows
import asyncio
import logging
from datetime import datetime, UTC
from typing import Dict, Any, Optional

class TracedOQGenerationWorkflow(Workflow):
    """Enhanced OQ workflow with comprehensive tracing for debugging."""
    
    def __init__(self, timeout: int = 1800, enable_tracing: bool = True, **kwargs):
        super().__init__(timeout=timeout)
        
        # Initialize comprehensive logging
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.enable_tracing = enable_tracing
        self.execution_metadata = {}
        self.step_timings = {}
        self.resource_usage = {}
        
        # NO FALLBACKS: Ensure generator creation succeeds
        try:
            self.generator = OQTestGeneratorV2()
            self.logger.info("OQTestGeneratorV2 instantiated successfully")
        except Exception as e:
            self.logger.error(f"Failed to create OQTestGeneratorV2: {e}")
            raise RuntimeError(
                f"OQ generator instantiation failed: {e}. "
                f"Check OQTestGeneratorV2 constructor and dependencies."
            ) from e
    
    async def _trace_step_entry(self, step_name: str, event_data: Dict[str, Any]) -> str:
        """Trace workflow step entry with detailed context."""
        trace_id = f"{step_name}_{datetime.now(UTC).strftime('%H%M%S_%f')}"
        
        if self.enable_tracing:
            self.logger.info(f"🔍 STEP ENTRY: {step_name} | Trace ID: {trace_id}")
            self.logger.info(f"📊 EVENT DATA: {type(event_data).__name__} with {len(str(event_data))} chars")
            
            # Record step timing
            self.step_timings[trace_id] = {
                "step_name": step_name,
                "start_time": datetime.now(UTC),
                "event_type": type(event_data).__name__
            }
            
            # Log memory usage
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            self.resource_usage[trace_id] = {
                "memory_rss": memory_info.rss,
                "memory_vms": memory_info.vms,
                "cpu_percent": process.cpu_percent()
            }
            
        return trace_id
    
    async def _trace_step_exit(self, trace_id: str, result_data: Any, success: bool = True) -> None:
        """Trace workflow step exit with performance metrics."""
        if not self.enable_tracing or trace_id not in self.step_timings:
            return
            
        end_time = datetime.now(UTC)
        start_time = self.step_timings[trace_id]["start_time"]
        duration = (end_time - start_time).total_seconds()
        
        self.step_timings[trace_id].update({
            "end_time": end_time,
            "duration_seconds": duration,
            "success": success,
            "result_type": type(result_data).__name__ if result_data else "None"
        })
        
        # Log final memory state
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        self.resource_usage[trace_id]["final_memory_rss"] = memory_info.rss
        memory_delta = memory_info.rss - self.resource_usage[trace_id]["memory_rss"]
        
        status_icon = "✅" if success else "❌"
        self.logger.info(f"{status_icon} STEP EXIT: {self.step_timings[trace_id]['step_name']} | "
                        f"Duration: {duration:.2f}s | Memory Δ: {memory_delta / 1024 / 1024:.1f}MB")
        
        if not success:
            self.logger.error(f"💥 STEP FAILED: {trace_id} | Result: {str(result_data)[:200]}")

    @step
    async def start_oq_generation(
        self,
        ctx: Context,
        ev: StartEvent
    ) -> OQTestGenerationEvent:
        """Enhanced start step with comprehensive tracing."""
        trace_id = await self._trace_step_entry("start_oq_generation", ev.__dict__)
        
        try:
            self.workflow_start_time = datetime.now(UTC)
            
            # Enhanced data extraction with tracing
            self.logger.info(f"🔍 ANALYZING StartEvent: {type(ev).__name__}")
            
            # Store workflow execution context
            await ctx.set("workflow_trace_id", trace_id)
            await ctx.set("execution_start_time", self.workflow_start_time)
            
            # Extract data with detailed logging
            try:
                if hasattr(ev, 'data'):
                    data = ev.data if ev.data is not None else {}
                    self.logger.info(f"📋 StartEvent.data found: {len(str(data))} chars")
                elif hasattr(ev, 'get'):
                    data = ev.get("data", {})
                    self.logger.info(f"📋 StartEvent.get() used: {len(str(data))} chars")
                elif hasattr(ev, '__dict__') and 'data' in ev.__dict__:
                    data = ev.__dict__.get('data', {})
                    self.logger.info(f"📋 StartEvent.__dict__ access: {len(str(data))} chars")
                else:
                    self.logger.warning(f"🚨 StartEvent has no standard data access. Attributes: {dir(ev)}")
                    data = {}
                
                if not data:
                    self.logger.warning("⚠️  StartEvent contains empty data dictionary")
                    
            except Exception as e:
                self.logger.error(f"💥 Error extracting data from StartEvent: {e}")
                raise RuntimeError(
                    f"Failed to process StartEvent in OQ generation workflow. "
                    f"Error: {e}, StartEvent type: {type(ev)}, "
                    f"This may indicate LlamaIndex version compatibility issues."
                ) from e
            
            # Create generation event with tracing
            generation_event = OQTestGenerationEvent(
                gamp_category=data.get("gamp_category", 3),
                urs_content=data.get("urs_content", ""),
                document_metadata=data.get("document_metadata", {}),
                required_test_count=data.get("required_test_count", 5),
                test_strategy=data.get("test_strategy", {}),
                aggregated_context=data.get("agent_results", {}),
                categorization_confidence=data.get("categorization_confidence", 0.8),
                event_id=uuid4(),
                timestamp=datetime.now(UTC),
                correlation_id=data.get("correlation_id", uuid4())
            )
                
            # Store the event with tracing context
            await ctx.set("generation_event", generation_event)
            await ctx.set("generation_event_trace_id", trace_id)
            
            self.logger.info(f"🎯 GENERATION EVENT CREATED: GAMP {generation_event.gamp_category}, "
                           f"Tests: {generation_event.required_test_count}, "
                           f"Doc: {generation_event.document_metadata.get('name', 'Unknown')}")
            
            await self._trace_step_exit(trace_id, generation_event, success=True)
            return generation_event
            
        except Exception as e:
            await self._trace_step_exit(trace_id, str(e), success=False)
            raise

    @step
    async def generate_oq_tests(
        self,
        ctx: Context,
        ev: OQTestGenerationEvent
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """Enhanced test generation with batch monitoring and timeout tracking."""
        trace_id = await self._trace_step_entry("generate_oq_tests", ev.__dict__)
        
        try:
            self.logger.info(f"🚀 STARTING BATCH GENERATION: GAMP {ev.gamp_category}, "
                           f"Target: {ev.required_test_count} tests")
            
            # Store generation context for debugging
            generation_context = {
                "trace_id": trace_id,
                "gamp_category": ev.gamp_category,
                "required_test_count": ev.required_test_count,
                "document_name": ev.document_metadata.get('name', 'unknown'),
                "context_size": len(str(ev.aggregated_context)),
                "urs_size": len(ev.urs_content)
            }
            await ctx.set("current_generation_context", generation_context)
            
            # Enhanced monitoring for batch processing
            batch_monitor = BatchProcessingMonitor(
                trace_id=trace_id,
                logger=self.logger,
                expected_test_count=ev.required_test_count
            )
            
            # Execute generation with comprehensive monitoring
            result = await self._generate_oq_test_suite_with_monitoring(
                ctx, ev, batch_monitor
            )
            
            # Validate result with detailed logging
            if isinstance(result, ConsultationRequiredEvent):
                self.logger.warning(f"🔔 CONSULTATION REQUIRED: {result.consultation_type}")
                await self._trace_step_exit(trace_id, result, success=False)
                return result
            elif isinstance(result, OQTestSuiteEvent):
                self.logger.info(f"✅ GENERATION SUCCESS: {len(result.test_suite.test_cases)} tests generated")
                await self._trace_step_exit(trace_id, result, success=True)
                return result
            else:
                self.logger.error(f"💥 UNEXPECTED RESULT TYPE: {type(result)}")
                await self._trace_step_exit(trace_id, result, success=False)
                return ConsultationRequiredEvent(
                    consultation_type="oq_generation_system_error",
                    context={
                        "error": f"Unexpected result type: {type(result)}",
                        "trace_id": trace_id,
                        "generation_context": generation_context,
                        "timestamp": datetime.now(UTC).isoformat()
                    },
                    urgency="high",
                    required_expertise=["system_admin", "qa_engineer"],
                    triggering_step="generate_oq_tests",
                    consultation_id=uuid4()
                )
                
        except Exception as e:
            self.logger.error(f"💥 GENERATION FAILED: {e}")
            self.logger.error(f"🔍 TRACEBACK: {traceback.format_exc()}")
            await self._trace_step_exit(trace_id, str(e), success=False)
            
            return ConsultationRequiredEvent(
                consultation_type="oq_generation_system_error",
                context={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "trace_id": trace_id,
                    "gamp_category": ev.gamp_category,
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.now(UTC).isoformat()
                },
                urgency="high",
                required_expertise=["system_admin", "qa_engineer"],
                triggering_step="generate_oq_tests",
                consultation_id=uuid4()
            )

    async def _generate_oq_test_suite_with_monitoring(
        self,
        ctx: Context,
        ev: OQTestGenerationEvent,
        batch_monitor: 'BatchProcessingMonitor'
    ) -> OQTestSuiteEvent | ConsultationRequiredEvent:
        """Execute test generation with comprehensive batch monitoring."""
        
        try:
            start_time = time.time()
            batch_monitor.log_generation_start()
            
            # Convert gamp_category to proper enum
            from src.core.events import GAMPCategory
            
            if isinstance(ev.gamp_category, int):
                gamp_category_enum = GAMPCategory(ev.gamp_category)
            else:
                gamp_category_enum = ev.gamp_category
            
            self.logger.info(f"🔧 USING MODEL: DeepSeek V3 for GAMP Category {gamp_category_enum.value}")
            self.logger.info(f"📄 DOCUMENT: {ev.document_metadata.get('name', 'unknown')}")
            self.logger.info(f"🎯 TARGET COUNT: {ev.required_test_count} tests")
            
            # Monitor generation progress with detailed logging
            batch_monitor.log_batch_start(1, ev.required_test_count)
            
            suite_result = await self.generator.generate_oq_test_suite(
                gamp_category=gamp_category_enum,
                urs_content=ev.urs_content,
                document_name=ev.document_metadata.get("name", "unknown"),
                context_data=ev.aggregated_context
            )
            
            generation_time = time.time() - start_time
            batch_monitor.log_batch_complete(1, len(suite_result.test_cases) if suite_result else 0)
            
            self.logger.info(f"🎉 GENERATION COMPLETE: {generation_time:.2f} seconds")
            
            # Enhanced result validation
            if not suite_result:
                self.logger.error("💥 NULL RESULT: Generator returned None")
                return ConsultationRequiredEvent(
                    consultation_type="oq_generation_empty_result",
                    context={
                        "error": "Generation returned None result",
                        "gamp_category": ev.gamp_category,
                        "generation_time": generation_time,
                        "batch_monitor_data": batch_monitor.get_summary(),
                        "timestamp": datetime.now(UTC).isoformat()
                    },
                    urgency="normal",
                    required_expertise=["qa_engineer"],
                    triggering_step="_generate_oq_test_suite_with_monitoring",
                    consultation_id=uuid4()
                )
            
            # Validate test suite structure
            if not hasattr(suite_result, 'test_cases') or not suite_result.test_cases:
                self.logger.error(f"💥 INVALID STRUCTURE: {type(suite_result)} missing test_cases")
                return ConsultationRequiredEvent(
                    consultation_type="oq_generation_invalid_result", 
                    context={
                        "error": "Generation returned object without test_cases",
                        "result_type": str(type(suite_result)),
                        "gamp_category": ev.gamp_category,
                        "generation_time": generation_time,
                        "batch_monitor_data": batch_monitor.get_summary(),
                        "timestamp": datetime.now(UTC).isoformat()
                    },
                    urgency="normal",
                    required_expertise=["qa_engineer"],
                    triggering_step="_generate_oq_test_suite_with_monitoring",
                    consultation_id=uuid4()
                )
            
            # Success logging
            test_count = len(suite_result.test_cases)
            self.logger.info(f"✅ SUCCESS: {test_count} test cases generated")
            self.logger.info(f"📊 SUITE ID: {suite_result.suite_id}")
            self.logger.info(f"⏱️  TIMING: {generation_time:.2f}s total")
            
            # Create result event with enhanced metadata
            return OQTestSuiteEvent(
                test_suite=suite_result,
                generation_metadata={
                    "generation_time_seconds": generation_time,
                    "workflow_duration": (
                        datetime.now(UTC) - self.workflow_start_time
                    ).total_seconds() if self.workflow_start_time else None,
                    "gamp_category": ev.gamp_category,
                    "num_test_cases": test_count,
                    "generator_version": "v2",
                    "batch_monitor_summary": batch_monitor.get_summary(),
                    "resource_usage": self.get_resource_summary()
                },
                generation_successful=True,
                compliance_validation={"gamp5_compliant": True},
                event_id=uuid4(),
                timestamp=datetime.now(UTC),
                correlation_id=ev.correlation_id
            )
            
        except Exception as e:
            self.logger.error(f"💥 GENERATION IMPLEMENTATION ERROR: {e}")
            self.logger.error(f"🔍 FULL TRACEBACK: {traceback.format_exc()}")
            
            return ConsultationRequiredEvent(
                consultation_type="oq_generation_implementation_error",
                context={
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "gamp_category": ev.gamp_category,
                    "traceback": traceback.format_exc(),
                    "batch_monitor_data": batch_monitor.get_summary() if 'batch_monitor' in locals() else {},
                    "timestamp": datetime.now(UTC).isoformat()
                },
                urgency="high",
                required_expertise=["system_admin", "qa_engineer"],
                triggering_step="_generate_oq_test_suite_with_monitoring",
                consultation_id=uuid4()
            )

    def get_resource_summary(self) -> Dict[str, Any]:
        """Get comprehensive resource usage summary."""
        if not self.resource_usage:
            return {}
        
        total_memory_delta = 0
        max_memory = 0
        step_count = len(self.resource_usage)
        
        for trace_id, usage in self.resource_usage.items():
            if "final_memory_rss" in usage:
                memory_delta = usage["final_memory_rss"] - usage["memory_rss"]
                total_memory_delta += memory_delta
                max_memory = max(max_memory, usage["final_memory_rss"])
        
        return {
            "total_steps": step_count,
            "total_memory_delta_mb": total_memory_delta / 1024 / 1024,
            "max_memory_usage_mb": max_memory / 1024 / 1024,
            "step_timings": {tid: timing["duration_seconds"] for tid, timing in self.step_timings.items() if "duration_seconds" in timing}
        }
```

#### 2. Batch Processing Monitor

```python
class BatchProcessingMonitor:
    """Comprehensive monitoring for batch test generation operations."""
    
    def __init__(self, trace_id: str, logger: logging.Logger, expected_test_count: int):
        self.trace_id = trace_id
        self.logger = logger
        self.expected_test_count = expected_test_count
        self.batch_data = {}
        self.generation_start_time = None
        self.timeouts_detected = []
        self.errors_encountered = []
    
    def log_generation_start(self):
        """Log the start of test generation process."""
        self.generation_start_time = datetime.now(UTC)
        self.logger.info(f"🏁 BATCH START: Trace {self.trace_id} | Target: {self.expected_test_count} tests")
    
    def log_batch_start(self, batch_num: int, batch_size: int):
        """Log the start of a specific batch."""
        batch_start_time = datetime.now(UTC)
        self.batch_data[batch_num] = {
            "batch_num": batch_num,
            "batch_size": batch_size,
            "start_time": batch_start_time,
            "status": "in_progress"
        }
        
        self.logger.info(f"🔄 BATCH {batch_num} START: {batch_size} tests")
        
        # Calculate ETA
        if self.generation_start_time:
            elapsed = (batch_start_time - self.generation_start_time).total_seconds()
            if batch_num > 1:
                avg_batch_time = elapsed / (batch_num - 1)
                remaining_batches = (self.expected_test_count // batch_size) - batch_num + 1
                eta_seconds = remaining_batches * avg_batch_time
                self.logger.info(f"⏰ ETA: {eta_seconds:.0f}s remaining")
    
    def log_batch_complete(self, batch_num: int, actual_test_count: int):
        """Log the completion of a specific batch."""
        if batch_num not in self.batch_data:
            self.logger.warning(f"⚠️  BATCH {batch_num} not found in tracking data")
            return
        
        batch_end_time = datetime.now(UTC)
        batch_duration = (batch_end_time - self.batch_data[batch_num]["start_time"]).total_seconds()
        
        self.batch_data[batch_num].update({
            "end_time": batch_end_time,
            "duration_seconds": batch_duration,
            "actual_test_count": actual_test_count,
            "status": "completed"
        })
        
        self.logger.info(f"✅ BATCH {batch_num} COMPLETE: {actual_test_count} tests in {batch_duration:.2f}s")
        
        # Performance analysis
        tests_per_second = actual_test_count / batch_duration if batch_duration > 0 else 0
        self.logger.info(f"📈 PERFORMANCE: {tests_per_second:.2f} tests/second")
    
    def log_batch_timeout(self, batch_num: int, timeout_seconds: int):
        """Log a batch timeout event."""
        timeout_time = datetime.now(UTC)
        timeout_data = {
            "batch_num": batch_num,
            "timeout_seconds": timeout_seconds,
            "timeout_time": timeout_time
        }
        
        self.timeouts_detected.append(timeout_data)
        self.logger.error(f"⏰ BATCH {batch_num} TIMEOUT: {timeout_seconds}s exceeded")
        
        if batch_num in self.batch_data:
            self.batch_data[batch_num]["status"] = "timeout"
    
    def log_batch_error(self, batch_num: int, error: Exception):
        """Log a batch error event."""
        error_time = datetime.now(UTC)
        error_data = {
            "batch_num": batch_num,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_time": error_time
        }
        
        self.errors_encountered.append(error_data)
        self.logger.error(f"💥 BATCH {batch_num} ERROR: {type(error).__name__}: {str(error)}")
        
        if batch_num in self.batch_data:
            self.batch_data[batch_num]["status"] = "error"
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive batch processing summary."""
        total_duration = 0
        total_tests_generated = 0
        successful_batches = 0
        
        for batch_data in self.batch_data.values():
            if batch_data["status"] == "completed":
                total_duration += batch_data.get("duration_seconds", 0)
                total_tests_generated += batch_data.get("actual_test_count", 0)
                successful_batches += 1
        
        return {
            "trace_id": self.trace_id,
            "expected_test_count": self.expected_test_count,
            "actual_test_count": total_tests_generated,
            "total_batches": len(self.batch_data),
            "successful_batches": successful_batches,
            "total_duration_seconds": total_duration,
            "timeouts_detected": len(self.timeouts_detected),
            "errors_encountered": len(self.errors_encountered),
            "performance_metrics": {
                "tests_per_second": total_tests_generated / total_duration if total_duration > 0 else 0,
                "avg_batch_duration": total_duration / successful_batches if successful_batches > 0 else 0
            },
            "timeout_details": self.timeouts_detected,
            "error_details": self.errors_encountered
        }
```

#### 3. Phoenix Observability Integration

```python
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from phoenix.otel import register

class EnhancedPhoenixObservability:
    """Enhanced Phoenix observability for OQ agent debugging."""
    
    def __init__(self, endpoint: str = "http://localhost:6006"):
        self.endpoint = endpoint
        self.tracer_provider = None
        self.instrumentor = None
    
    def setup_instrumentation(self):
        """Setup comprehensive Phoenix instrumentation."""
        try:
            # Register Phoenix tracer
            self.tracer_provider = register(
                project_name="OQ_Test_Generation",
                endpoint=self.endpoint
            )
            
            # Initialize LlamaIndex instrumentation
            self.instrumentor = LlamaIndexInstrumentor()
            self.instrumentor.instrument(tracer_provider=self.tracer_provider)
            
            logging.info("✅ Phoenix observability initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"💥 Failed to setup Phoenix observability: {e}")
            return False
    
    def add_custom_span(self, span_name: str, attributes: Dict[str, Any] = None):
        """Add custom span with OQ-specific attributes."""
        if not self.tracer_provider:
            return None
        
        tracer = self.tracer_provider.get_tracer(__name__)
        span = tracer.start_span(span_name)
        
        # Add OQ-specific attributes
        oq_attributes = {
            "oq.operation": span_name,
            "oq.timestamp": datetime.now(UTC).isoformat(),
            "oq.trace_level": "detailed"
        }
        
        if attributes:
            oq_attributes.update(attributes)
        
        for key, value in oq_attributes.items():
            span.set_attribute(key, str(value))
        
        return span
    
    def trace_workflow_execution(self, workflow_instance: TracedOQGenerationWorkflow):
        """Add comprehensive tracing to workflow execution."""
        
        @contextmanager
        def span_context(span_name: str, attributes: Dict[str, Any] = None):
            span = self.add_custom_span(span_name, attributes)
            try:
                yield span
            except Exception as e:
                if span:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            finally:
                if span:
                    span.end()
        
        # Monkey patch workflow methods to add tracing
        original_start_oq_generation = workflow_instance.start_oq_generation
        original_generate_oq_tests = workflow_instance.generate_oq_tests
        
        async def traced_start_oq_generation(ctx, ev):
            with span_context("oq.workflow.start", {
                "oq.event_type": type(ev).__name__,
                "oq.workflow_start_time": datetime.now(UTC).isoformat()
            }):
                return await original_start_oq_generation(ctx, ev)
        
        async def traced_generate_oq_tests(ctx, ev):
            with span_context("oq.workflow.generate_tests", {
                "oq.gamp_category": ev.gamp_category,
                "oq.required_test_count": ev.required_test_count,
                "oq.document_name": ev.document_metadata.get('name', 'unknown')
            }):
                return await original_generate_oq_tests(ctx, ev)
        
        workflow_instance.start_oq_generation = traced_start_oq_generation
        workflow_instance.generate_oq_tests = traced_generate_oq_tests
        
        return workflow_instance
```

#### 4. Workflow Checkpointing and Resume Patterns

```python
from llama_index.core.workflow.checkpointer import WorkflowCheckpointer

class OQWorkflowDebugger:
    """Comprehensive debugging utilities for OQ workflows."""
    
    def __init__(self, workflow: TracedOQGenerationWorkflow):
        self.workflow = workflow
        self.checkpointer = WorkflowCheckpointer(workflow=workflow)
        self.execution_history = []
    
    async def run_with_debugging(self, **kwargs) -> Dict[str, Any]:
        """Run workflow with comprehensive debugging and checkpointing."""
        
        # Enable verbose mode for detailed step tracking
        self.workflow.verbose = True
        
        try:
            # Run with checkpointing
            handler = self.checkpointer.run(**kwargs)
            result = await handler
            
            # Analyze execution path
            execution_analysis = self.analyze_execution(handler.run_id)
            
            return {
                "result": result,
                "execution_analysis": execution_analysis,
                "checkpoints": self.get_checkpoint_summary(handler.run_id),
                "performance_metrics": self.workflow.get_resource_summary()
            }
            
        except Exception as e:
            # Capture failure state
            failure_analysis = self.analyze_failure(e)
            
            return {
                "result": None,
                "error": str(e),
                "failure_analysis": failure_analysis,
                "partial_checkpoints": self.get_all_checkpoints()
            }
    
    async def run_stepwise_debugging(self, **kwargs) -> Dict[str, Any]:
        """Run workflow step-by-step for detailed analysis."""
        
        self.workflow.verbose = True
        handler = self.workflow.run(stepwise=True, **kwargs)
        
        step_results = []
        step_number = 0
        
        try:
            while produced_events := await handler.run_step():
                step_number += 1
                
                step_data = {
                    "step_number": step_number,
                    "events_produced": len(produced_events),
                    "event_types": [type(ev).__name__ for ev in produced_events],
                    "timestamp": datetime.now(UTC).isoformat()
                }
                
                logging.info(f"🔍 STEP {step_number}: {step_data['event_types']}")
                
                # Analyze each event
                for i, event in enumerate(produced_events):
                    event_analysis = self.analyze_event(event, step_number, i)
                    step_data[f"event_{i}_analysis"] = event_analysis
                    
                    # Send event to continue workflow
                    handler.ctx.send_event(event)
                
                step_results.append(step_data)
                
                # Check for potential issues
                if step_number > 20:  # Prevent infinite loops
                    logging.warning("⚠️  Step limit reached - potential infinite loop")
                    break
            
            # Get final result
            final_result = await handler
            
            return {
                "result": final_result,
                "step_analysis": step_results,
                "total_steps": step_number,
                "execution_successful": True
            }
            
        except Exception as e:
            return {
                "result": None,
                "error": str(e),
                "step_analysis": step_results,
                "total_steps": step_number,
                "execution_successful": False,
                "failure_step": step_number
            }
    
    def analyze_execution(self, run_id: str) -> Dict[str, Any]:
        """Analyze workflow execution for performance insights."""
        checkpoints = self.checkpointer.checkpoints.get(run_id, [])
        
        analysis = {
            "run_id": run_id,
            "total_checkpoints": len(checkpoints),
            "steps_completed": [cp.last_completed_step for cp in checkpoints],
            "execution_path": [],
            "potential_issues": []
        }
        
        # Analyze execution path
        for checkpoint in checkpoints:
            analysis["execution_path"].append({
                "step": checkpoint.last_completed_step,
                "timestamp": checkpoint.timestamp if hasattr(checkpoint, 'timestamp') else None
            })
        
        # Identify potential issues
        if len(checkpoints) == 0:
            analysis["potential_issues"].append("No checkpoints created - workflow may have failed immediately")
        
        if len(checkpoints) > 10:
            analysis["potential_issues"].append("Excessive checkpoints - potential loop or retry behavior")
        
        return analysis
    
    def analyze_event(self, event: Any, step_number: int, event_index: int) -> Dict[str, Any]:
        """Analyze individual workflow event for debugging insights."""
        
        analysis = {
            "event_type": type(event).__name__,
            "step_number": step_number,
            "event_index": event_index,
            "timestamp": datetime.now(UTC).isoformat(),
            "data_size": len(str(event.__dict__)) if hasattr(event, '__dict__') else 0,
            "attributes": []
        }
        
        # Extract key attributes
        if hasattr(event, '__dict__'):
            for key, value in event.__dict__.items():
                if not key.startswith('_'):
                    analysis["attributes"].append({
                        "name": key,
                        "type": type(value).__name__,
                        "size": len(str(value)) if isinstance(value, (str, list, dict)) else None
                    })
        
        # Event-specific analysis
        if hasattr(event, 'gamp_category'):
            analysis["gamp_category"] = event.gamp_category
        
        if hasattr(event, 'required_test_count'):
            analysis["required_test_count"] = event.required_test_count
        
        if hasattr(event, 'test_suite') and hasattr(event.test_suite, 'test_cases'):
            analysis["generated_test_count"] = len(event.test_suite.test_cases)
        
        return analysis
    
    def get_checkpoint_summary(self, run_id: str) -> Dict[str, Any]:
        """Get comprehensive checkpoint summary."""
        checkpoints = self.checkpointer.checkpoints.get(run_id, [])
        
        return {
            "run_id": run_id,
            "checkpoint_count": len(checkpoints),
            "completed_steps": [cp.last_completed_step for cp in checkpoints],
            "checkpoint_details": [
                {
                    "step": cp.last_completed_step,
                    "data_size": len(str(cp.__dict__)) if hasattr(cp, '__dict__') else 0
                }
                for cp in checkpoints
            ]
        }
    
    def analyze_failure(self, exception: Exception) -> Dict[str, Any]:
        """Analyze workflow failure for debugging insights."""
        
        return {
            "error_type": type(exception).__name__,
            "error_message": str(exception),
            "traceback": traceback.format_exc(),
            "workflow_state": {
                "step_timings": self.workflow.step_timings,
                "resource_usage": self.workflow.resource_usage,
                "execution_metadata": self.workflow.execution_metadata
            },
            "checkpoint_state": self.get_all_checkpoints(),
            "diagnostic_suggestions": self.generate_diagnostic_suggestions(exception)
        }
    
    def generate_diagnostic_suggestions(self, exception: Exception) -> List[str]:
        """Generate diagnostic suggestions based on error type."""
        
        suggestions = []
        error_type = type(exception).__name__
        error_message = str(exception).lower()
        
        if "timeout" in error_message:
            suggestions.extend([
                "Check network connectivity to LLM provider",
                "Increase workflow timeout parameter",
                "Review batch size settings for progressive generation",
                "Monitor resource usage during generation"
            ])
        
        elif "memory" in error_message or "oom" in error_message:
            suggestions.extend([
                "Reduce batch size for test generation",
                "Clear context between workflow runs",
                "Monitor memory usage patterns",
                "Consider streaming generation approach"
            ])
        
        elif "json" in error_message or "parse" in error_message:
            suggestions.extend([
                "Review LLM response format validation",
                "Check YAML fallback parser functionality",
                "Validate prompt templates for JSON structure",
                "Monitor LLM response quality"
            ])
        
        elif "connection" in error_message or "network" in error_message:
            suggestions.extend([
                "Verify LLM provider API connectivity",
                "Check API key configuration",
                "Review network firewall settings",
                "Implement connection retry logic"
            ])
        
        else:
            suggestions.extend([
                "Review workflow step dependencies",
                "Check context store state consistency",
                "Validate input event data structure",
                "Monitor resource cleanup between runs"
            ])
        
        return suggestions
```

### Implementation Gotchas

#### 1. State Accumulation Between Runs

**Critical Issue**: The "works once then fails" pattern often indicates state accumulation in the workflow context or generator instance:

```python
# ❌ PROBLEM: State accumulation in workflow instance
class OQGenerationWorkflow(Workflow):
    def __init__(self):
        super().__init__()
        self.generator = OQTestGeneratorV2()  # Shared instance
        self.cached_results = {}  # Accumulates state
        self.execution_count = 0  # Never reset

# ✅ SOLUTION: Clean state management
class OQGenerationWorkflow(Workflow):
    def __init__(self):
        super().__init__()
        # Don't store stateful objects as instance variables
    
    async def _get_fresh_generator(self) -> OQTestGeneratorV2:
        """Create a fresh generator instance for each run."""
        return OQTestGeneratorV2(
            verbose=False,
            generation_timeout=900
        )
    
    async def cleanup_after_run(self, ctx: Context):
        """Explicit cleanup after each workflow run."""
        # Clear context store
        await ctx.store.clear()
        
        # Reset any accumulated state
        self.step_timings.clear()
        self.resource_usage.clear()
        self.execution_metadata.clear()
```

#### 2. Context Store Pollution

**Issue**: LlamaIndex workflow context stores can accumulate data between runs:

```python
# ❌ PROBLEM: Context pollution
@step
async def generate_oq_tests(self, ctx: Context, ev: OQTestGenerationEvent):
    # Previous run data may still be in context
    old_data = await ctx.store.get("previous_generation_result")  # May be stale
    
# ✅ SOLUTION: Explicit context management
@step
async def generate_oq_tests(self, ctx: Context, ev: OQTestGenerationEvent):
    # Clear any stale data at start of step
    correlation_id = str(ev.correlation_id)
    
    # Use correlation-specific keys
    await ctx.store.set(f"generation_start_{correlation_id}", datetime.now(UTC))
    
    # Explicit cleanup pattern
    try:
        result = await self._generate_with_cleanup(ctx, ev)
        return result
    finally:
        # Clean up correlation-specific data
        keys_to_clean = [
            f"generation_start_{correlation_id}",
            f"generation_context_{correlation_id}",
            f"batch_monitor_{correlation_id}"
        ]
        for key in keys_to_clean:
            await ctx.store.delete(key)
```

#### 3. Resource Leak Detection

**Issue**: LLM connections, file handles, or memory allocations may not be properly cleaned up:

```python
class ResourceTracker:
    """Track and cleanup resources during workflow execution."""
    
    def __init__(self):
        self.tracked_resources = {}
        self.cleanup_callbacks = []
    
    def track_resource(self, resource_id: str, resource: Any, cleanup_callback: callable):
        """Track a resource for cleanup."""
        self.tracked_resources[resource_id] = resource
        self.cleanup_callbacks.append((resource_id, cleanup_callback))
    
    async def cleanup_all(self):
        """Cleanup all tracked resources."""
        for resource_id, cleanup_callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(cleanup_callback):
                    await cleanup_callback()
                else:
                    cleanup_callback()
                logging.info(f"✅ Cleaned up resource: {resource_id}")
            except Exception as e:
                logging.error(f"💥 Failed to cleanup {resource_id}: {e}")
        
        self.tracked_resources.clear()
        self.cleanup_callbacks.clear()

# Usage in workflow
@step
async def generate_oq_tests(self, ctx: Context, ev: OQTestGenerationEvent):
    resource_tracker = ResourceTracker()
    
    try:
        # Track LLM instance
        llm = LLMConfig.get_llm(max_tokens=4000)
        resource_tracker.track_resource("llm", llm, lambda: setattr(llm, '_client', None))
        
        # Track file handles
        temp_file = tempfile.NamedTemporaryFile()
        resource_tracker.track_resource("temp_file", temp_file, temp_file.close)
        
        # Execute generation
        result = await self._generate_tests(llm, ev)
        return result
        
    finally:
        # Always cleanup resources
        await resource_tracker.cleanup_all()
```

#### 4. Progressive Generation State Tracking

**Issue**: Batch generation state can become inconsistent between batches:

```python
class ProgressiveGenerationTracker:
    """Track state across progressive test generation batches."""
    
    def __init__(self, trace_id: str, total_tests: int):
        self.trace_id = trace_id
        self.total_tests = total_tests
        self.completed_batches = []
        self.failed_batches = []
        self.generated_test_ids = set()
        self.batch_contexts = {}
    
    def start_batch(self, batch_num: int, batch_size: int, context: Dict[str, Any]):
        """Start tracking a new batch."""
        self.batch_contexts[batch_num] = {
            "batch_num": batch_num,
            "batch_size": batch_size,
            "start_time": datetime.now(UTC),
            "context": context,
            "status": "in_progress"
        }
    
    def complete_batch(self, batch_num: int, test_ids: List[str]):
        """Mark batch as completed with generated test IDs."""
        if batch_num not in self.batch_contexts:
            raise ValueError(f"Batch {batch_num} not started")
        
        # Check for duplicate test IDs
        duplicates = self.generated_test_ids.intersection(set(test_ids))
        if duplicates:
            raise ValueError(f"Duplicate test IDs detected: {duplicates}")
        
        self.generated_test_ids.update(test_ids)
        self.completed_batches.append(batch_num)
        self.batch_contexts[batch_num]["status"] = "completed"
        self.batch_contexts[batch_num]["test_ids"] = test_ids
        self.batch_contexts[batch_num]["end_time"] = datetime.now(UTC)
    
    def fail_batch(self, batch_num: int, error: Exception):
        """Mark batch as failed."""
        self.failed_batches.append(batch_num)
        self.batch_contexts[batch_num]["status"] = "failed"
        self.batch_contexts[batch_num]["error"] = str(error)
        self.batch_contexts[batch_num]["end_time"] = datetime.now(UTC)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get comprehensive state summary."""
        return {
            "trace_id": self.trace_id,
            "total_tests_required": self.total_tests,
            "total_tests_generated": len(self.generated_test_ids),
            "completed_batches": len(self.completed_batches),
            "failed_batches": len(self.failed_batches),
            "batch_details": self.batch_contexts,
            "generated_test_ids": sorted(list(self.generated_test_ids)),
            "state_consistent": self._validate_state_consistency()
        }
    
    def _validate_state_consistency(self) -> bool:
        """Validate that the tracking state is consistent."""
        try:
            # Check that completed + failed batches don't exceed total
            total_processed = len(self.completed_batches) + len(self.failed_batches)
            
            # Check that test ID count matches batch outputs
            expected_tests = sum(
                len(self.batch_contexts[batch]["test_ids"])
                for batch in self.completed_batches
                if "test_ids" in self.batch_contexts[batch]
            )
            
            return len(self.generated_test_ids) == expected_tests
            
        except Exception:
            return False
```

### Regulatory Considerations

#### GAMP-5 Traceability Requirements

All OQ test generation must maintain complete traceability for regulatory compliance:

```python
class GAMP5TraceabilityLogger:
    """Comprehensive traceability logging for GAMP-5 compliance."""
    
    def __init__(self, audit_log_path: str):
        self.audit_log_path = audit_log_path
        self.audit_entries = []
    
    def log_generation_event(
        self,
        event_type: str,
        gamp_category: int,
        user_id: str,
        details: Dict[str, Any]
    ):
        """Log a generation event with full regulatory context."""
        
        audit_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "gamp_category": gamp_category,
            "user_id": user_id,
            "session_id": details.get("session_id"),
            "trace_id": details.get("trace_id"),
            "workflow_version": details.get("workflow_version", "unknown"),
            "llm_model": details.get("llm_model", "unknown"),
            "generation_parameters": details.get("generation_parameters", {}),
            "validation_results": details.get("validation_results", {}),
            "compliance_checks": details.get("compliance_checks", {}),
            "data_integrity_hash": self._calculate_integrity_hash(details)
        }
        
        self.audit_entries.append(audit_entry)
        
        # Write to persistent audit log
        self._write_audit_entry(audit_entry)
    
    def _calculate_integrity_hash(self, details: Dict[str, Any]) -> str:
        """Calculate hash for data integrity verification."""
        import hashlib
        import json
        
        # Create deterministic string representation
        content = json.dumps(details, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _write_audit_entry(self, entry: Dict[str, Any]):
        """Write audit entry to persistent storage."""
        try:
            with open(self.audit_log_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logging.error(f"Failed to write audit entry: {e}")
```

#### Timeout Debugging Strategies

**Issue**: Timeouts are critical for pharmaceutical systems and must be comprehensively tracked:

```python
class TimeoutDiagnosticCollector:
    """Collect comprehensive diagnostic information for timeout debugging."""
    
    def __init__(self):
        self.timeout_events = []
        self.system_metrics = []
        self.network_metrics = []
    
    async def monitor_operation_with_timeout(
        self,
        operation: callable,
        timeout_seconds: int,
        operation_name: str,
        context: Dict[str, Any]
    ):
        """Monitor an operation for timeout behavior with comprehensive diagnostics."""
        
        start_time = datetime.now(UTC)
        
        # Start system monitoring
        monitoring_task = asyncio.create_task(
            self._monitor_system_metrics(operation_name)
        )
        
        try:
            # Execute operation with timeout
            result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
            
            # Operation completed successfully
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()
            
            self._log_successful_operation(operation_name, duration, context)
            return result
            
        except asyncio.TimeoutError:
            # Operation timed out - collect diagnostics
            end_time = datetime.now(UTC)
            
            timeout_diagnostics = await self._collect_timeout_diagnostics(
                operation_name, start_time, end_time, timeout_seconds, context
            )
            
            self.timeout_events.append(timeout_diagnostics)
            
            # Log detailed timeout information
            logging.error(f"⏰ TIMEOUT DETECTED: {operation_name}")
            logging.error(f"🔍 DIAGNOSTICS: {timeout_diagnostics}")
            
            raise
            
        finally:
            # Stop monitoring
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _collect_timeout_diagnostics(
        self,
        operation_name: str,
        start_time: datetime,
        end_time: datetime,
        timeout_seconds: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect comprehensive timeout diagnostics."""
        
        import psutil
        import requests
        
        diagnostics = {
            "operation_name": operation_name,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "timeout_seconds": timeout_seconds,
            "actual_duration": (end_time - start_time).total_seconds(),
            "context": context
        }
        
        # System metrics
        try:
            process = psutil.Process()
            diagnostics["system_metrics"] = {
                "memory_rss_mb": process.memory_info().rss / 1024 / 1024,
                "memory_vms_mb": process.memory_info().vms / 1024 / 1024,
                "cpu_percent": process.cpu_percent(),
                "open_files": len(process.open_files()),
                "num_threads": process.num_threads()
            }
        except Exception as e:
            diagnostics["system_metrics_error"] = str(e)
        
        # Network connectivity
        try:
            # Test basic connectivity
            response = requests.get("https://httpbin.org/status/200", timeout=5)
            diagnostics["network_connectivity"] = {
                "basic_connectivity": response.status_code == 200,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            diagnostics["network_connectivity"] = {
                "basic_connectivity": False,
                "error": str(e)
            }
        
        # LLM provider specific checks
        if "llm" in operation_name.lower():
            diagnostics["llm_diagnostics"] = await self._check_llm_provider_status()
        
        return diagnostics
    
    async def _check_llm_provider_status(self) -> Dict[str, Any]:
        """Check LLM provider specific status."""
        diagnostics = {}
        
        # Check OpenAI API status
        try:
            import openai
            client = openai.AsyncOpenAI()
            
            # Simple API health check
            start_time = time.time()
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            end_time = time.time()
            
            diagnostics["openai_api"] = {
                "status": "healthy",
                "response_time_ms": (end_time - start_time) * 1000,
                "model_accessible": True
            }
            
        except Exception as e:
            diagnostics["openai_api"] = {
                "status": "error",
                "error": str(e),
                "model_accessible": False
            }
        
        return diagnostics
    
    async def _monitor_system_metrics(self, operation_name: str):
        """Continuously monitor system metrics during operation."""
        while True:
            try:
                await asyncio.sleep(1)  # Monitor every second
                
                import psutil
                process = psutil.Process()
                
                metric_entry = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "operation": operation_name,
                    "memory_rss_mb": process.memory_info().rss / 1024 / 1024,
                    "cpu_percent": process.cpu_percent()
                }
                
                self.system_metrics.append(metric_entry)
                
                # Keep only last 300 entries (5 minutes at 1 second intervals)
                if len(self.system_metrics) > 300:
                    self.system_metrics.pop(0)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.warning(f"Error monitoring system metrics: {e}")
                await asyncio.sleep(1)
    
    def get_timeout_summary(self) -> Dict[str, Any]:
        """Get comprehensive timeout analysis summary."""
        if not self.timeout_events:
            return {"timeouts_detected": 0, "system_healthy": True}
        
        return {
            "timeouts_detected": len(self.timeout_events),
            "timeout_details": self.timeout_events[-5:],  # Last 5 timeouts
            "common_timeout_operations": self._analyze_timeout_patterns(),
            "system_metrics_summary": self._summarize_system_metrics(),
            "recommendations": self._generate_timeout_recommendations()
        }
    
    def _analyze_timeout_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in timeout events."""
        if not self.timeout_events:
            return {}
        
        operation_counts = {}
        for event in self.timeout_events:
            op_name = event.get("operation_name", "unknown")
            operation_counts[op_name] = operation_counts.get(op_name, 0) + 1
        
        return {
            "most_frequent_timeouts": sorted(
                operation_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3],
            "total_unique_operations": len(operation_counts)
        }
    
    def _generate_timeout_recommendations(self) -> List[str]:
        """Generate recommendations based on timeout analysis."""
        recommendations = []
        
        if len(self.timeout_events) > 0:
            recommendations.append("High timeout frequency detected - review system resources")
        
        if any("llm" in event.get("operation_name", "").lower() for event in self.timeout_events):
            recommendations.extend([
                "LLM timeouts detected - check API provider status",
                "Consider increasing LLM-specific timeout values",
                "Review prompt complexity and token limits"
            ])
        
        if any(event.get("system_metrics", {}).get("memory_rss_mb", 0) > 1000 for event in self.timeout_events):
            recommendations.append("High memory usage during timeouts - investigate memory leaks")
        
        return recommendations
```

### Specific Answers to Research Questions

#### 1. Event Tracing: How can we trace the exact event flow through the OQ workflow steps?

**Solution**: Implement comprehensive event flow tracing using LlamaIndex's verbose mode, checkpointing, and custom tracing:

```python
# Enable verbose workflow execution
workflow = TracedOQGenerationWorkflow(verbose=True, enable_tracing=True)

# Use checkpointing for step-by-step analysis
checkpointer = WorkflowCheckpointer(workflow=workflow)
handler = checkpointer.run(**input_data)

# Implement stepwise execution for detailed analysis
handler = workflow.run(stepwise=True, **input_data)
while produced_events := await handler.run_step():
    for event in produced_events:
        # Log each event with detailed context
        logger.info(f"Event: {type(event).__name__}, Data: {event.__dict__}")
        handler.ctx.send_event(event)
```

#### 2. Batch Monitoring: How to add visibility into batch processing (2 tests at a time)?

**Solution**: Implement comprehensive batch monitoring with the `BatchProcessingMonitor` class:

```python
# Monitor each batch with detailed logging
batch_monitor = BatchProcessingMonitor(
    trace_id=trace_id,
    logger=logger,
    expected_test_count=ev.required_test_count
)

# Track batch progress
batch_monitor.log_batch_start(batch_num, batch_size)
# ... batch execution ...
batch_monitor.log_batch_complete(batch_num, actual_test_count)

# Get comprehensive batch summary
summary = batch_monitor.get_summary()
```

#### 3. Timeout Debugging: What's the best way to identify where timeouts occur?

**Solution**: Use the `TimeoutDiagnosticCollector` for comprehensive timeout analysis:

```python
timeout_collector = TimeoutDiagnosticCollector()

# Monitor operations with timeout diagnostics
result = await timeout_collector.monitor_operation_with_timeout(
    operation=lambda: self.generator.generate_oq_test_suite(...),
    timeout_seconds=300,
    operation_name="oq_test_generation",
    context={"gamp_category": ev.gamp_category, "test_count": ev.required_test_count}
)
```

#### 4. State Tracking: How to track workflow state between consecutive runs?

**Solution**: Implement explicit state management and cleanup:

```python
# Use correlation-specific context keys
correlation_id = str(ev.correlation_id)
await ctx.store.set(f"generation_context_{correlation_id}", context_data)

# Implement cleanup after each run
async def cleanup_after_run(self, ctx: Context, correlation_id: str):
    keys_to_clean = [
        f"generation_context_{correlation_id}",
        f"batch_monitor_{correlation_id}",
        f"resource_tracker_{correlation_id}"
    ]
    for key in keys_to_clean:
        await ctx.store.delete(key)
```

#### 5. Performance Bottlenecks: How to identify which step is causing the hang?

**Solution**: Combine multiple tracing approaches:

```python
# 1. Use workflow checkpointing to identify last successful step
checkpoints = checkpointer.checkpoints[run_id]
last_step = checkpoints[-1].last_completed_step if checkpoints else "none"

# 2. Implement step timing analysis
step_timings = workflow.step_timings
bottleneck_step = max(step_timings.items(), key=lambda x: x[1].get("duration_seconds", 0))

# 3. Monitor resource usage per step
resource_summary = workflow.get_resource_summary()
memory_intensive_step = max(resource_summary["step_timings"].items(), key=lambda x: x[1])

# 4. Use Phoenix observability for detailed span analysis
phoenix_client = PhoenixEnhancedClient()
traces = await phoenix_client.query_workflow_traces("OQTestGenerationWorkflow")
```

### Recommended Libraries and Versions

#### Core Tracing Dependencies

```python
# Enhanced observability stack
arize-phoenix>=5.1.0  # Latest Phoenix observability
openinference-instrumentation-llama-index>=3.0.0  # LlamaIndex tracing
opentelemetry-sdk>=1.12.0  # OpenTelemetry core
opentelemetry-exporter-otlp>=1.12.0  # OTLP export
psutil>=5.9.0  # System monitoring
```

#### Development Environment Setup

```bash
# Install comprehensive tracing stack
uv add arize-phoenix>=5.1.0 openinference-instrumentation-llama-index>=3.0.0
uv add opentelemetry-sdk>=1.12.0 opentelemetry-exporter-otlp>=1.12.0
uv add psutil>=5.9.0  # For resource monitoring
```

This comprehensive research provides all the necessary patterns and code examples to add robust traceability to the OQ agent and debug the "works once then fails" reliability issue. The implementation focuses on practical, pharmaceutical-compliant solutions that provide detailed visibility into workflow execution, batch processing, and resource management.