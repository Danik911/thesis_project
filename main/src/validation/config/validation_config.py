#!/usr/bin/env python3
"""
Validation Configuration for Execution Framework

This module provides comprehensive configuration management for the validation
execution framework, including parallel processing settings, metrics configuration,
error recovery parameters, and Phoenix observability integration.

CRITICAL REQUIREMENTS:
- Production-safe default configurations
- Comprehensive validation of all settings
- Environment variable override support
- Integration with existing system configuration
- NO DEFAULT FALLBACK VALUES - explicit configuration required
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import timedelta
import logging


@dataclass
class ParallelProcessingConfig:
    """Configuration for parallel document processing."""
    max_concurrent_documents: int = 3
    api_rate_limit_per_second: int = 10
    resource_monitoring_enabled: bool = True
    cpu_threshold_percent: float = 80.0
    memory_threshold_percent: float = 80.0
    processing_timeout_seconds: int = 300
    semaphore_timeout_seconds: int = 30
    
    def __post_init__(self):
        """Validate parallel processing configuration."""
        if not (1 <= self.max_concurrent_documents <= 10):
            raise ValueError("max_concurrent_documents must be between 1 and 10")
        
        if not (1 <= self.api_rate_limit_per_second <= 100):
            raise ValueError("api_rate_limit_per_second must be between 1 and 100")
        
        if not (10.0 <= self.cpu_threshold_percent <= 95.0):
            raise ValueError("cpu_threshold_percent must be between 10.0 and 95.0")
        
        if not (10.0 <= self.memory_threshold_percent <= 95.0):
            raise ValueError("memory_threshold_percent must be between 10.0 and 95.0")
        
        if self.processing_timeout_seconds <= 0:
            raise ValueError("processing_timeout_seconds must be positive")


@dataclass
class MetricsCollectionConfig:
    """Configuration for metrics collection and analysis."""
    enable_detailed_metrics: bool = True
    enable_phoenix_integration: bool = True
    enable_statistical_analysis: bool = True
    confidence_level: float = 0.95
    significance_level: float = 0.05
    metrics_storage_path: str = "logs/validation/metrics"
    metrics_retention_days: int = 90
    enable_real_time_metrics: bool = True
    metrics_update_interval_seconds: int = 5
    
    # Quality thresholds
    min_accuracy_threshold: float = 0.7
    min_confidence_threshold: float = 0.6
    max_coefficient_variation: float = 0.2
    min_success_rate_threshold: float = 0.8
    min_consistency_threshold: float = 0.8
    
    def __post_init__(self):
        """Validate metrics collection configuration."""
        if not (0.5 <= self.confidence_level <= 0.99):
            raise ValueError("confidence_level must be between 0.5 and 0.99")
        
        if not (0.01 <= self.significance_level <= 0.1):
            raise ValueError("significance_level must be between 0.01 and 0.1")
        
        if not (0.0 <= self.min_accuracy_threshold <= 1.0):
            raise ValueError("min_accuracy_threshold must be between 0.0 and 1.0")
        
        if not (0.0 <= self.min_confidence_threshold <= 1.0):
            raise ValueError("min_confidence_threshold must be between 0.0 and 1.0")
        
        if self.max_coefficient_variation <= 0:
            raise ValueError("max_coefficient_variation must be positive")
        
        if self.metrics_retention_days <= 0:
            raise ValueError("metrics_retention_days must be positive")


@dataclass
class ProgressTrackingConfig:
    """Configuration for progress tracking and monitoring."""
    enable_progress_tracking: bool = True
    enable_real_time_updates: bool = True
    progress_update_interval_seconds: int = 5
    eta_calculation_window: int = 10
    enable_progress_callbacks: bool = True
    progress_storage_path: str = "logs/validation/progress"
    save_progress_to_disk: bool = True
    progress_retention_days: int = 30
    
    # ETA calculation settings
    eta_smoothing_factor: float = 0.3
    eta_minimum_samples: int = 3
    eta_maximum_prediction_hours: int = 24
    
    def __post_init__(self):
        """Validate progress tracking configuration."""
        if self.progress_update_interval_seconds <= 0:
            raise ValueError("progress_update_interval_seconds must be positive")
        
        if not (1 <= self.eta_calculation_window <= 50):
            raise ValueError("eta_calculation_window must be between 1 and 50")
        
        if not (0.0 < self.eta_smoothing_factor <= 1.0):
            raise ValueError("eta_smoothing_factor must be between 0.0 and 1.0")
        
        if self.eta_minimum_samples < 1:
            raise ValueError("eta_minimum_samples must be at least 1")


@dataclass
class ErrorRecoveryConfig:
    """Configuration for error recovery and retry logic."""
    enable_error_recovery: bool = True
    max_retries: int = 3
    base_retry_delay_seconds: float = 1.0
    max_retry_delay_seconds: float = 60.0
    exponential_backoff_multiplier: float = 2.0
    
    # Checkpoint configuration
    enable_checkpoints: bool = True
    checkpoint_interval_documents: int = 5
    checkpoint_storage_path: str = "logs/validation/checkpoints"
    checkpoint_retention_days: int = 7
    
    # Error categorization
    enable_error_categorization: bool = True
    enable_pattern_analysis: bool = True
    error_storage_path: str = "logs/validation/errors"
    error_retention_days: int = 30
    
    # Recovery strategies
    enable_partial_recovery: bool = True
    enable_document_skipping: bool = True
    enable_fold_skipping: bool = True
    max_failed_documents_per_fold: int = 5
    max_failed_folds: int = 2
    
    def __post_init__(self):
        """Validate error recovery configuration."""
        if not (1 <= self.max_retries <= 10):
            raise ValueError("max_retries must be between 1 and 10")
        
        if self.base_retry_delay_seconds <= 0:
            raise ValueError("base_retry_delay_seconds must be positive")
        
        if self.max_retry_delay_seconds <= self.base_retry_delay_seconds:
            raise ValueError("max_retry_delay_seconds must be greater than base_retry_delay_seconds")
        
        if self.exponential_backoff_multiplier <= 1.0:
            raise ValueError("exponential_backoff_multiplier must be greater than 1.0")
        
        if self.checkpoint_interval_documents <= 0:
            raise ValueError("checkpoint_interval_documents must be positive")


@dataclass
class ResultsAggregationConfig:
    """Configuration for results aggregation and reporting."""
    enable_comprehensive_analysis: bool = True
    enable_statistical_tests: bool = True
    enable_trend_analysis: bool = True
    enable_compliance_assessment: bool = True
    
    # Statistical analysis settings
    enable_confidence_intervals: bool = True
    enable_normality_tests: bool = True
    enable_correlation_analysis: bool = True
    bootstrap_samples: int = 1000
    
    # Reporting configuration
    results_storage_path: str = "logs/validation/results"
    reports_storage_path: str = "logs/validation/reports"
    generate_summary_reports: bool = True
    generate_detailed_reports: bool = True
    generate_csv_exports: bool = True
    reports_retention_days: int = 365
    
    # Quality assessment
    enable_quality_scoring: bool = True
    quality_weights: Dict[str, float] = field(default_factory=lambda: {
        "success_rate": 0.4,
        "accuracy": 0.3,
        "consistency": 0.3
    })
    
    def __post_init__(self):
        """Validate results aggregation configuration."""
        if self.bootstrap_samples <= 0:
            raise ValueError("bootstrap_samples must be positive")
        
        if self.reports_retention_days <= 0:
            raise ValueError("reports_retention_days must be positive")
        
        # Validate quality weights
        if abs(sum(self.quality_weights.values()) - 1.0) > 0.01:
            raise ValueError("quality_weights must sum to 1.0")
        
        for weight_name, weight_value in self.quality_weights.items():
            if not (0.0 <= weight_value <= 1.0):
                raise ValueError(f"quality weight '{weight_name}' must be between 0.0 and 1.0")


@dataclass
class PhoenixIntegrationConfig:
    """Configuration for Phoenix observability integration."""
    enable_phoenix_integration: bool = True
    enable_span_recording: bool = True
    enable_metrics_recording: bool = True
    enable_trace_export: bool = True
    
    # Phoenix connection settings
    phoenix_endpoint: Optional[str] = None
    project_name: str = "validation_framework"
    experiment_name: str = "cross_validation_execution"
    service_name: str = "validation_executor"
    
    # Performance settings
    enable_batch_export: bool = True
    batch_export_delay_ms: int = 5000
    max_queue_size: int = 2048
    export_timeout_ms: int = 30000
    
    def __post_init__(self):
        """Validate Phoenix integration configuration."""
        if self.batch_export_delay_ms <= 0:
            raise ValueError("batch_export_delay_ms must be positive")
        
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        
        if self.export_timeout_ms <= 0:
            raise ValueError("export_timeout_ms must be positive")


class ValidationExecutionConfig:
    """
    Comprehensive configuration for the validation execution framework.
    
    This class provides centralized configuration management for all aspects
    of the validation execution framework, with support for environment
    variable overrides and comprehensive validation.
    """
    
    def __init__(self, config_file_path: Optional[str] = None):
        """
        Initialize validation execution configuration.
        
        Args:
            config_file_path: Optional path to configuration file
            
        Raises:
            RuntimeError: If configuration initialization fails
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize sub-configurations with defaults
            self.parallel_processing = ParallelProcessingConfig()
            self.metrics_collection = MetricsCollectionConfig()
            self.progress_tracking = ProgressTrackingConfig()
            self.error_recovery = ErrorRecoveryConfig()
            self.results_aggregation = ResultsAggregationConfig()
            self.phoenix_integration = PhoenixIntegrationConfig()
            
            # General execution settings
            self.execution_id_prefix = "validation"
            self.max_execution_time_hours = 12
            self.enable_comprehensive_logging = True
            self.log_level = "INFO"
            
            # Load configuration from file if provided
            if config_file_path:
                self._load_config_file(config_file_path)
            
            # Apply environment variable overrides
            self._apply_environment_overrides()
            
            # Validate complete configuration
            self._validate_configuration()
            
            # Create required directories
            self._create_required_directories()
            
            self.logger.info("Validation execution configuration initialized successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize validation configuration: {e!s}")
    
    def _load_config_file(self, config_file_path: str) -> None:
        """Load configuration from JSON file."""
        try:
            config_path = Path(config_file_path)
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Update configurations from file
            self._update_from_dict(config_data)
            
            self.logger.info(f"Configuration loaded from: {config_file_path}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration file: {e!s}")
    
    def _update_from_dict(self, config_data: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        # Update parallel processing config
        if "parallel_processing" in config_data:
            pp_config = config_data["parallel_processing"]
            for key, value in pp_config.items():
                if hasattr(self.parallel_processing, key):
                    setattr(self.parallel_processing, key, value)
        
        # Update metrics collection config
        if "metrics_collection" in config_data:
            mc_config = config_data["metrics_collection"]
            for key, value in mc_config.items():
                if hasattr(self.metrics_collection, key):
                    setattr(self.metrics_collection, key, value)
        
        # Update progress tracking config
        if "progress_tracking" in config_data:
            pt_config = config_data["progress_tracking"]
            for key, value in pt_config.items():
                if hasattr(self.progress_tracking, key):
                    setattr(self.progress_tracking, key, value)
        
        # Update error recovery config
        if "error_recovery" in config_data:
            er_config = config_data["error_recovery"]
            for key, value in er_config.items():
                if hasattr(self.error_recovery, key):
                    setattr(self.error_recovery, key, value)
        
        # Update results aggregation config
        if "results_aggregation" in config_data:
            ra_config = config_data["results_aggregation"]
            for key, value in ra_config.items():
                if hasattr(self.results_aggregation, key):
                    setattr(self.results_aggregation, key, value)
        
        # Update Phoenix integration config
        if "phoenix_integration" in config_data:
            pi_config = config_data["phoenix_integration"]
            for key, value in pi_config.items():
                if hasattr(self.phoenix_integration, key):
                    setattr(self.phoenix_integration, key, value)
        
        # Update general settings
        general_keys = ["execution_id_prefix", "max_execution_time_hours", "enable_comprehensive_logging", "log_level"]
        for key in general_keys:
            if key in config_data:
                setattr(self, key, config_data[key])
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Parallel processing overrides
        if os.getenv("VALIDATION_MAX_CONCURRENT_DOCS"):
            self.parallel_processing.max_concurrent_documents = int(os.getenv("VALIDATION_MAX_CONCURRENT_DOCS"))
        
        if os.getenv("VALIDATION_API_RATE_LIMIT"):
            self.parallel_processing.api_rate_limit_per_second = int(os.getenv("VALIDATION_API_RATE_LIMIT"))
        
        if os.getenv("VALIDATION_PROCESSING_TIMEOUT"):
            self.parallel_processing.processing_timeout_seconds = int(os.getenv("VALIDATION_PROCESSING_TIMEOUT"))
        
        # Metrics collection overrides
        if os.getenv("VALIDATION_ENABLE_DETAILED_METRICS"):
            self.metrics_collection.enable_detailed_metrics = os.getenv("VALIDATION_ENABLE_DETAILED_METRICS").lower() == "true"
        
        if os.getenv("VALIDATION_CONFIDENCE_LEVEL"):
            self.metrics_collection.confidence_level = float(os.getenv("VALIDATION_CONFIDENCE_LEVEL"))
        
        # Error recovery overrides
        if os.getenv("VALIDATION_MAX_RETRIES"):
            self.error_recovery.max_retries = int(os.getenv("VALIDATION_MAX_RETRIES"))
        
        if os.getenv("VALIDATION_ENABLE_CHECKPOINTS"):
            self.error_recovery.enable_checkpoints = os.getenv("VALIDATION_ENABLE_CHECKPOINTS").lower() == "true"
        
        # Phoenix integration overrides
        if os.getenv("VALIDATION_PHOENIX_ENDPOINT"):
            self.phoenix_integration.phoenix_endpoint = os.getenv("VALIDATION_PHOENIX_ENDPOINT")
        
        if os.getenv("VALIDATION_ENABLE_PHOENIX"):
            self.phoenix_integration.enable_phoenix_integration = os.getenv("VALIDATION_ENABLE_PHOENIX").lower() == "true"
        
        # General overrides
        if os.getenv("VALIDATION_LOG_LEVEL"):
            self.log_level = os.getenv("VALIDATION_LOG_LEVEL")
        
        if os.getenv("VALIDATION_MAX_EXECUTION_HOURS"):
            self.max_execution_time_hours = int(os.getenv("VALIDATION_MAX_EXECUTION_HOURS"))
    
    def _validate_configuration(self) -> None:
        """Validate the complete configuration."""
        # General validation
        if self.max_execution_time_hours <= 0:
            raise ValueError("max_execution_time_hours must be positive")
        
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("log_level must be a valid logging level")
        
        # Cross-configuration validation
        if (self.error_recovery.max_retries * self.error_recovery.max_retry_delay_seconds > 
            self.parallel_processing.processing_timeout_seconds):
            self.logger.warning(
                "Error recovery retry time may exceed processing timeout - consider adjusting timeouts"
            )
        
        if (self.metrics_collection.metrics_update_interval_seconds > 
            self.progress_tracking.progress_update_interval_seconds * 2):
            self.logger.warning(
                "Metrics update interval is much larger than progress update interval"
            )
    
    def _create_required_directories(self) -> None:
        """Create required directories for the validation framework."""
        directories = [
            self.metrics_collection.metrics_storage_path,
            self.progress_tracking.progress_storage_path,
            self.error_recovery.checkpoint_storage_path,
            self.error_recovery.error_storage_path,
            self.results_aggregation.results_storage_path,
            self.results_aggregation.reports_storage_path,
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.warning(f"Could not create directory {directory}: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            "parallel_processing": {
                "max_concurrent_documents": self.parallel_processing.max_concurrent_documents,
                "api_rate_limit_per_second": self.parallel_processing.api_rate_limit_per_second,
                "resource_monitoring_enabled": self.parallel_processing.resource_monitoring_enabled,
                "cpu_threshold_percent": self.parallel_processing.cpu_threshold_percent,
                "memory_threshold_percent": self.parallel_processing.memory_threshold_percent,
                "processing_timeout_seconds": self.parallel_processing.processing_timeout_seconds
            },
            "metrics_collection": {
                "enable_detailed_metrics": self.metrics_collection.enable_detailed_metrics,
                "enable_phoenix_integration": self.metrics_collection.enable_phoenix_integration,
                "enable_statistical_analysis": self.metrics_collection.enable_statistical_analysis,
                "confidence_level": self.metrics_collection.confidence_level,
                "min_accuracy_threshold": self.metrics_collection.min_accuracy_threshold,
                "min_success_rate_threshold": self.metrics_collection.min_success_rate_threshold
            },
            "progress_tracking": {
                "enable_progress_tracking": self.progress_tracking.enable_progress_tracking,
                "enable_real_time_updates": self.progress_tracking.enable_real_time_updates,
                "progress_update_interval_seconds": self.progress_tracking.progress_update_interval_seconds,
                "eta_calculation_window": self.progress_tracking.eta_calculation_window
            },
            "error_recovery": {
                "enable_error_recovery": self.error_recovery.enable_error_recovery,
                "max_retries": self.error_recovery.max_retries,
                "base_retry_delay_seconds": self.error_recovery.base_retry_delay_seconds,
                "enable_checkpoints": self.error_recovery.enable_checkpoints,
                "enable_partial_recovery": self.error_recovery.enable_partial_recovery
            },
            "results_aggregation": {
                "enable_comprehensive_analysis": self.results_aggregation.enable_comprehensive_analysis,
                "enable_statistical_tests": self.results_aggregation.enable_statistical_tests,
                "enable_trend_analysis": self.results_aggregation.enable_trend_analysis,
                "generate_summary_reports": self.results_aggregation.generate_summary_reports
            },
            "phoenix_integration": {
                "enable_phoenix_integration": self.phoenix_integration.enable_phoenix_integration,
                "project_name": self.phoenix_integration.project_name,
                "experiment_name": self.phoenix_integration.experiment_name,
                "phoenix_endpoint": self.phoenix_integration.phoenix_endpoint
            },
            "general": {
                "execution_id_prefix": self.execution_id_prefix,
                "max_execution_time_hours": self.max_execution_time_hours,
                "enable_comprehensive_logging": self.enable_comprehensive_logging,
                "log_level": self.log_level
            }
        }
    
    def save_to_file(self, file_path: str) -> None:
        """
        Save configuration to JSON file.
        
        Args:
            file_path: Path to save configuration file
            
        Raises:
            RuntimeError: If saving fails
        """
        try:
            config_dict = self.to_dict()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to: {file_path}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration: {e!s}")
    
    def validate_runtime_environment(self) -> List[str]:
        """
        Validate runtime environment for the configuration.
        
        Returns:
            List of validation issues (empty if all good)
        """
        issues = []
        
        # Check required directories
        directories_to_check = [
            self.metrics_collection.metrics_storage_path,
            self.progress_tracking.progress_storage_path,
            self.error_recovery.checkpoint_storage_path,
            self.results_aggregation.results_storage_path
        ]
        
        for directory in directories_to_check:
            if not Path(directory).exists():
                issues.append(f"Required directory does not exist: {directory}")
            elif not os.access(directory, os.W_OK):
                issues.append(f"No write permission for directory: {directory}")
        
        # Check Phoenix integration if enabled
        if self.phoenix_integration.enable_phoenix_integration:
            if not self.phoenix_integration.phoenix_endpoint:
                issues.append("Phoenix integration enabled but no endpoint specified")
        
        # Check resource thresholds
        if (self.parallel_processing.cpu_threshold_percent > 90 or 
            self.parallel_processing.memory_threshold_percent > 90):
            issues.append("Resource thresholds are very high - may cause system instability")
        
        # Check timeout configurations
        if (self.error_recovery.max_retry_delay_seconds * self.error_recovery.max_retries > 
            self.parallel_processing.processing_timeout_seconds):
            issues.append("Retry timeout configuration may exceed processing timeout")
        
        return issues
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary for logging/debugging.
        
        Returns:
            Dictionary with configuration summary
        """
        return {
            "parallel_processing": {
                "max_concurrent_documents": self.parallel_processing.max_concurrent_documents,
                "resource_monitoring": self.parallel_processing.resource_monitoring_enabled,
                "processing_timeout": self.parallel_processing.processing_timeout_seconds
            },
            "metrics_collection": {
                "detailed_metrics": self.metrics_collection.enable_detailed_metrics,
                "phoenix_integration": self.metrics_collection.enable_phoenix_integration,
                "statistical_analysis": self.metrics_collection.enable_statistical_analysis
            },
            "error_recovery": {
                "enabled": self.error_recovery.enable_error_recovery,
                "max_retries": self.error_recovery.max_retries,
                "checkpoints": self.error_recovery.enable_checkpoints
            },
            "general": {
                "max_execution_hours": self.max_execution_time_hours,
                "log_level": self.log_level,
                "comprehensive_logging": self.enable_comprehensive_logging
            }
        }