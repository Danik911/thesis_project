# GAMP-5 Categorization - Testing Data

This file contains a set of User Requirements Specifications (URS) to be used for **testing** the GAMP-5 categorization agent. The examples are designed to cover clear and ambiguous cases.

---

## URS-001: Environmental Monitoring System (EMS)
**Target Category**: 3 (Clear)
**System Type**: Continuous Temperature and Humidity Monitoring

### 1. Introduction
This URS defines the requirements for an Environmental Monitoring System to monitor critical storage areas for temperature-sensitive pharmaceutical products.

### 2. Functional Requirements
- **URS-EMS-001**: The system shall continuously monitor temperature in all GMP storage areas.
- **URS-EMS-002**: Temperature readings shall be recorded at intervals not exceeding 5 minutes.
- **URS-EMS-003**: The system shall use vendor-supplied software without modification.
- **URS-EMS-004**: Temperature range: -80°C to +50°C with accuracy of ±0.5°C.
- **URS-EMS-005**: The system shall generate alerts when temperature deviates ±2°C from setpoint.
- **URS-EMS-006**: All data shall be stored in the vendor's standard database format.
- **URS-EMS-007**: Standard reports provided by vendor shall be used for batch release.

### 3. Regulatory Requirements
- **URS-EMS-008**: System shall maintain an audit trail per 21 CFR Part 11.
- **URS-EMS-009**: Electronic signatures shall use vendor's built-in functionality.
- **URS-EMS-010**: Data shall be retained for 7 years using vendor's archival feature.

---

## URS-002: Laboratory Information Management System (LIMS)
**Target Category**: 4 (Clear)
**System Type**: Sample Management and Testing Platform

### 1. Introduction
This URS defines requirements for a LIMS to manage QC laboratory operations, including sample registration, test execution, and result reporting.

### 2. Functional Requirements
- **URS-LIMS-001**: System shall be based on commercial LIMS package (LabWare/STARLIMS).
- **URS-LIMS-002**: Configure workflows for raw material, in-process, and finished product testing.
- **URS-LIMS-003**: System shall integrate with existing SAP ERP using vendor's standard adapter.
- **URS-LIMS-004**: Configure sample login screens to capture site-specific attributes:
  - Batch number (alphanumeric, 10 characters)
  - Manufacturing date
  - Expiry date calculation based on product master data
  - Storage conditions (dropdown selection)
- **URS-LIMS-005**: Configure stability study protocols using vendor's configuration tools.
- **URS-LIMS-006**: Implement custom business rules for OOS investigations using vendor's scripting language.
- **URS-LIMS-007**: Configure electronic worksheets for 15 different analytical methods.
- **URS-LIMS-008**: System shall use vendor's standard reporting engine with configured templates.

### 3. Regulatory Requirements
- **URS-LIMS-009**: Configure user roles: Analyst, Reviewer, QA Approver.
- **URS-LIMS-010**: Implement two-stage electronic review using configuration options.
- **URS-LIMS-011**: Configure audit trail categories per site SOPs.

---

## URS-003: Manufacturing Execution System (MES)
**Target Category**: 5 (Clear)
**System Type**: Custom Batch Record Management System

### 1. Introduction
This URS defines requirements for a custom MES to manage electronic batch records for sterile injectable products.

### 2. Functional Requirements
- **URS-MES-001**: System shall be custom-developed to integrate with proprietary equipment.
- **URS-MES-002**: Custom algorithms required for:
  - Dynamic in-process control limits based on multivariate analysis
  - Real-time batch genealogy tracking across multiple unit operations
  - Proprietary yield optimization calculations
- **URS-MES-003**: Develop custom interfaces for:
  - 12 different equipment types with proprietary protocols
  - Integration with custom warehouse management system
  - Real-time data exchange with proprietary PAT systems
- **URS-MES-004**: Custom workflow engine to handle:
  - Parallel processing paths unique to our manufacturing process
  - Complex exception handling for deviations
  - Site-specific business rules not supported by commercial packages
