/**
 * URS Templates for GAMP-5 Pharmaceutical Test Generation
 *
 * Contains 8 curated templates (2 per GAMP category) with structured data
 * for form-based editing.
 */

// =============================================================================
// Type Definitions
// =============================================================================

export interface RequirementItem {
  id: string;           // e.g., "URS-EMS-001"
  description: string;  // e.g., "The system shall continuously monitor..."
}

export interface URSTemplateData {
  // Header fields (editable)
  systemName: string;
  gampCategoryLabel: string;  // "(Standard Software)", "(Configured Products)", etc.
  systemType: string;
  domain: string;
  complexityLevel: 'Low' | 'Medium' | 'Medium-High' | 'High';

  // Introduction (editable textarea)
  introduction: string;

  // Requirement sections (editable list of items)
  functionalRequirements: RequirementItem[];
  regulatoryRequirements: RequirementItem[];
  performanceRequirements: RequirementItem[];
  integrationRequirements: RequirementItem[];
}

export interface URSTemplate {
  id: string;
  name: string;
  gampCategory: '3' | '4' | '5' | 'ambiguous';
  description: string;
  icon: string;  // Emoji for card display
  data: URSTemplateData;
}

export type GampCategoryFilter = 'all' | '3' | '4' | '5' | 'ambiguous';

// =============================================================================
// Template Data (8 Curated Templates)
// =============================================================================

