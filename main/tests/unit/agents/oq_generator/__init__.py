"""
Unit tests for OQ (Operational Qualification) test generation agent.

This package contains comprehensive unit tests for validating the OQ test
generation functionality including:

- Pydantic model validation and schema correctness
- Workflow event-driven orchestration 
- Core test generation logic and LLMTextCompletionProgram integration
- Pharmaceutical compliance validation (GAMP-5, ALCOA+, 21 CFR Part 11)
- Error handling without fallback mechanisms
- Template and configuration validation

Test Structure:
- test_oq_models.py: Tests for Pydantic data models
- test_oq_workflow.py: Tests for workflow integration
- test_oq_generator.py: Tests for core generation logic
- test_oq_templates.py: Tests for GAMP templates and prompts

All tests follow the NO FALLBACKS principle and validate proper error handling
with complete diagnostic information for pharmaceutical compliance.
"""