- **URS-MES-005**: Develop proprietary data structures for:
  - Multi-level bill of materials with conditional components
  - Process parameters with complex interdependencies
- **URS-MES-006**: Custom mobile application for shop floor data entry.
- **URS-MES-007**: Bespoke analytics module for real-time process monitoring.

### 3. Regulatory Requirements
- **URS-MES-008**: Custom audit trail implementation with enhanced metadata.
- **URS-MES-009**: Develop proprietary electronic signature workflow.
- **URS-MES-010**: Custom data integrity checks beyond standard validations.

---

## URS-004: Chromatography Data System (CDS)
**Target Category**: Ambiguous 3/4
**System Type**: Analytical Instrument Control and Data Analysis

### 1. Introduction
This URS defines requirements for a CDS to control HPLC/GC instruments and process chromatographic data.

### 2. Functional Requirements
- **URS-CDS-001**: System based on commercial CDS software (Empower/OpenLab).
- **URS-CDS-002**: Use vendor's standard instrument control for Waters/Agilent equipment.
- **URS-CDS-003**: Minor configuration of acquisition methods within vendor parameters.
- **URS-CDS-004**: Implement custom calculations using vendor's formula editor:
  - Non-standard impurity calculations
  - Proprietary relative response factor adjustments
  - Complex bracketing schemes beyond vendor defaults
- **URS-CDS-005**: Develop custom reports using vendor's report designer.
- **URS-CDS-006**: Configure standard integration parameters for peak detection.
- **URS-CDS-007**: Create custom export routines for LIMS interface.
- **URS-CDS-008**: Implement site-specific naming conventions via configuration.

### 3. Ambiguous Requirements
- **URS-CDS-009**: System shall support "enhanced" system suitability calculations (Note: unclear if vendor's standard SST is sufficient or custom development needed).
- **URS-CDS-010**: Implement "advanced" trending capabilities for method performance.
- **URS-CDS-011**: System shall handle "complex" multi-dimensional chromatography.

---

## URS-005: Clinical Trial Management System (CTMS)
**Target Category**: Ambiguous 4/5
**System Type**: Hybrid Cloud-Based Trial Management Platform

### 1. Introduction
This URS defines requirements for a CTMS to manage global clinical trials with both standard and specialized adaptive trial designs.

### 2. Functional Requirements
- **URS-CTMS-001**: Base system shall use commercial Veeva CTMS platform.
- **URS-CTMS-002**: Standard modules to be configured:
  - Site management
  - Patient enrollment tracking
  - Monitoring visit planning
  - Standard financial management
- **URS-CTMS-003**: Develop custom modules for:
  - Proprietary adaptive trial design algorithms
  - Integration with in-house randomization system
  - Custom safety signal detection beyond platform capabilities
- **URS-CTMS-004**: Configure workflow approvals using platform tools.
- **URS-CTMS-005**: Implement extensive custom APIs for:
  - Real-time data exchange with wearable devices
  - Integration with AI-based image analysis systems
  - Connection to proprietary biomarker databases
- **URS-CTMS-006**: Develop custom dashboards with advanced visualizations not available in base product.
- **URS-CTMS-007**: Create specialized reports combining CTMS data with external real-world evidence.

### 3. Ambiguous Requirements
- **URS-CTMS-008**: System shall support "innovative" trial designs (Note: unclear if configuration or custom development required).
- **URS-CTMS-009**: Implement "sophisticated" risk-based monitoring algorithms.
- **URS-CTMS-010**: System shall provide "enhanced" regulatory compliance tracking beyond standard GCP.
- **URS-CTMS-011**: Enable "advanced" machine learning capabilities for patient recruitment optimization.

### 4. Technical Requirements
- **URS-CTMS-012**: Hybrid deployment with some modules on-premise due to data sovereignty.
- **URS-CTMS-013**: Custom encryption beyond platform standards for certain jurisdictions.
