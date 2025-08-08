# Debug Plan: OSS Migration Critical Fixes

## Root Cause Analysis

### 1. JSON Parsing Failures (Priority: HIGH)
**Root Cause**: OSS model (openai/gpt-oss-120b) produces mixed text/markdown responses instead of pure JSON
- **Current Status**: Extensive JSON extraction logic already implemented in both OQ generator and SME agent
- **Issue**: OSS model doesn't reliably follow structured output format despite enhanced prompting
- **Solution**: Implement alternative structured formats (YAML, XML) with fallback parsing strategies

### 2. SME Agent Timeout (Priority: HIGH) 
**Root Cause**: OpenRouter API timeout (120s) is less than SME agent timeout (180s)
- **Current Status**: OpenRouter hardcoded to 120s, SME agent expects 180s
- **Issue**: API timeout occurs before agent timeout, causing failure instead of graceful handling
- **Solution**: Make timeouts configurable and increase OpenRouter timeout limits

### 3. Missing LLM Spans (Priority: MEDIUM)
**Root Cause**: Phoenix tracer initialization or OpenTelemetry configuration issue
- **Current Status**: Comprehensive instrumentation exists in OpenRouterCompatLLM 
- **Issue**: Despite proper span creation code, spans not reaching Phoenix
- **Solution**: Fix Phoenix tracer initialization and OpenTelemetry integration

## Solution Steps

### Step 1: Alternative Format Implementation

#### 1.1 Add YAML Support to OQ Generator
```python
# File: main/src/agents/oq_generator/yaml_parser.py
import yaml
import json
from typing import Any, Dict
from .models import OQTestSuite

def extract_yaml_from_response(response_text: str) -> Dict[str, Any]:
    """Extract YAML from mixed response with fallback strategies."""
    
    # Strategy 1: Extract from YAML code blocks
    yaml_patterns = [
        r'```yaml\s*\n(.*?)\n```',
        r'```yml\s*\n(.*?)\n```', 
        r'```\s*\n(.*?)\n```'  # Generic code blocks
    ]
    
    for pattern in yaml_patterns:
        matches = re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if matches:
            try:
                return yaml.safe_load(matches[0].strip())
            except yaml.YAMLError:
                continue
    
    # Strategy 2: Try parsing entire response as YAML
    try:
        return yaml.safe_load(response_text.strip())
    except yaml.YAMLError:
        pass
    
    # Strategy 3: Convert to structured text format
    return extract_structured_text_format(response_text)

def extract_structured_text_format(response_text: str) -> Dict[str, Any]:
    """Extract structured data from plain text format."""
    result = {}
    
    # Extract suite_id pattern
    if match := re.search(r'Suite ID:\s*(.+)', response_text, re.IGNORECASE):
        result['suite_id'] = match.group(1).strip()
    
    # Extract test cases from numbered lists
    test_cases = []
    test_pattern = r'Test Case (\d+):\s*(.+?)(?=Test Case \d+:|$)'
    for match in re.finditer(test_pattern, response_text, re.DOTALL | re.IGNORECASE):
        test_num = match.group(1)
        test_content = match.group(2).strip()
        
        # Extract test details from content
        test_case = extract_test_case_from_text(test_num, test_content)
        if test_case:
            test_cases.append(test_case)
    
    result['test_cases'] = test_cases
    result['total_test_count'] = len(test_cases)
    
    return result
```