export const TEMPLATES: URSTemplate[] = [
  // =========================================================================
  // Category 3: Standard Software (Non-configured COTS)
  // =========================================================================
  {
    id: 'urs-001',
    name: 'Environmental Monitoring System',
    gampCategory: '3',
    description: 'Temperature and humidity monitoring for GMP storage areas using vendor-supplied software without modification.',
    icon: '🌡️',
    data: {
      systemName: 'Environmental Monitoring System (EMS)',
      gampCategoryLabel: '(Standard Software)',
      systemType: 'Continuous Temperature and Humidity Monitoring',
      domain: 'Environmental Control',
      complexityLevel: 'Low',
      introduction: 'This URS defines the requirements for an Environmental Monitoring System to monitor critical storage areas for temperature-sensitive pharmaceutical products.',
      functionalRequirements: [
        { id: 'URS-EMS-001', description: 'The system shall continuously monitor temperature in all GMP storage areas.' },
        { id: 'URS-EMS-002', description: 'Temperature readings shall be recorded at intervals not exceeding 5 minutes.' },
        { id: 'URS-EMS-003', description: 'The system shall use vendor-supplied software without modification.' },
        { id: 'URS-EMS-004', description: 'Temperature range: -80°C to +50°C with accuracy of ±0.5°C.' },
        { id: 'URS-EMS-005', description: 'The system shall generate alerts when temperature deviates ±2°C from setpoint.' },
        { id: 'URS-EMS-006', description: 'All data shall be stored in the vendor\'s standard database format.' },
        { id: 'URS-EMS-007', description: 'Standard reports provided by vendor shall be used for batch release.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-EMS-008', description: 'System shall maintain an audit trail per 21 CFR Part 11.' },
        { id: 'URS-EMS-009', description: 'Electronic signatures shall use vendor\'s built-in functionality.' },
        { id: 'URS-EMS-010', description: 'Data shall be retained for 7 years using vendor\'s archival feature.' },
      ],
      performanceRequirements: [
        { id: 'URS-EMS-011', description: 'System response time shall not exceed 30 seconds for alarm conditions.' },
        { id: 'URS-EMS-012', description: 'Data storage capacity shall support minimum 10 years of continuous monitoring.' },
        { id: 'URS-EMS-013', description: 'System availability shall be 99.5% excluding planned maintenance.' },
      ],
      integrationRequirements: [
        { id: 'URS-EMS-014', description: 'System shall interface with existing facility management system via standard protocols.' },
        { id: 'URS-EMS-015', description: 'Alarm notifications shall integrate with site paging system using vendor API.' },
      ],
    },
  },
  {
    id: 'urs-006',
    name: 'Inventory Management System',
    gampCategory: '3',
    description: 'COTS inventory tracking for pharmaceutical materials using standard warehouse management software.',
    icon: '📦',
    data: {
      systemName: 'Standard Inventory Management System',
      gampCategoryLabel: '(Standard Software)',
      systemType: 'COTS Inventory Management Platform',
      domain: 'Warehouse Management',
      complexityLevel: 'Low',
      introduction: 'This URS defines the requirements for a standard inventory management system to track pharmaceutical materials using commercial off-the-shelf software without customization.',
      functionalRequirements: [
        { id: 'URS-INV-001', description: 'System shall be based on commercially available inventory software (SAP WM, Oracle WMS).' },
        { id: 'URS-INV-002', description: 'Track raw materials, packaging components, and finished goods using standard item master.' },
        { id: 'URS-INV-003', description: 'Implement First-In-First-Out (FIFO) inventory rotation using vendor default algorithms.' },
        { id: 'URS-INV-004', description: 'Support First-Expired-First-Out (FEFO) rotation for expiry date management.' },
        { id: 'URS-INV-005', description: 'Generate standard picking lists using vendor templates.' },
        { id: 'URS-INV-006', description: 'Track inventory quantities in real-time using standard database updates.' },
        { id: 'URS-INV-007', description: 'Support barcode scanning using vendor\'s barcode integration module.' },
        { id: 'URS-INV-008', description: 'Generate cycle count schedules using vendor\'s standard scheduling engine.' },
        { id: 'URS-INV-009', description: 'Create inventory movement reports using pre-built templates.' },
        { id: 'URS-INV-010', description: 'Support multiple storage locations with standard location master setup.' },
        { id: 'URS-INV-011', description: 'Generate reorder alerts based on minimum stock levels using standard alerting.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-INV-016', description: 'Maintain inventory audit trail using vendor\'s standard logging functionality.' },
        { id: 'URS-INV-017', description: 'Support user access controls through vendor\'s role-based security.' },
        { id: 'URS-INV-018', description: 'Generate inventory accuracy reports using standard reconciliation features.' },
        { id: 'URS-INV-019', description: 'Archive transaction history using vendor\'s data retention policies.' },
      ],
      performanceRequirements: [
        { id: 'URS-INV-012', description: 'System shall support up to 10,000 SKUs using standard database capacity.' },
        { id: 'URS-INV-013', description: 'Inventory updates shall be reflected within 30 seconds using standard refresh rates.' },
        { id: 'URS-INV-014', description: 'Standard reports shall generate within 5 minutes using vendor default settings.' },
        { id: 'URS-INV-015', description: 'System shall support 25 concurrent users per vendor specifications.' },
      ],
      integrationRequirements: [
        { id: 'URS-INV-020', description: 'Interface with existing ERP system using vendor\'s standard connectors.' },
        { id: 'URS-INV-021', description: 'Export inventory data to Excel format using built-in export functionality.' },
      ],
    },
  },

  // =========================================================================
  // Category 4: Configured Products
  // =========================================================================
  {
    id: 'urs-002',
    name: 'Laboratory Information System',
    gampCategory: '4',
    description: 'Configured LIMS for QC sample management, testing workflows, and result reporting.',
    icon: '🔬',
    data: {
      systemName: 'Laboratory Information Management System (LIMS)',
      gampCategoryLabel: '(Configured Products)',
      systemType: 'Sample Management and Testing Platform',
      domain: 'Quality Control Laboratory',
      complexityLevel: 'Medium',
      introduction: 'This URS defines requirements for a LIMS to manage QC laboratory operations, including sample registration, test execution, and result reporting.',
      functionalRequirements: [
        { id: 'URS-LIMS-001', description: 'System shall be based on commercial LIMS package (LabWare/STARLIMS).' },
        { id: 'URS-LIMS-002', description: 'Configure workflows for raw material, in-process, and finished product testing.' },
        { id: 'URS-LIMS-003', description: 'System shall integrate with existing SAP ERP using vendor\'s standard adapter.' },
        { id: 'URS-LIMS-004', description: 'Configure sample login screens to capture site-specific attributes including batch number, manufacturing date, expiry date, and storage conditions.' },
        { id: 'URS-LIMS-005', description: 'Configure stability study protocols using vendor\'s configuration tools.' },
        { id: 'URS-LIMS-006', description: 'Implement custom business rules for OOS investigations using vendor\'s scripting language.' },
        { id: 'URS-LIMS-007', description: 'Configure electronic worksheets for 15 different analytical methods.' },
        { id: 'URS-LIMS-008', description: 'System shall use vendor\'s standard reporting engine with configured templates.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-LIMS-009', description: 'Configure user roles: Analyst, Reviewer, QA Approver.' },
        { id: 'URS-LIMS-010', description: 'Implement two-stage electronic review using configuration options.' },
        { id: 'URS-LIMS-011', description: 'Configure audit trail categories per site SOPs.' },
      ],
      performanceRequirements: [
        { id: 'URS-LIMS-012', description: 'Sample throughput shall support 500 samples per day.' },
        { id: 'URS-LIMS-013', description: 'Report generation shall complete within 5 minutes for standard templates.' },
        { id: 'URS-LIMS-014', description: 'System shall support concurrent use by 50 users.' },
      ],
      integrationRequirements: [
        { id: 'URS-LIMS-015', description: 'Interface with analytical instruments using vendor connectors.' },
        { id: 'URS-LIMS-016', description: 'Configure data exchange with stability chambers via OPC protocol.' },
        { id: 'URS-LIMS-017', description: 'Generate certificates of analysis in PDF format using configured templates.' },
      ],
    },
  },
  {
    id: 'urs-022',
    name: 'Deviation Management System',
    gampCategory: '4',
    description: 'Configured QMS workflows for deviation tracking, CAPA management, and quality event handling.',
    icon: '⚠️',
    data: {
      systemName: 'Configured Deviation Management',
      gampCategoryLabel: '(Configured Product)',
      systemType: 'QMS deviation and CAPA workflows configured via vendor tools',
      domain: 'Quality Assurance',
      complexityLevel: 'Medium-High',
      introduction: 'Implement a deviation management workflow using vendor\'s configuration framework including state models, business rules, and reporting templates.',
      functionalRequirements: [
        { id: 'URS-022-001', description: 'Configure deviation lifecycle with states: Draft, Under Review, Investigation, CAPA, Closure.' },
        { id: 'URS-022-002', description: 'Implement risk scoring rules using vendor scripting.' },
        { id: 'URS-022-003', description: 'Configure mandatory fields and attachments by risk level.' },
        { id: 'URS-022-004', description: 'Provide configured dashboards and standard reporting engine outputs.' },
        { id: 'URS-022-005', description: 'Enforce e-signatures at key state transitions.' },
        { id: 'URS-022-006', description: 'Implement SLA timers with escalation notifications.' },
        { id: 'URS-022-007', description: 'Provide CAPA linkage with effectiveness checks.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-022-008', description: 'Full ALCOA+ compliant audit trail for record changes.' },
        { id: 'URS-022-009', description: '21 CFR Part 11 compliant e-signatures and access controls.' },
        { id: 'URS-022-010', description: 'Retention and retrieval of closed records per policy.' },
      ],
      performanceRequirements: [
        { id: 'URS-022-011', description: 'Handle 500 concurrent users across sites.' },
        { id: 'URS-022-012', description: 'Search latency < 2 seconds for 1M records.' },
      ],
      integrationRequirements: [
        { id: 'URS-022-013', description: 'Integrate with LDAP/AD and HRMS for user provisioning.' },
        { id: 'URS-022-014', description: 'API-based integration to send CAPA tasks to ticketing system.' },
      ],
    },
  },

  // =========================================================================
  // Category 5: Custom Applications
  // =========================================================================
  {
    id: 'urs-003',
    name: 'Manufacturing Execution System',
    gampCategory: '5',
    description: 'Custom MES for electronic batch records with proprietary algorithms and integrations.',
    icon: '🏭',
    data: {
      systemName: 'Manufacturing Execution System (MES)',
      gampCategoryLabel: '(Custom Applications)',
      systemType: 'Custom Batch Record Management System',
      domain: 'Manufacturing Operations',
      complexityLevel: 'High',
      introduction: 'This URS defines requirements for a custom MES to manage electronic batch records for sterile injectable products.',
      functionalRequirements: [
        { id: 'URS-MES-001', description: 'System shall be custom-developed to integrate with proprietary equipment.' },
        { id: 'URS-MES-002', description: 'Custom algorithms required for dynamic in-process control limits based on multivariate analysis, real-time batch genealogy tracking, and proprietary yield optimization calculations.' },
        { id: 'URS-MES-003', description: 'Develop custom interfaces for 12 different equipment types with proprietary protocols.' },
        { id: 'URS-MES-004', description: 'Custom workflow engine to handle parallel processing paths unique to manufacturing process.' },
        { id: 'URS-MES-005', description: 'Develop proprietary data structures for multi-level bill of materials with conditional components.' },
        { id: 'URS-MES-006', description: 'Custom mobile application for shop floor data entry.' },
        { id: 'URS-MES-007', description: 'Bespoke analytics module for real-time process monitoring.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-MES-008', description: 'Custom audit trail implementation with enhanced metadata.' },
        { id: 'URS-MES-009', description: 'Develop proprietary electronic signature workflow.' },
        { id: 'URS-MES-010', description: 'Custom data integrity checks beyond standard validations.' },
      ],
      performanceRequirements: [
        { id: 'URS-MES-011', description: 'System shall process 100 concurrent batch records.' },
        { id: 'URS-MES-012', description: 'Real-time data collection with maximum 2-second latency.' },
        { id: 'URS-MES-013', description: 'Custom reporting shall complete within 10 minutes for complex queries.' },
      ],
      integrationRequirements: [
        { id: 'URS-MES-014', description: 'Develop custom APIs for third-party system integration.' },
        { id: 'URS-MES-015', description: 'Proprietary message queuing for equipment communication.' },
        { id: 'URS-MES-016', description: 'Custom synchronization with enterprise planning systems.' },
      ],
    },
  },
  {
    id: 'urs-025',
    name: 'Custom Batch Release Orchestrator',
    gampCategory: '5',
    description: 'Microservice-based orchestrator with proprietary release rules and multi-factor scoring.',
    icon: '📊',
    data: {
      systemName: 'Custom Batch Release Orchestrator',
      gampCategoryLabel: '(Custom Application)',
      systemType: 'Microservice-based orchestrator with proprietary release rules',
      domain: 'Manufacturing Operations',
      complexityLevel: 'High',
      introduction: 'Develop a custom application that orchestrates batch release by applying proprietary algorithms combining QC results, deviations, and stability trending.',
      functionalRequirements: [
        { id: 'URS-025-001', description: 'Ingest test results, deviations, and stability metrics via APIs.' },
        { id: 'URS-025-002', description: 'Apply proprietary multi-factor release scoring algorithm.' },
        { id: 'URS-025-003', description: 'Provide explainability dashboard for each release decision.' },
        { id: 'URS-025-004', description: 'Support manual override with dual e-signature and rationale.' },
        { id: 'URS-025-005', description: 'Generate release packet with all evidentiary documents.' },
        { id: 'URS-025-006', description: 'Implement rule versioning with rollback capability.' },
        { id: 'URS-025-007', description: 'Provide sandbox for what-if analysis on release rules.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-025-008', description: 'Maintain data lineage and ALCOA+ attributes for all inputs.' },
        { id: 'URS-025-009', description: 'Enforce 21 CFR Part 11 for approvals.' },
        { id: 'URS-025-010', description: 'Provide traceability from algorithm input to final disposition.' },
      ],
      performanceRequirements: [
        { id: 'URS-025-011', description: 'Process a batch decision in < 5 seconds with 1,000 inputs.' },
        { id: 'URS-025-012', description: 'Availability ≥ 99.9% with active-active deployment.' },
      ],
      integrationRequirements: [
        { id: 'URS-025-013', description: 'Integrations with LIMS, QMS, MES, and ERP via APIs.' },
        { id: 'URS-025-014', description: 'SSO via OIDC with role-based authorization.' },
      ],
    },
  },

  // =========================================================================
  // Ambiguous (Category 3/4 Border Cases)
  // =========================================================================
  {
    id: 'urs-004',
    name: 'Chromatography Data System',
    gampCategory: 'ambiguous',
    description: 'CDS with mix of standard instrument control and custom calculations - category depends on implementation choices.',
    icon: '📈',
    data: {
      systemName: 'Chromatography Data System (CDS)',
      gampCategoryLabel: 'Ambiguous (3/4)',
      systemType: 'Analytical Instrument Control and Data Analysis',
      domain: 'Analytical Chemistry',
      complexityLevel: 'Medium',
      introduction: 'This URS defines requirements for a CDS to control HPLC/GC instruments and process chromatographic data.',
      functionalRequirements: [
        { id: 'URS-CDS-001', description: 'System based on commercial CDS software (Empower/OpenLab).' },
        { id: 'URS-CDS-002', description: 'Use vendor\'s standard instrument control for Waters/Agilent equipment.' },
        { id: 'URS-CDS-003', description: 'Minor configuration of acquisition methods within vendor parameters.' },
        { id: 'URS-CDS-004', description: 'Implement custom calculations using vendor\'s formula editor for non-standard impurity calculations.' },
        { id: 'URS-CDS-005', description: 'Develop custom reports using vendor\'s report designer.' },
        { id: 'URS-CDS-006', description: 'Configure standard integration parameters for peak detection.' },
        { id: 'URS-CDS-007', description: 'Create custom export routines for LIMS interface.' },
        { id: 'URS-CDS-008', description: 'Implement site-specific naming conventions via configuration.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-CDS-015', description: 'System shall maintain complete audit trail for all analytical data per 21 CFR Part 11.' },
        { id: 'URS-CDS-016', description: 'Electronic signatures shall be implemented for method approval and data review.' },
        { id: 'URS-CDS-017', description: 'Data integrity controls shall prevent unauthorized data modification.' },
        { id: 'URS-CDS-018', description: 'System shall support data retention requirements for regulatory submissions.' },
      ],
      performanceRequirements: [
        { id: 'URS-CDS-012', description: 'Data acquisition shall support up to 8 simultaneous instrument runs.' },
        { id: 'URS-CDS-013', description: 'Peak integration processing shall complete within 30 seconds.' },
        { id: 'URS-CDS-014', description: 'Custom calculation routines shall execute within 60 seconds.' },
      ],
      integrationRequirements: [
        { id: 'URS-CDS-019', description: 'Interface with LIMS using standard XML format.' },
        { id: 'URS-CDS-020', description: 'Export data to regulatory submission formats (eCTD).' },
        { id: 'URS-CDS-021', description: 'Synchronize with enterprise document management system.' },
      ],
    },
  },
  {
    id: 'urs-018',
    name: 'Chromatography Sample Scheduling',
    gampCategory: 'ambiguous',
    description: 'Scheduling and reporting add-on that can be realized via COTS or configuration - category depends on approach.',
    icon: '🔧',
    data: {
      systemName: 'Chromatography Sample Scheduling Module',
      gampCategoryLabel: 'Ambiguous',
      systemType: 'Scheduling and reporting add-on for CDS/LIMS',
      domain: 'Analytical Chemistry (QC Lab)',
      complexityLevel: 'Medium',
      introduction: 'This module provides laboratory analysts with a standardized way to schedule chromatography sample runs and generate compliance-ready reports. The capability can be realized using the vendor\'s built-in scheduling and reporting features (commercial off-the-shelf) or by configuring workflow templates and parameters via the supplier\'s configuration tools for lab-specific routing.',
      functionalRequirements: [
        { id: 'URS-018-001', description: 'Users shall create sample run schedules with priority, instrument, and method selections.' },
        { id: 'URS-018-002', description: 'The system shall enforce method-version locking for scheduled runs.' },
        { id: 'URS-018-003', description: 'The module shall provide vendor\'s standard reporting engine with configured templates for batch results.' },
        { id: 'URS-018-004', description: 'Users shall route samples to instruments based on configured availability rules.' },
        { id: 'URS-018-005', description: 'The system shall support pause/resume and re-queue of failed runs with reason capture.' },
        { id: 'URS-018-006', description: 'Audit trail entries shall be generated for all changes to schedule entries.' },
        { id: 'URS-018-007', description: 'Users shall receive alerts for instrument readiness and run completion.' },
        { id: 'URS-018-008', description: 'Role-based access shall control schedule creation, approval, and execution.' },
        { id: 'URS-018-009', description: 'The system shall support configured hold rules when stability chambers report excursions.' },
        { id: 'URS-018-010', description: 'Configurable approvals shall be required prior to execution of GMP runs.' },
        { id: 'URS-018-011', description: 'The system shall generate exception summaries for out-of-trend runs.' },
        { id: 'URS-018-012', description: 'The system shall provide a schedule Gantt view filtered by instrument and analyst.' },
      ],
      regulatoryRequirements: [
        { id: 'URS-018-013', description: 'Electronic records shall comply with 21 CFR Part 11 including electronic signatures.' },
        { id: 'URS-018-014', description: 'All actions shall be captured in a secure, time-stamped audit trail (ALCOA+).' },
        { id: 'URS-018-015', description: 'Report templates shall be controlled artifacts under document control.' },
        { id: 'URS-018-016', description: 'Access controls shall follow least privilege with periodic review.' },
        { id: 'URS-018-017', description: 'System shall support retention and retrieval for the required regulatory period.' },
      ],
      performanceRequirements: [
        { id: 'URS-018-018', description: 'Load 500-sample schedules in < 3 seconds in typical conditions.' },
        { id: 'URS-018-019', description: 'Generate standard batch report within 10 seconds for 200 injections.' },
        { id: 'URS-018-020', description: 'Support concurrent access by 30 users with no functional degradation.' },
        { id: 'URS-018-021', description: 'System availability shall be ≥ 99.5% during lab operating hours.' },
        { id: 'URS-018-022', description: 'Alerts shall be delivered within 5 seconds of event detection.' },
        { id: 'URS-018-023', description: 'Gantt view refresh shall complete in < 2 seconds.' },
      ],
      integrationRequirements: [
        { id: 'URS-018-024', description: 'Integrate with vendor CDS/LIMS via standard APIs or vendor-approved connectors.' },
        { id: 'URS-018-025', description: 'Pull instrument availability and calibration status from asset system.' },
        { id: 'URS-018-026', description: 'Push finalized batch reports to the controlled document repository.' },
        { id: 'URS-018-027', description: 'Support LDAP/AD for user authentication and role sync.' },
      ],
    },
  },
];

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Convert structured template data back to markdown format for submission
 */
