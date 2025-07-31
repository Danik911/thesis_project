# Realistic OQ Test Scripts for Pharmaceutical Computerized Systems Validation

Operational Qualification (OQ) test scripts form the backbone of pharmaceutical computerized systems validation, ensuring software performs according to specifications while maintaining regulatory compliance. This comprehensive guide presents 15 realistic test script examples across GAMP categories 3, 4, and 5, demonstrating various test formats and complexity levels appropriate to each system type.

## Understanding GAMP categories and their validation requirements

The GAMP framework categorizes computerized systems based on complexity and customization level, directly influencing validation approaches. **Category 3 systems** represent non-configured commercial software used "as-is," requiring minimal validation focused on installation and basic functionality. **Category 4 systems** involve configured commercial packages customized through standard tools, demanding validation of configured elements while leveraging supplier testing for core functions. **Category 5 systems** encompass custom-developed software requiring the most rigorous validation, including code review and comprehensive testing of all functions.

Risk assessment drives the validation intensity for each category. Category 3 systems typically pose lower risk due to widespread use and vendor validation, while Category 5 systems carry highest risk due to unique code and lack of usage history. This risk-based approach, endorsed by FDA's Computer Software Assurance guidance and GAMP 5 Second Edition, ensures validation efforts align with potential impact on patient safety and product quality.

## GAMP Category 3: Non-configured systems test scripts

Category 3 systems demonstrate standardized functionality across implementations, allowing streamlined validation approaches that focus on proper installation and intended use verification.

### Environmental Monitoring System - Robust Scripted Format

**System**: Vaisala viewLinc Continuous Monitoring Software  
**Risk Level**: Medium (GxP environment monitoring)

The following test script exemplifies detailed step-by-step validation for alarm generation functionality:

```
Test Script OQ-001: Alarm Generation and Notification
Traceability: URS-003 "System must notify personnel when readings exceed limits"

Prerequisites:
- System installed per IQ protocol
- Test sensor configured with alarm thresholds
- Email server connectivity verified

Test Steps:
1. Navigate to sensor configuration screen
   Action: Log in with validated credentials
   Expected: Dashboard displays within 30 seconds
   Actual: _____________
   Pass/Fail: ___

2. Configure alarm thresholds
   Action: Set high alarm 5°C above current reading
   Expected: Threshold saved with confirmation message
   Actual: _____________
   Pass/Fail: ___

3. Simulate alarm condition
   Action: Introduce controlled temperature change
   Expected: Visual alarm within 2 minutes
   Actual: _____________
   Pass/Fail: ___

4. Verify email notification
   Action: Check designated email account
   Expected: Email contains sensor ID, values, timestamp
   Actual: _____________
   Pass/Fail: ___

21 CFR Part 11: Electronic signature required for completion
```

### HPLC Data System - Limited Scripted Format

This approach balances documentation requirements with testing efficiency for analytical systems:

```
Test Script OQ-002: System Suitability and Data Integrity
System: Standard chromatography data acquisition software

Test Overview:
Verify system performs within analytical parameters while maintaining data integrity

High-Level Execution:
□ Equilibrate system with test method
□ Inject system suitability standard 6 times
□ Calculate: retention time, peak area, resolution, tailing
□ Verify audit trail completeness
□ Confirm data tamper-evidence

Acceptance Criteria:
- Peak resolution ≥2.0
- Tailing factor ≤2.0
- %RSD replicate injections ≤2.0%
- Complete audit trail for all actions
```

### Laboratory Balance Software - Unscripted/Exploratory Format

Exploratory testing suits user-focused validation of standard laboratory equipment:

```
Test Script OQ-003: Weighing Function Validation
System: Analytical balance with data logging

Exploratory Scope:
Test all user-accessible weighing and data management functions

Key Areas:
1. Basic weighing operations (zero/tare, units, repeatability)
2. Data management (logging, export, retrieval)
3. Error handling (overload, environmental, power loss)

Success Criteria:
- Functions match user manual descriptions
- Accuracy ±0.0001g for 1mg-100g range
- Complete transaction logging
- Graceful error recovery

Documentation: Maintain detailed test log with screenshots
```

