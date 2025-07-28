# GAMP-5 Categorization - Validation Data

This file contains a set of User Requirements Specifications (URS) to be used for **validating** the performance of the GAMP-5 categorization agent.

---

## URS-V01: Manufacturing Execution System (MES)
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

## URS-V02: Chromatography Data System (CDS)
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

## URS-V03: Clinical Trial Management System (CTMS)
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

---

## URS-V04: Electronic Document Management System (EDMS)
**Target Category**: 4 (Clear)
**System Type**: Document Control and Management

### 1. Introduction
This URS specifies the requirements for an Electronic Document Management System (EDMS) for managing GxP documents such as SOPs, Batch Records, and Validation Protocols.

### 2. Functional Requirements
- **URS-EDMS-001**: The system shall be a commercial off-the-shelf product (e.g., Veeva Vault, OpenText Documentum).
- **URS-EDMS-002**: Configure document types and subtypes for all GxP document categories.
- **URS-EDMS-003**: Configure lifecycles and workflows for document drafting, review, approval, and periodic review.
- **URS-EDMS-004**: The system shall be configured to integrate with the company's single sign-on (SSO) solution.
- **URS-EDMS-005**: Configure dynamic watermarks to indicate the status of documents (e.g., "Draft", "Effective", "Obsolete").
- **URS-EDMS-006**: Configure the system's standard reporting module to generate metrics on document cycle times.

### 3. Regulatory Requirements
- **URS-EDMS-007**: The system's standard 21 CFR Part 11 compliant electronic signature functionality shall be configured and enabled for all approval steps.
- **URS-EDMS-008**: Configure the system's audit trail to capture all events related to document creation, modification, and deletion.
- **URS-EDMS-009**: User roles and permissions shall be configured to enforce segregation of duties.

---

## URS-V05: PLC-based Autoclave Controller
**Target Category**: 3 (Clear)
**System Type**: Process Control System

### 1. Introduction
This document defines the user requirements for the control system of a new GMP autoclave for sterilization of equipment.

### 2. Functional Requirements
- **URS-AC-001**: The control system shall be based on a standard industrial PLC (e.g., Allen-Bradley CompactLogix, Siemens S7).
- **URS-AC-002**: The PLC will execute the standard, unmodified sterilization cycle logic provided by the autoclave vendor.
- **URS-AC-003**: The system will use the vendor's standard HMI panel, and no screens will be modified.
- **URS-AC-004**: The system shall record critical process parameters (temperature, pressure, time) for each cycle.
- **URS-AC-005**: The system will have no direct network connection to other plant systems. Data will be transferred via a USB stick.

### 3. Regulatory Requirements
- **URS-AC-006**: The vendor must provide documentation demonstrating that their software development lifecycle is robust.
- **URS-AC-007**: The system must have basic user access controls (Operator, Supervisor) as provided by the vendor.
- **URS-AC-008**: The system shall generate a non-editable batch report at the end of each cycle.
