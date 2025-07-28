"""
Test suite for Phoenix observability integration.

Tests configuration, initialization, and event handling with Phoenix.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, UTC

from main.src.monitoring import (
    PhoenixConfig,
    PhoenixManager,
    setup_phoenix,
    PhoenixEventStreamHandler,
    PharmaceuticalEventHandler
)
from main.src.core.events import (
    GAMPCategorizationEvent,
    ValidationEvent,
    ErrorRecoveryEvent
)
from main.src.shared.config import Config


class TestPhoenixConfig:
    """Test Phoenix configuration management."""
    
    def test_default_configuration(self):
        """Test default Phoenix configuration values."""
        config = PhoenixConfig()
        
        assert config.phoenix_host == "localhost"
        assert config.phoenix_port == 6006
        assert config.service_name == "test_generator"
        assert config.enable_tracing is True
        assert config.enable_local_ui is True
        
    def test_environment_configuration(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("PHOENIX_HOST", "phoenix.example.com")
        monkeypatch.setenv("PHOENIX_PORT", "8080")
        monkeypatch.setenv("PHOENIX_API_KEY", "test-api-key")
        monkeypatch.setenv("DEPLOYMENT_ENVIRONMENT", "production")
        
        config = PhoenixConfig()
        
        assert config.phoenix_host == "phoenix.example.com"
        assert config.phoenix_port == 8080
        assert config.phoenix_api_key == "test-api-key"
        assert config.deployment_environment == "production"
        
    def test_production_defaults(self, monkeypatch):
        """Test production-specific defaults."""
        monkeypatch.setenv("DEPLOYMENT_ENVIRONMENT", "production")
        
        config = PhoenixConfig()
        
        assert config.enable_local_ui is False
        assert config.batch_span_processor_schedule_delay_millis == 1000
        
    def test_otlp_endpoint_construction(self):
        """Test OTLP endpoint default construction."""
        config = PhoenixConfig()
        
        assert config.otlp_endpoint == "http://localhost:6006/v1/traces"
        
    def test_resource_attributes(self):
        """Test conversion to OpenTelemetry resource attributes."""
        config = PhoenixConfig()
        attributes = config.to_resource_attributes()
        
        assert attributes["service.name"] == "test_generator"
        assert attributes["deployment.environment"] == "development"
        assert attributes["compliance.gamp5.enabled"] is True


class TestPhoenixManager:
    """Test Phoenix lifecycle management."""
    
    @patch('main.src.monitoring.phoenix_config.trace')
    def test_setup_initialization(self, mock_trace):
        """Test Phoenix manager initialization."""
        manager = PhoenixManager()
        
        assert manager.config is not None
        assert manager.tracer_provider is None
        assert manager._initialized is False
        
    @patch('main.src.monitoring.phoenix_config.trace')
    @patch('main.src.monitoring.phoenix_config.OTLPSpanExporter')
    def test_setup_with_tracing_enabled(self, mock_exporter, mock_trace):
        """Test setup with tracing enabled."""
        manager = PhoenixManager()
        manager.setup()
        
        assert manager._initialized is True
        mock_trace.set_tracer_provider.assert_called_once()
        
    def test_setup_with_tracing_disabled(self):
        """Test setup with tracing disabled."""
        config = PhoenixConfig(enable_tracing=False)
        manager = PhoenixManager(config)
        manager.setup()
        
        assert manager._initialized is False
        assert manager.tracer_provider is None
        
    @patch('main.src.monitoring.phoenix_config.px')
    @patch('main.src.monitoring.phoenix_config.trace')
    def test_local_phoenix_launch(self, mock_trace, mock_px):
        """Test local Phoenix UI launch."""
        mock_session = MagicMock()
        mock_session.url = "http://localhost:6006"
        mock_px.launch_app.return_value = mock_session
        
        config = PhoenixConfig(enable_local_ui=True, deployment_environment="development")
        manager = PhoenixManager(config)
        manager.setup()
        
        mock_px.launch_app.assert_called_once_with(
            host="localhost",
            port=6006
        )
        assert manager.phoenix_session == mock_session
        
    def test_get_tracer(self):
        """Test getting a tracer instance."""
        manager = PhoenixManager()
        tracer = manager.get_tracer("test_module")
        
        assert tracer is not None


class TestPhoenixEventStreamHandler:
    """Test Phoenix-integrated event stream handler."""
    
    @pytest.mark.asyncio
    async def test_event_processing_with_span(self):
        """Test event processing adds span attributes."""
        handler = PhoenixEventStreamHandler()
        
        # Mock span
        mock_span = Mock()
        mock_span.is_recording.return_value = True
        
        with patch('main.src.monitoring.phoenix_event_handler.trace.get_current_span', return_value=mock_span):
            event_data = {
                "event_type": "GAMPCategorizationEvent",
                "event_id": "test-123",
                "workflow_context": {
                    "step": "categorization",
                    "agent_id": "gamp_agent",
                    "correlation_id": "corr-123"
                },
                "payload": {
                    "category": "GAMP Category 4",
                    "confidence": 0.85,
                    "review_required": False
                }
            }
            
            # Process event (this will call parent's _process_event)
            # We're testing that our override adds attributes
            with patch.object(handler, 'structured_logger') as mock_logger:
                mock_logger.log_event = Mock()
                with patch.object(handler, 'compliance_logger') as mock_compliance:
                    mock_compliance.log_audit_event = Mock()
                    
                    # Call our _process_event directly
                    await handler._process_event(event_data)
            
            # Verify span attributes were set
            mock_span.set_attribute.assert_any_call("event.type", "GAMPCategorizationEvent")
            mock_span.set_attribute.assert_any_call("event.id", "test-123")
            mock_span.set_attribute.assert_any_call("pharmaceutical.workflow.step", "categorization")
            mock_span.set_attribute.assert_any_call("gamp5.category", "GAMP Category 4")
            mock_span.set_attribute.assert_any_call("gamp5.confidence_score", 0.85)


class TestPharmaceuticalEventHandler:
    """Test pharmaceutical-specific event handler."""
    
    @pytest.mark.asyncio
    async def test_gamp_categorization_handling(self):
        """Test GAMP categorization event handling."""
        handler = PharmaceuticalEventHandler()
        
        event = GAMPCategorizationEvent(
            document_name="test_sop.pdf",
            gamp_category="GAMP Category 4",
            confidence_score=0.9,
            categorized_by="test_user",
            review_required=False,
            risk_assessment={
                "level": "Medium",
                "patient_impact": "Indirect",
                "data_integrity": "High"
            },
            correlation_id="test-correlation-123"
        )
        
        # Mock OpenInference and tracer
        with patch('main.src.monitoring.pharmaceutical_event_handler.using_attributes'):
            with patch.object(handler.tracer, 'start_as_current_span') as mock_span:
                mock_span_context = MagicMock()
                mock_span.return_value.__enter__.return_value = mock_span_context
                
                await handler.handle_event(event)
                
                # Verify span was created
                mock_span.assert_called_once_with("gamp_categorization", kind=2)  # INTERNAL
                
                # Verify attributes were set
                mock_span_context.set_attribute.assert_any_call("gamp5.document_name", "test_sop.pdf")
                mock_span_context.set_attribute.assert_any_call("gamp5.category", "GAMP Category 4")
                mock_span_context.set_attribute.assert_any_call("gamp5.confidence_score", 0.9)
                
        assert handler.processed_events == 1
    
    @pytest.mark.asyncio
    async def test_error_recovery_handling(self):
        """Test error recovery event handling."""
        handler = PharmaceuticalEventHandler()
        
        event = ErrorRecoveryEvent(
            error_type="API_FAILURE",
            error_message="Connection timeout",
            recovery_action="Retry with backoff",
            retry_count=2,
            recovery_success=False,
            correlation_id="test-correlation-456"
        )
        
        with patch('main.src.monitoring.pharmaceutical_event_handler.using_attributes'):
            with patch.object(handler.tracer, 'start_as_current_span') as mock_span:
                mock_span_context = MagicMock()
                mock_span.return_value.__enter__.return_value = mock_span_context
                
                await handler.handle_event(event)
                
                # Verify error status was set
                mock_span_context.set_status.assert_called_once()
                
                # Verify error attributes
                mock_span_context.set_attribute.assert_any_call("error.type", "API_FAILURE")
                mock_span_context.set_attribute.assert_any_call("error.recovery_success", False)


def test_setup_phoenix_singleton():
    """Test setup_phoenix returns singleton instance."""
    with patch('main.src.monitoring.phoenix_config.PhoenixManager.setup'):
        manager1 = setup_phoenix()
        manager2 = setup_phoenix()
        
        assert manager1 is manager2