### Statistical Software - Ad Hoc Format

Ad hoc testing efficiently validates calculation accuracy using reference datasets:

```
Test Script OQ-004: Statistical Calculations
System: Standard statistical package (Minitab/JMP)

Test Approach:
Use NIST reference datasets to verify calculation accuracy

Sample Tests:
- Basic statistics against certified values
- Linear regression with known parameters
- Process capability calculations

Expected Results:
All values match references within software precision (6-8 digits)

Documentation: Comparison table of calculated vs. reference values
```

### Data Acquisition System - Hybrid Format

This hybrid approach combines scripted accuracy testing with exploratory functionality validation:

```
Test Script OQ-005: Data Acquisition Functions

Part A - Scripted Testing:
1. Data Accuracy Test
   - Connect calibrated sensors
   - Record 1 hour at 1 sample/minute
   - Compare to reference values
   - Accept: ±0.5% accuracy

2. Power Loss Recovery
   - Start logging, interrupt power
   - Verify data recovery
   - Accept: No data loss

Part B - Exploratory Testing:
- Various sampling rates
- Multiple sensor inputs
- Export formats
- Alarm functionality
```

## GAMP Category 4: Configured systems test scripts

Category 4 systems require focused validation on configured elements while leveraging vendor testing for standard functionality.

### LIMS Sample Management - Robust Scripted Format

**System**: LabWare LIMS configured for pharmaceutical QC

This comprehensive test script validates critical sample chain of custody functions:

```
Test Script LIMS-OQ-001: Sample Reception and Login
Objective: Verify sample registration and chain of custody

Prerequisites:
- LIMS operational in test environment
- User roles configured per specification
- Barcode scanners connected

Detailed Steps:
1. Login with QC Analyst credentials
   Expected: Role-based dashboard displays
   Pass/Fail: ___

2. Navigate to Sample Reception
   Expected: Module loads with correct fields
   Pass/Fail: ___

3. Scan sample barcode ABC123
   Expected: System recognizes format, auto-populates fields
   Pass/Fail: ___

4. Enter: Client ID=PHARMA01, Type=Raw Material, 
   Collection=07/31/2025 14:30
   Expected: All fields accept valid data
   Pass/Fail: ___

5. Assign storage location FR-01-A3
   Expected: Inventory updates, location reserved
   Pass/Fail: ___

6. Generate Chain of Custody
   Expected: PDF with complete sample details
   Pass/Fail: ___

7. Verify audit trail entry
   Expected: UserID, timestamp, "Sample Logged" action
   Pass/Fail: ___

8. Login as different user, attempt modification
   Expected: System enforces permission restrictions
   Pass/Fail: ___

Overall Pass Criteria: All steps pass, data integrity maintained
```

### MES Batch Record - Robust Scripted Format

Manufacturing Execution Systems demand rigorous validation of electronic batch records:

```
Test Script MES-OQ-005: Electronic Batch Record Execution
System: AVEVA MES configured for tablet production

Prerequisites:
- Master recipe loaded for Product X
- Equipment interfaces operational
- Test materials available

Execution Steps:
1. Create batch from master recipe PROD-X-001
   Expected: Unique batch ID generated
   Verify: _______________

2. Download recipe to Tablet Press TP-01
   Expected: Parameters match master recipe
   Verify: _______________

3. Execute dispensing step
   - Scan material barcode
   - Enter weight 10.05 kg
   - Capture operator signature
   Expected: Material lot tracked, weight in tolerance
   Verify: _______________

4. Record process deviation
   - Document: "Temperature spike to 82°C at 14:35"
   - Enter corrective action taken
   - Obtain supervisor approval
   Expected: Deviation captured with full details
   Verify: _______________

5. Complete batch review
   Expected: All steps show completion status
   Verify: _______________

6. Generate batch report
   Expected: Complete PDF with all manufacturing data
   Verify: _______________

21 CFR Part 11: Verify electronic signatures at each approval point
```

### ERP Quality Module - Ad Hoc Configuration Testing