#### 1.2 Update OQ Generator with Alternative Formats
```python
# File: main/src/agents/oq_generator/generator.py
# Add to imports:
from .yaml_parser import extract_yaml_from_response
import yaml

# Update _generate_with_structured_output method (around line 528):
except Exception as e:
    # Standard approach failed - try alternative formats
    self.logger.warning(f"Standard structured output failed: {e}, attempting alternative formats")
    
    # Get raw LLM response for alternative parsing
    raw_response = self._get_raw_llm_response(
        gamp_category=gamp_category,
        urs_content=urs_content,
        document_name=document_name,
        test_count=test_count,
        context_summary=context_summary
    )
    
    # Strategy 1: Try YAML extraction
    try:
        yaml_data = extract_yaml_from_response(raw_response)
        result = OQTestSuite(**yaml_data)
        self.logger.info("OQ generation successful with YAML extraction")
        return result
    except Exception as yaml_e:
        self.logger.warning(f"YAML extraction failed: {yaml_e}")
    
    # Strategy 2: Try JSON extraction (existing)
    try:
        json_string, diagnostic_context = extract_json_from_mixed_response(raw_response)
        json_data = json.loads(json_string)
        result = OQTestSuite(**json_data)
        self.logger.info("OQ generation successful with JSON extraction fallback")
        return result
    except Exception as json_e:
        self.logger.warning(f"JSON extraction failed: {json_e}")
    
    # Strategy 3: Template-based extraction as final fallback
    try:
        template_data = self._extract_template_based_data(raw_response, gamp_category, test_count)
        result = OQTestSuite(**template_data)
        self.logger.info("OQ generation successful with template-based extraction")
        return result
    except Exception as template_e:
        # Final failure - provide comprehensive diagnostic information
        raise TestGenerationFailure(
            f"All parsing strategies failed: JSON({json_e}), YAML({yaml_e}), Template({template_e})",
            {
                "original_error": str(e),
                "raw_response_preview": raw_response[:500],
                "parsing_attempts": ["json", "yaml", "template"],
                "no_fallback_available": True,
                "requires_human_intervention": True
            }
        )
```

### Step 2: Configurable Timeout Implementation

#### 2.1 Add Environment Variable Configuration
```python
# File: main/src/config/timeout_config.py
import os
from typing import Dict, Any

class TimeoutConfig:
    """Centralized timeout configuration for all agents and services."""
    
    # Default timeouts (in seconds)
    DEFAULT_TIMEOUTS = {
        "openrouter_api": 300,      # Increased from 120s to 5 minutes
        "sme_agent": 360,           # 6 minutes (buffer over API timeout)
        "oq_generator": 480,        # 8 minutes for complex generation
        "context_provider": 120,    # 2 minutes
        "research_agent": 180,      # 3 minutes
        "unified_workflow": 1800,   # 30 minutes total
    }
    
    @classmethod
    def get_timeout(cls, service: str) -> int:
        """Get timeout for specific service with environment override."""
        env_key = f"{service.upper()}_TIMEOUT"
        return int(os.getenv(env_key, cls.DEFAULT_TIMEOUTS.get(service, 300)))
    
    @classmethod
    def get_all_timeouts(cls) -> Dict[str, int]:
        """Get all configured timeouts."""
        return {
            service: cls.get_timeout(service) 
            for service in cls.DEFAULT_TIMEOUTS.keys()
        }
    
    @classmethod
    def validate_timeouts(cls) -> Dict[str, Any]:
        """Validate timeout configuration for consistency."""
        timeouts = cls.get_all_timeouts()
        issues = []
        
        # API timeout should be less than agent timeout
        if timeouts["openrouter_api"] >= timeouts["sme_agent"]:
            issues.append("OpenRouter API timeout should be less than SME agent timeout")
        
        if timeouts["openrouter_api"] >= timeouts["oq_generator"]:
            issues.append("OpenRouter API timeout should be less than OQ generator timeout")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "timeouts": timeouts
        }
```

