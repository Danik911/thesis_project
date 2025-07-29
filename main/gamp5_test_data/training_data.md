# GAMP-5 Categorization - Training Data

This file contains a set of User Requirements Specifications (URS) to be used for **training** the GAMP-5 categorization agent.

---

## URS-T01: Environmental Monitoring System (EMS)
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

## URS-T02: Laboratory Information Management System (LIMS)
**Target Category**: 4 (Clear)
**System Type**: Sample Management and Testing Platform

### 1. Introduction
This URS defines requirements for a LIMS to manage QC laboratory operations, including sample registration, test execution, and result reporting.

### 2. Functional Requirements
- **URS-LIMS-001**: System shall be based on commercial LIMS package (LabWare/STARLIMS).
- **URS-LIMS-002**: Configure workflows for raw material, in-process, and finished product testing.
- **URS-LIMS-003**: System shall integrate with existing SAP ERP using vendor's standard adapter.
- **URS-LIMS-004**: Configure sample login screens to capture site-specific attributes.
- **URS-LIMS-005**: Configure stability study protocols using vendor's configuration tools.
- **URS-LIMS-006**: Implement custom business rules for OOS investigations using vendor's scripting language.
- **URS-LIMS-007**: Configure electronic worksheets for 15 different analytical methods.
- **URS-LIMS-008**: System shall use vendor's standard reporting engine with configured templates.

### 3. Regulatory Requirements
- **URS-LIMS-009**: Configure user roles: Analyst, Reviewer, QA Approver.
- **URS-LIMS-010**: Implement two-stage electronic review using configuration options.
- **URS-LIMS-011**: Configure audit trail categories per site SOPs.

---

## URS-T03: Standalone Temperature Data Logger
**Target Category**: 3 (Clear)
**System Type**: Portable Data Logger

### 1. Introduction
This document specifies the requirements for a standalone, battery-powered data logger for monitoring temperature during transportation of clinical trial materials.

### 2. Functional Requirements
- **URS-DL-001**: The device shall be a commercial off-the-shelf (COTS) data logger.
- **URS-DL-002**: The logger must operate without any connection to a network during its logging mission.
- **URS-DL-003**: The device shall be configured once before shipment using the vendor's standard software. No changes to configuration are permitted during use.
- **URS-DL-004**: The device shall have a single button to start and stop logging.
- **URS-DL-005**: Data shall be extracted after use via a USB connection to a PC running the vendor's standard data extraction software.
- **URS-DL-006**: The extraction software shall generate a non-editable PDF report.

### 3. Regulatory Requirements
- **URS-DL-007**: The vendor software used for configuration and reporting must be 21 CFR Part 11 compliant for audit trails.
- **URS-DL-008**: The PDF report must meet ALCOA+ principles for data integrity.

---

## URS-T04: Building Management System (BMS)
**Target Category**: 4 (Clear)
**System Type**: Facility Monitoring and Control

### 1. Introduction
This URS outlines the requirements for a Building Management System (BMS) to monitor and control GMP-critical environmental parameters within the manufacturing facility.

### 2. Functional Requirements
- **URS-BMS-001**: The system shall be based on a commercial BMS platform (e.g., Siemens Desigo, Johnson Controls Metasys).
- **URS-BMS-002**: Configure alarm limits and notifications for all GMP-relevant areas (e.g., cleanrooms, warehouses).
- **URS-BMS-003**: Configure user access levels for different roles (e.g., Operator, Engineer, QA) using standard system features.
- **URS-BMS-004**: The system shall be configured to monitor differential pressure, temperature, and humidity in all classified areas.
- **URS-BMS-005**: Configure historical data collection and trend displays for all monitored points.
- **URS-BMS-006**: The system's graphical user interface (GUI) shall be configured to display a map of the facility with live data overlays.

### 3. Regulatory Requirements
- **URS-BMS-007**: The system shall be configured to enforce electronic signatures for changes to critical alarm setpoints.
- **URS-BMS-008**: Configure the system to synchronize its clock with the site's NTP server.
- **URS-BMS-009**: All GMP-relevant actions must be logged in an un-editable audit trail, configured to capture user ID, timestamp, and action details.

---

## URS-T05: Custom AI-based Diagnostic Software
**Target Category**: 5 (Clear)
**System Type**: Software as a Medical Device (SaMD)

### 1. Introduction
This URS defines the requirements for a novel, custom-developed AI software application intended to diagnose retinopathy from retinal scan images.

### 2. Functional Requirements
- **URS-AI-001**: The system shall be developed from the ground up using Python and TensorFlow.
- **URS-AI-002**: A proprietary deep learning model shall be developed to classify images into five stages of disease progression.
- **URS-AI-003**: The system shall include a custom-built user interface for clinicians to upload images and view results.
- **URS-AI-004**: Develop a bespoke algorithm for image pre-processing and quality checking.
- **URS-AI-005**: The system must integrate with the hospital's custom Electronic Health Record (EHR) system via a newly developed API.
- **URS-AI-006**: A custom database schema shall be designed and implemented in PostgreSQL to store image metadata and diagnostic results.

### 3. Regulatory Requirements
- **URS-AI-007**: The system must be developed in compliance with IEC 62304 for medical device software.
- **URS-AI-008**: A custom audit trail module must be developed to log all system activities, including model inferences.
- **URS-AI-009**: The system shall implement a custom-developed security module to ensure HIPAA compliance.