Configuration-specific validation for customized ERP modules:

```
Test Script QM-OQ-001: Complaint Handling Workflow
System: SAP QM module configured for complaints

Configuration Tests:
□ Complaint categories populate correctly
□ Routing rules direct to appropriate departments
□ CAPA integration triggers on severity ≥3
□ Regulatory reporting flags for serious events
□ Document attachments link properly

Test Method:
- Create test complaints for each category
- Verify workflow routing matches configuration
- Test integration points with CAPA module
- Confirm custom field calculations
- Validate report generation

Acceptance: All configured features function per FRS
```

### Electronic Batch Records - Limited Scripted Format

High-level validation of paperless manufacturing execution:

```
Test Script EBR-OQ-003: Production Batch Execution
System: Tulip EBR platform

Test Objectives:
1. Load and execute complete batch recipe
2. Verify material tracking throughout process
3. Test deviation handling procedures
4. Validate review and approval workflows
5. Generate compliant batch documentation

Key Verification Points:
□ Recipe parameters correctly transferred
□ Material genealogy maintained
□ Electronic signatures captured
□ Audit trail complete
□ Final batch package comprehensive

Method: Execute representative batch with all typical scenarios
```

### Document Management - Unscripted/Exploratory Format

Risk-based exploratory testing for configured DMS:

```
Test Script DMS-OQ-002: Document Lifecycle Testing
System: Configured SharePoint for GxP documents

Exploratory Charter:
Mission: Validate complete document lifecycle functionality
Time box: 4 hours
Resources: Test documents, multiple user accounts

Focus Areas:
- Creation and version control mechanisms
- Review/approval workflow configurations
- Distribution list management
- Access control enforcement
- Archive and retrieval processes

Success Criteria:
- Workflows match configured specifications
- Version control prevents overwrites
- Audit trail captures all actions
- Access restrictions enforced consistently
```

## GAMP Category 5: Custom systems test scripts

Category 5 systems require the most comprehensive validation approach, including code-level testing and extensive functional verification.

### Custom LIMS Security Module - Comprehensive Robust Format

This detailed script demonstrates the rigor required for custom-developed security functions:

```
Test Script OQ-LIMS-001: User Access Control Validation
System: Custom-developed LIMS security module

Objective: Verify authentication, authorization, and audit functions

Test Case 1.1: Authentication Testing
Prerequisites: Test users configured with various permission levels

Negative Testing:
1. Login: validuser/wrongpassword
   Expected: Access denied, "Invalid credentials"
   Actual: _______________
   
2. Login: wronguser/validpassword  
   Expected: Access denied, "Invalid credentials"
   Actual: _______________
   
3. Login: validuser/validpassword (expired)
   Expected: Force password change screen
   Actual: _______________

4. Attempt 3 consecutive failed logins
   Expected: Account locked, admin notification sent
   Actual: _______________

Positive Testing:
5. Login: validuser/validpassword
   Expected: Successful login, dashboard per role
   Actual: _______________

6. Verify session timeout at 30 minutes
   Expected: Automatic logout, return to login screen
   Actual: _______________

Password Complexity:
7. Change password to "simple"
   Expected: Rejected - complexity requirements
   Actual: _______________

8. Change password to "Complex!Pass123"
   Expected: Accepted, confirmation message
   Actual: _______________

Audit Trail:
9. Review security audit log
   Expected: All login attempts recorded with:
   - Username attempted
   - Success/failure status  
   - Timestamp to second
   - Source IP address
   Actual: _______________

Test Case 1.2: Authorization Matrix Testing
[Continues with role-based access verification]

Pass Criteria: 100% of security controls function as designed
```

### Custom Process Control - Algorithm Validation Format

Algorithm testing requires mathematical verification alongside functional testing:

```
Test Script OQ-PCS-001: Temperature Control Algorithm
System: Custom bioreactor control system

Test Objective: Validate PID control algorithm accuracy

Test Setup:
- Process simulator with known response characteristics
- Reference calculations for expected control outputs
- Test scenarios covering full operational range

Algorithm Test Cases:

1. Steady State Control
   Setpoint: 37.0°C
   Initial: 35.0°C
   Expected response time: <5 minutes
   Expected overshoot: <0.5°C
   Expected steady-state error: <0.1°C
   
   Results:
   Rise time: _______
   Overshoot: _______
   Settling time: _______
   SS error: _______

2. Disturbance Rejection
   Introduce: +3°C step disturbance
   Expected recovery: <2 minutes
   Maximum deviation: <1°C
   
   Results:
   Max deviation: _______
   Recovery time: _______

3. Setpoint Tracking
   Change: 37°C → 25°C → 42°C
   Expected: Smooth transitions
   No oscillation
   
   Results: [Graph attached]

4. Boundary Conditions
   Test: 4°C, 45°C (limits)
   Expected: Stable control
   Safety interlocks activate
   
   Results: _______

Mathematical Verification:
□ PID calculations match theoretical values ±0.01%
□ Anti-windup logic prevents integral accumulation
□ Derivative filtering reduces noise amplification

Code Review Evidence:
□ Algorithm implementation matches design specification
□ No memory leaks identified in 24-hour test
□ Exception handling covers all error conditions
```

### Custom Data Analysis - Performance Testing Format

Complex custom software requires performance validation under stress conditions:

```
Test Script OQ-DAS-001: Statistical Engine Performance
System: Custom pharmaceutical data analysis platform

Performance Requirements:
- 1000 concurrent analyses
- <3 second response for standard calculations
- Zero data corruption under load

Load Test Protocol:

1. Baseline Performance
   Single user, standard dataset (n=1000)
   Measure: CPU, memory, response time
   Baseline: _______

2. Concurrent User Scaling
   Users: 10, 50, 100, 500, 1000
   Monitor: Response degradation curve
   Results: [Performance graph]

3. Large Dataset Processing
   Test sets: 10K, 100K, 1M, 10M records
   Measure: Processing time, memory usage
   Results: [Scaling analysis]

4. Stress Testing
   150% maximum specified load
   Duration: 8 hours continuous
   Monitor: Memory leaks, crashes, data integrity
   Results: _______

5. Failure Recovery
   Interrupt processing at various stages
   Verify: Graceful recovery, data preservation
   Results: _______

Statistical Accuracy (Parallel Testing):
□ Results match SAS output ±0.0001%
□ Edge cases handled appropriately
□ Numerical stability verified

Performance Acceptance:
- 95th percentile response <3 seconds
- Linear scaling to 1000 users
- Zero data corruption observed
- Graceful degradation beyond limits
```

### Custom Automation - Integration Testing Format

Integration testing validates complex interactions between custom components:

```
Test Script OQ-AUTO-001: Multi-System Integration
Systems: Custom LIMS + Custom MES + Custom Analytics

Integration Test Scenarios:

Scenario 1: End-to-End Batch Processing
1. Create batch order in MES
2. Transfer to LIMS for testing
3. Execute analyses in LIMS
4. Return results to MES
5. Trigger analytics calculations
6. Generate integrated batch report

Verification Points:
□ Data integrity across transfers
□ No duplicate or lost records
□ Proper error handling
□ Transaction rollback capability
□ Audit trails synchronized

Scenario 2: Exception Handling
[Detailed exception test cases]

Scenario 3: Performance Under Load
[Concurrent transaction testing]

Data Integrity Verification:
- Compare record counts pre/post transfer
- Validate calculated fields
- Verify referential integrity
- Check audit trail completeness
```

### Custom EBR System - Comprehensive Validation Suite

Electronic Batch Record systems require extensive validation across all functions:

```
Test Script OQ-EBR-001: Complete Functional Validation
System: Custom-developed EBR platform

Test Suite Overview:
1. Recipe Management (15 test cases)
2. Batch Execution (25 test cases)
3. Electronic Signatures (10 test cases)
4. Audit Trail (12 test cases)
5. Reporting (8 test cases)
6. Integration (20 test cases)

Sample Test Case - Critical Process Parameter Monitoring:

Setup: Configure batch with critical parameters
- Temperature: 50-60°C (critical)
- Pressure: 1-3 bar (non-critical)
- pH: 6.8-7.2 (critical)

Execution:
1. Start batch execution
2. Simulate temperature = 65°C
   Expected: Immediate alarm, batch pause
   Actual: _______

3. Acknowledge alarm, enter deviation
   Expected: Deviation form, supervisor approval required
   Actual: _______

4. Continue with approved deviation
   Expected: Batch proceeds, deviation documented
   Actual: _______

5. Complete batch with deviations
   Expected: Report flags all deviations
   Actual: _______

21 CFR Part 11 Verification:
□ All actions require e-signature
□ Signatures include meaning
□ Audit trail tamper-proof
□ Two-factor authentication enforced
```

## Test format selection and compliance considerations

Selecting appropriate test formats requires careful risk assessment balanced with practical considerations. The FDA's Computer Software Assurance guidance emphasizes matching validation rigor to actual risk rather than applying maximum documentation to all systems.

**Robust scripted testing** suits high-risk functions directly impacting patient safety or product quality. These comprehensive scripts provide repeatability, traceability, and detailed evidence for regulatory inspection. Manufacturing control systems, clinical data management, and automated release testing typically warrant this approach.

**Limited scripted testing** offers flexibility for mixed-risk systems. High-risk functions receive detailed scripts while lower-risk areas use exploratory methods. This hybrid approach optimizes resources while maintaining compliance for critical functions. Configuration testing of commercial systems often benefits from this balanced methodology.

**Unscripted and exploratory testing** effectively validates user interfaces, workflow efficiency, and error handling in lower-risk applications. Subject matter experts leverage their experience to discover issues that scripted testing might miss. FDA explicitly endorses unscripted approaches for non-critical functions, reducing validation burden without compromising quality.

**Ad hoc testing** provides quick verification for patches, minor configuration changes, or troubleshooting. While insufficient for initial validation, ad hoc methods support ongoing system maintenance within established change control procedures.

## Ensuring 21 CFR Part 11 and GAMP 5 compliance

Regulatory compliance requires consistent implementation of electronic records and signatures controls regardless of test format. **Every OQ script must verify** that systems generate tamper-evident audit trails capturing who did what, when, and why. User access controls, including unique usernames and passwords, require testing across all permission levels.

GAMP 5 Second Edition emphasizes critical thinking over excessive documentation. Risk assessments should justify validation scope, with clear rationale for test format selection. **Leverage supplier testing** for standard functionality while focusing internal efforts on configurations and customizations. Modern approaches like continuous integration and automated testing align with GAMP 5 principles when properly documented.

Data integrity verification spans all test formats. The ALCOA+ principles (Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available) guide test design. **Each script should confirm** that data remains traceable, unalterable, and retrievable throughout its lifecycle.

## Key success factors for OQ test script development

Successful OQ testing begins with clear traceability from user requirements through test execution. Each test script must explicitly reference the requirements it verifies, enabling regulators to follow the validation logic. **Acceptance criteria should be specific, measurable, and directly linked** to intended use.

Test data selection significantly impacts validation quality. Reference standards, certified datasets, and known values provide objective verification of system calculations. For Category 5 systems, mathematical proofs and parallel testing against validated systems demonstrate algorithm accuracy.

Documentation depth should align with risk level. High-risk Category 5 systems warrant comprehensive step-by-step scripts with detailed expected results. Lower-risk Category 3 systems may use streamlined formats focusing on key functionality. **The goal remains consistent**: demonstrate the system performs reliably for its intended use.

Modern validation embraces efficiency without sacrificing quality. Automated testing tools capture evidence while reducing manual documentation. Risk-based approaches focus efforts where they matter most. The evolution from Computer System Validation to Computer Software Assurance reflects industry maturation, emphasizing outcomes over paperwork.

Organizations implementing these OQ test scripts should maintain flexibility while ensuring compliance. Regular review and updates keep validation current with evolving regulations and industry practices. By matching validation rigor to actual risk and leveraging modern testing approaches, pharmaceutical companies can achieve robust system validation supporting product quality and patient safety.