#### 2.2 Update OpenRouter Compatibility Layer
```python
# File: main/src/llms/openrouter_compat.py
# Update imports:
from src.config.timeout_config import TimeoutConfig

# Update _make_openrouter_request method (around line 172):
def _make_openrouter_request(self, messages: list[dict], stream: bool = False) -> dict:
    """Make API request to OpenRouter with configurable timeout."""
    
    headers = {
        "Authorization": f"Bearer {self._openrouter_api_key}",
        "Content-Type": "application/json", 
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "GAMP-5 Pharmaceutical Test Generation"
    }
    
    data = {
        "model": self.model,
        "messages": messages,
        "temperature": self.temperature,
        "max_tokens": self.max_tokens,
        "stream": stream
    }
    
    # Get configurable timeout
    api_timeout = TimeoutConfig.get_timeout("openrouter_api")
    
    try:
        response = requests.post(
            f"{self._openrouter_api_base}/chat/completions",
            headers=headers,
            json=data,
            timeout=api_timeout  # Now configurable
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as e:
        raise RuntimeError(
            f"OpenRouter API request timed out after {api_timeout} seconds. "
            f"Configure with OPENROUTER_API_TIMEOUT environment variable. "
            f"NO FALLBACK ALLOWED - Human consultation required."
        ) from e
```

#### 2.3 Update SME Agent Timeout Handling
```python
# File: main/src/agents/parallel/sme_agent.py
# Update imports:
from src.config.timeout_config import TimeoutConfig

# Update SMEAgentRequest model (around line 305):
class SMEAgentRequest(BaseModel):
    """Request model for SME Agent."""
    specialty: str
    test_focus: str
    compliance_level: str
    domain_knowledge: list[str] = Field(default_factory=list)
    validation_focus: list[str] = Field(default_factory=list)
    risk_factors: dict[str, Any] = Field(default_factory=dict)
    categorization_context: dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID
    timeout_seconds: int = Field(default_factory=lambda: TimeoutConfig.get_timeout("sme_agent"))
```

### Step 3: Phoenix Instrumentation Fix

#### 3.1 Enhanced Phoenix Tracer Initialization
```python
# File: main/src/monitoring/phoenix_setup.py
import os
import logging
from typing import Optional
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

def setup_phoenix_tracing(
    phoenix_endpoint: Optional[str] = None,
    service_name: str = "pharmaceutical_multi_agent_system"
) -> bool:
    """Setup Phoenix tracing with proper OpenTelemetry configuration."""
    
    try:
        # Get Phoenix endpoint
        endpoint = phoenix_endpoint or os.getenv("PHOENIX_ENDPOINT", "http://localhost:6006")
        
        # Create resource with service information
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development")
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        
        # Configure OTLP exporter for Phoenix
        otlp_exporter = OTLPSpanExporter(
            endpoint=f"{endpoint}/v1/traces",
            headers={
                "Content-Type": "application/json",
            }
        )
        
        # Add batch span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Test connection with a simple span
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span("phoenix_setup_test") as span:
            span.set_attribute("setup.status", "successful")
            span.set_attribute("phoenix.endpoint", endpoint)
        
        logger.info(f"✅ Phoenix tracing initialized successfully: {endpoint}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Phoenix tracing setup failed: {e}")
        return False

def verify_phoenix_connection() -> bool:
    """Verify Phoenix is receiving spans."""
    try:
        tracer = trace.get_tracer("phoenix_verification")
        
        with tracer.start_as_current_span("connection_verification") as span:
            span.set_attribute("verification.timestamp", str(datetime.now()))
            span.set_attribute("verification.test", "connectivity") 
            span.set_status(trace.Status(trace.StatusCode.OK))
        
        logger.info("✅ Phoenix connection verification span sent")
        return True
        
    except Exception as e:
        logger.error(f"❌ Phoenix connection verification failed: {e}")
        return False
```