export function templateDataToMarkdown(template: URSTemplate, data: URSTemplateData): string {
  const formatRequirements = (items: RequirementItem[]): string =>
    items.map(r => `- **${r.id}**: ${r.description}`).join('\n');

  return `# ${template.id.toUpperCase()}: ${data.systemName}
**GAMP Category**: ${data.gampCategoryLabel}
**System Type**: ${data.systemType}
**Domain**: ${data.domain}
**Complexity Level**: ${data.complexityLevel}

## 1. Introduction
${data.introduction}

## 2. Functional Requirements
${formatRequirements(data.functionalRequirements)}

## 3. Regulatory Requirements
${formatRequirements(data.regulatoryRequirements)}

## 4. Performance Requirements
${formatRequirements(data.performanceRequirements)}

## 5. Integration Requirements
${formatRequirements(data.integrationRequirements)}
`;
}

/**
 * Get templates filtered by GAMP category
 */
export function getTemplatesByCategory(category: GampCategoryFilter): URSTemplate[] {
  if (category === 'all') {
    return TEMPLATES;
  }
  return TEMPLATES.filter(t => t.gampCategory === category);
}

/**
 * Get a single template by ID
 */
export function getTemplateById(id: string): URSTemplate | undefined {
  return TEMPLATES.find(t => t.id === id);
}