#### 3.2 Update LLM Config with Phoenix Integration
```python
# File: main/src/config/llm_config.py
# Add imports:
from src.monitoring.phoenix_setup import setup_phoenix_tracing, verify_phoenix_connection

# Update get_llm method (around line 85):
# Get the global callback manager from LlamaIndex Settings
# This ensures Phoenix instrumentation is passed to the LLM
callback_manager = Settings.callback_manager if hasattr(Settings, 'callback_manager') else None

# Initialize Phoenix tracing if not already done
if not hasattr(cls, '_phoenix_initialized'):
    phoenix_success = setup_phoenix_tracing()
    if phoenix_success:
        verify_phoenix_connection()
    cls._phoenix_initialized = True

# Ensure Phoenix handler is registered if available
if callback_manager and hasattr(callback_manager, 'handlers'):
    # Check if handlers list is empty
    if len(callback_manager.handlers) == 0:
        try:
            # Import Phoenix callback handler
            from phoenix.trace.llama_index import LlamaIndexInstrumentor
            
            # Initialize Phoenix instrumentor
            LlamaIndexInstrumentor().instrument()
            
            logger.info("✅ Phoenix LlamaIndex instrumentation enabled")
            
        except ImportError:
            logger.warning("Phoenix instrumentation not available")
```

### Step 4: Testing and Validation

#### 4.1 Create Comprehensive Test Suite
```python
# File: main/test_oss_migration_fixes.py
#!/usr/bin/env python3
"""Comprehensive test suite for OSS migration fixes."""

import asyncio
import logging
import os
from pathlib import Path
import yaml
import json

from src.config.timeout_config import TimeoutConfig
from src.config.llm_config import LLMConfig
from src.agents.oq_generator.generator import OQTestGenerator
from src.agents.parallel.sme_agent import create_sme_agent
from src.monitoring.phoenix_setup import setup_phoenix_tracing, verify_phoenix_connection

async def test_timeout_configuration():
    """Test timeout configuration and validation."""
    logger.info("=== Testing Timeout Configuration ===")
    
    # Test timeout retrieval
    timeouts = TimeoutConfig.get_all_timeouts()
    logger.info(f"Configured timeouts: {timeouts}")
    
    # Test timeout validation
    validation = TimeoutConfig.validate_timeouts()
    logger.info(f"Timeout validation: {validation}")
    
    if not validation["valid"]:
        logger.warning(f"Timeout validation issues: {validation['issues']}")
    
    return validation["valid"]

async def test_alternative_formats():
    """Test YAML and alternative format parsing."""
    logger.info("=== Testing Alternative Format Parsing ===")
    
    # Test YAML response parsing
    yaml_response = """
Here's your test suite:

```yaml
suite_id: "TEST-SUITE-001"
gamp_category: "5"
total_test_count: 3
test_cases:
  - test_id: "OQ-001"
    test_description: "System startup validation"
    test_category: "functional"
  - test_id: "OQ-002" 
    test_description: "User interface validation"
    test_category: "usability"
  - test_id: "OQ-003"
    test_description: "Data integrity validation"
    test_category: "data_integrity"
```

This meets your requirements.
    """
    
    try:
        from src.agents.oq_generator.yaml_parser import extract_yaml_from_response
        result = extract_yaml_from_response(yaml_response)
        logger.info(f"✅ YAML parsing successful: {len(result.get('test_cases', []))} test cases")
        return True
    except Exception as e:
        logger.error(f"❌ YAML parsing failed: {e}")
        return False

async def test_phoenix_integration():
    """Test Phoenix tracing integration."""
    logger.info("=== Testing Phoenix Integration ===")
    
    # Setup Phoenix
    phoenix_ok = setup_phoenix_tracing()
    if not phoenix_ok:
        logger.error("❌ Phoenix setup failed")
        return False
    
    # Verify connection
    connection_ok = verify_phoenix_connection()
    if not connection_ok:
        logger.error("❌ Phoenix connection verification failed")
        return False
    
    # Test LLM span creation
    try:
        llm = LLMConfig.get_llm()
        response = await llm.acomplete("Test prompt for span creation")
        logger.info(f"✅ LLM call successful, response length: {len(response.text)}")
        return True
    except Exception as e:
        logger.error(f"❌ LLM span test failed: {e}")
        return False

async def main():
    """Run comprehensive test suite."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Starting OSS Migration Fixes Test Suite")
    
    results = {}
    
    # Test timeout configuration
    results["timeouts"] = await test_timeout_configuration()
    
    # Test alternative formats
    results["formats"] = await test_alternative_formats()
    
    # Test Phoenix integration
    results["phoenix"] = await test_phoenix_integration()
    
    # Summary
    success_count = sum(results.values())
    total_count = len(results)
    
    logger.info(f"Test Results: {success_count}/{total_count} passed")
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"  {test}: {status}")
    
    if success_count == total_count:
        logger.info("🎉 All tests passed - OSS migration fixes working!")
    else:
        logger.error("❌ Some tests failed - review issues above")

if __name__ == "__main__":
    asyncio.run(main())
```

## Risk Assessment

### High Risk Changes
- **OpenRouter timeout increase**: Could cause longer waits before failure detection
  - **Mitigation**: Make timeout configurable with reasonable defaults
  - **Rollback**: Revert to 120s timeout if issues arise

### Medium Risk Changes  
- **Alternative format parsing**: New parsing logic could introduce bugs
  - **Mitigation**: Implement as fallback after existing JSON parsing
  - **Rollback**: Disable alternative parsing, rely only on JSON extraction

### Low Risk Changes
- **Phoenix instrumentation**: Observability improvements shouldn't affect functionality
  - **Mitigation**: Graceful degradation if Phoenix unavailable
  - **Rollback**: Disable Phoenix tracing completely

## Compliance Validation

### GAMP-5 Implications
- **Structured Output Reliability**: Alternative formats improve system reliability without compromising compliance
- **Audit Trail**: Enhanced logging and monitoring improve audit capabilities
- **Error Handling**: Explicit failure modes maintain pharmaceutical compliance requirements

### Regulatory Considerations
- **Data Integrity**: Alternative formats maintain same validation requirements as JSON
- **Change Control**: All changes documented and tested systematically
- **Risk Management**: Comprehensive risk assessment and mitigation strategies

## Implementation Timeline

### Phase 1: Timeout Configuration (Day 1)
1. Implement TimeoutConfig class
2. Update OpenRouter compatibility layer
3. Update SME agent timeout handling  
4. Test timeout validation

### Phase 2: Alternative Format Support (Day 2-3)
1. Implement YAML parser module
2. Update OQ generator with fallback strategies
3. Add template-based extraction
4. Test alternative format parsing

### Phase 3: Phoenix Integration (Day 4)
1. Implement enhanced Phoenix setup
2. Update LLM config with tracing
3. Verify span creation and transmission
4. Test observability functionality

### Phase 4: Integration Testing (Day 5)
1. Run comprehensive test suite
2. Validate end-to-end functionality
3. Performance testing with new timeouts
4. Documentation updates

## Success Criteria

- [ ] SME agent operations complete without timeout errors
- [ ] OQ generator successfully produces structured outputs using alternative formats  
- [ ] Phoenix captures and displays LLM operation spans
- [ ] System maintains GAMP-5 compliance requirements
- [ ] No regression in existing functionality
- [ ] Comprehensive test coverage for new features

## Rollback Plan

### Emergency Rollback
1. Revert OpenRouter timeout to 120s
2. Disable alternative format parsing
3. Remove Phoenix instrumentation changes
4. Return to original configuration

### Partial Rollback Options
- **Timeout Only**: Keep alternative formats, revert timeouts
- **Formats Only**: Keep timeout changes, disable alternative parsing
- **Phoenix Only**: Keep functional changes, disable observability

## Next Steps

1. **Immediate**: Implement timeout configuration changes
2. **Short-term**: Add YAML/XML parsing support with comprehensive testing
3. **Medium-term**: Enhance Phoenix integration and monitoring
4. **Long-term**: Consider additional structured output formats and optimization