/**
 * Get category display info
 */
export function getCategoryInfo(category: '3' | '4' | '5' | 'ambiguous'): {
  label: string;
  description: string;
  colorClass: string;
} {
  switch (category) {
    case '3':
      return {
        label: 'Category 3',
        description: 'Standard Software (Non-configured COTS)',
        colorClass: 'bg-green-500/20 text-green-300',
      };
    case '4':
      return {
        label: 'Category 4',
        description: 'Configured Products',
        colorClass: 'bg-blue-500/20 text-blue-300',
      };
    case '5':
      return {
        label: 'Category 5',
        description: 'Custom Applications',
        colorClass: 'bg-purple-500/20 text-purple-300',
      };
    case 'ambiguous':
      return {
        label: 'Ambiguous',
        description: 'Requires Human Review',
        colorClass: 'bg-amber-500/20 text-amber-300',
      };
  }
}

/**
 * Clone template data for editing (deep copy)
 */
export function cloneTemplateData(data: URSTemplateData): URSTemplateData {
  return {
    ...data,
    functionalRequirements: data.functionalRequirements.map(r => ({ ...r })),
    regulatoryRequirements: data.regulatoryRequirements.map(r => ({ ...r })),
    performanceRequirements: data.performanceRequirements.map(r => ({ ...r })),
    integrationRequirements: data.integrationRequirements.map(r => ({ ...r })),
  };
}
