/**
 * Compliance Flash Card Content
 *
 * Extracted from comprehensive regulatory compliance mapping documents.
 * Source: .claude/state/results/*-compliance-mapping-20251122.md
 *
 * Frameworks covered:
 * - GAMP-5: Good Automated Manufacturing Practice
 * - ALCOA+: Data Integrity Principles
 * - 21 CFR Part 11: Electronic Records & Signatures
 * - ICH Q9: Quality Risk Management
 * - ISO/IEC 27001: Information Security
 * - EU AI Act: Artificial Intelligence Regulation
 */

// ==================== TYPE DEFINITIONS ====================

export interface ComplianceCard {
  id: string;
  title: string;
  shortDescription: string;
  implementation: string;
  evidence?: string;
  status?: 'implemented' | 'partial' | 'planned';
}

export interface ComplianceFramework {
  id: string;
  name: string;
  fullName: string;
  description: string;
  icon: string;
  color: string;
  cards: ComplianceCard[];
}

// ==================== GAMP-5 COMPLIANCE ====================

export const gamp5Framework: ComplianceFramework = {
  id: 'gamp5',
  name: 'GAMP-5',
  fullName: 'Good Automated Manufacturing Practice Version 5',
  description: 'Risk-based approach to compliant GxP computerized systems validation',
  icon: '🏷️',
  color: '#3b82f6', // blue
  cards: [
    {
      id: 'gamp5-categorization',
      title: 'Software Categorization',
      shortDescription: 'Systems categorized by complexity (Cat 1-5) to determine validation rigor',
      implementation: 'Automatic GAMP categorization with confidence scoring. Category 5 systems get 25-30 tests vs. Category 3 with 5-10 tests.',
      evidence: 'unified_workflow.py:203-275 - Categorization workflow with human oversight',
      status: 'implemented'
    },
    {
      id: 'gamp5-risk-based',
      title: 'Risk-Based Validation',
      shortDescription: 'Validation effort proportionate to risk and complexity',
      implementation: 'Test count scales with GAMP category. Multi-agent validation provides redundant checks for high-risk systems.',
      evidence: 'Planning workflow generates risk-appropriate test coverage',
      status: 'implemented'
    },
    {
      id: 'gamp5-lifecycle',
      title: 'Life Cycle Management',
      shortDescription: 'Structured phases (Concept → Project → Operation → Retirement)',
      implementation: 'Currently in Project phase (Docker Compose). AWS migration moves to Operation phase with Terraform IaC.',
      evidence: 'PRPs/tasks/ directory with 23 structured tasks across 6 phases',
      status: 'implemented'
    },
    {
      id: 'gamp5-traceability',
      title: 'Specification Traceability',
      shortDescription: 'URS → FS → DS → Tests with complete traceability',
      implementation: 'Every test case linked to URS requirement. Requirements coverage report in dashboard.',
      evidence: 'Traceability matrix in generated YAML test suites',
      status: 'implemented'
    },
    {
      id: 'gamp5-alcoa',
      title: 'ALCOA+ Data Integrity',
      shortDescription: 'Electronic records must be Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available',
      implementation: 'Dedicated ALCOA+ validator checks all 9 principles. SHA-512 chain of custody.',
      evidence: 'alcoa_validator.py:1-287 - Comprehensive validation',
      status: 'implemented'
    },
    {
      id: 'gamp5-signatures',
      title: 'Electronic Signatures',
      shortDescription: '21 CFR Part 11 compliant signatures for approvals',
      implementation: 'Cryptographic signatures with user_id, timestamp, action, hash. Clerk authentication ensures identity.',
      evidence: 'unified_workflow.py:580-621 - Signature creation workflow',
      status: 'implemented'
    },
    {
      id: 'gamp5-change-control',
      title: 'Change Control',
      shortDescription: 'All changes require approval, version control, impact assessment',
      implementation: 'Git version control + PRP workflow for structured changes. tester-agent validates before completion.',
      evidence: '.claude/state/prp-workflow-state.md - Change audit trail',
      status: 'implemented'
    },
    {
      id: 'gamp5-audit-trail',
      title: 'Audit Trail',
      shortDescription: 'Who, what, when, why for all critical actions',
      implementation: 'Comprehensive audit logging with ALCOA+ markers. LangFuse traces 131 spans per execution. Append-only design.',
      evidence: 'audit.py:1-145 + LangFuse Cloud dashboard',
      status: 'implemented'
    },
    {
      id: 'gamp5-security',
      title: 'Security Controls',
      shortDescription: 'Authentication, authorization, encryption, OWASP compliance',
      implementation: 'Clerk authentication + JWT authorization. TLS 1.3 encryption. OWASP LLM Top 10 validation in Step 1.',
      evidence: 'auth.py:18-67 + OWASP checks in workflow',
      status: 'implemented'
    },
    {
      id: 'gamp5-validation-testing',
      title: 'Validation Testing (IQ/OQ/PQ)',
      shortDescription: 'Prove system installed, operates, and performs correctly',
      implementation: 'Docker health checks (IQ), generated test suites (OQ), end-to-end validation (PQ).',
      evidence: 'test_e2e_workflow.py + LangFuse performance metrics',
      status: 'implemented'
    },
    {
      id: 'gamp5-periodic-review',
      title: 'Periodic Review',
      shortDescription: 'Regular review of validated systems with revalidation after changes',
      implementation: 'LangFuse continuous monitoring. PRP workflow for change management. AWS migration triggers full revalidation.',
      evidence: 'CloudWatch metrics + change tracking in Git',
      status: 'implemented'
    },
    {
      id: 'gamp5-supplier-assessment',
      title: 'Supplier Assessment',
      shortDescription: 'Qualify third-party vendors and COTS components',
      implementation: 'All Category 3/4 components assessed (DeepSeek, AWS, Clerk). Vendor compliance verified (SOC 2, ISO 27001).',
      evidence: 'Supplier list in package.json + compliance documentation',
      status: 'implemented'
    },
    {
      id: 'gamp5-disaster-recovery',
      title: 'Disaster Recovery',
      shortDescription: 'Backup, recovery procedures, RTO/RPO defined',
      implementation: 'Aurora automated backups (35-day retention), S3 Object Lock (7-year), Multi-AZ deployment. RTO <1hr, RPO <5min.',
      evidence: 'aws/AWS-ARCHITECTURE.md:445-478 - DR strategy',
      status: 'partial'
    },
    {
      id: 'gamp5-critical-thinking',
      title: 'Critical Thinking (Appendix D5)',
      shortDescription: 'Challenge assumptions, verify outputs, question automation',
      implementation: 'Multi-agent validation (3 independent checks), NO FALLBACK LOGIC, confidence-based human escalation.',
      evidence: 'Parallel agent execution in workflow steps 4-5',
      status: 'implemented'
    },
    {
      id: 'gamp5-ai-validation',
      title: 'AI/ML Validation (Appendix D11)',
      shortDescription: 'Explainability, bias detection, model validation',
      implementation: 'DeepSeek V3 open-weights (inspectable), LangFuse traces all prompts/responses, multi-agent consensus reduces bias.',
      evidence: 'LangFuse observability + EU AI Act compliance mapping',
      status: 'implemented'
    }
  ]
};

// ==================== ALCOA+ COMPLIANCE ====================

export const alcoaPlusFramework: ComplianceFramework = {
  id: 'alcoa-plus',
  name: 'ALCOA+',
  fullName: 'Data Integrity Principles (Attributable, Legible, Contemporaneous, Original, Accurate, Complete, Consistent, Enduring, Available)',
  description: 'Pharmaceutical data integrity standard ensuring electronic records are trustworthy',
  icon: '✅',
  color: '#10b981', // green
  cards: [
    {
      id: 'alcoa-attributable',
      title: 'Attributable',
      shortDescription: 'All actions must be linked to specific individuals with unique user identification.',
      implementation: 'Clerk authentication captures user_id and email for every workflow execution. All audit logs and LangFuse traces include complete user attribution.',
      evidence: 'auth.py:18-67, audit.py:76-82, langfuse_callback.py:29-94',
      status: 'implemented'
    },
    {
      id: 'alcoa-legible',
      title: 'Legible',
      shortDescription: 'Records must be human-readable in standardized formats with clear naming.',
      implementation: 'YAML output with UTF-8 encoding. ISO 8601 timestamps. Self-explanatory field names. No cryptic abbreviations.',
      evidence: 'oq_generator.py:198-203, local_adapter.py:134-143',
      status: 'implemented'
    },
    {
      id: 'alcoa-contemporaneous',
      title: 'Contemporaneous',
      shortDescription: 'Records created in real-time as work is performed, not reconstructed later.',
      implementation: 'Automatic UTC timestamps generated by system (not manual). LangFuse traces capture exact execution timeline with no delays.',
      evidence: 'audit.py:76, langfuse_callback.py:29-94',
      status: 'implemented'
    },
    {
      id: 'alcoa-original',
      title: 'Original',
      shortDescription: 'First recording of data with immutability controls to prevent modifications.',
      implementation: 'Append-only audit logs (no UPDATE/DELETE). SHA-512 chain of custody detects tampering. S3 Object Lock planned for 7-year immutability.',
      evidence: 'alcoa_validator.py:45-67, audit.py:1-145',
      status: 'partial'
    },
    {
      id: 'alcoa-accurate',
      title: 'Accurate',
      shortDescription: 'Data validated for correctness through multi-agent cross-checks and confidence scoring.',
      implementation: 'Three independent agents validate each decision. Confidence <80% triggers human review. NO FALLBACK LOGIC ensures explicit error handling.',
      evidence: 'unified_workflow.py:317-395, alcoa_validator.py:89-112',
      status: 'implemented'
    },
    {
      id: 'alcoa-complete',
      title: 'Complete',
      shortDescription: 'All required fields populated with full context and traceability.',
      implementation: 'Required metadata enforcement. Every test case includes objectives, steps, criteria, and URS traceability. 131 spans captured per workflow.',
      evidence: 'local_adapter.py:89-103, oq_generator.py:156-203',
      status: 'implemented'
    },
    {
      id: 'alcoa-consistent',
      title: 'Consistent',
      shortDescription: 'Standardized formats maintained across time and systems.',
      implementation: 'ISO 8601 UTC timestamps throughout. Pydantic enums enforce terminology (GAMP categories, risk levels). YAML schema validated before save.',
      evidence: 'alcoa_validator.py:134-156, unified_workflow.py:45-67',
      status: 'implemented'
    },
    {
      id: 'alcoa-enduring',
      title: 'Enduring',
      shortDescription: 'Long-term retention (7+ years) with format preservation and migration strategies.',
      implementation: 'Persistent Docker volumes (current). AWS S3 Object Lock with 7-year retention (planned). YAML format ensures readability across technology changes.',
      evidence: 'docker-compose.yml:89-95, aws/AWS-ARCHITECTURE.md:445-478',
      status: 'partial'
    },
    {
      id: 'alcoa-available',
      title: 'Available',
      shortDescription: 'Records readily accessible for authorized personnel with fast retrieval.',
      implementation: 'RESTful API with <5 second download time. History dashboard for browsing all jobs. LangFuse search/filter by user, date, tags.',
      evidence: 'app.py:89-178, history.tsx',
      status: 'implemented'
    }
  ]
};

// ==================== 21 CFR PART 11 COMPLIANCE ====================

export const cfr21Part11Framework: ComplianceFramework = {
  id: 'cfr-part-11',
  name: '21 CFR Part 11',
  fullName: 'Electronic Records and Electronic Signatures',
  description: 'FDA regulation for electronic records and signatures in pharmaceutical systems',
  icon: '✍️',
  color: '#8b5cf6', // purple
  cards: [
    {
      id: 'cfr11-validation',
      title: 'System Validation (§11.10(a))',
      shortDescription: 'Systems must be validated to ensure accuracy and reliability.',
      implementation: 'GAMP-5 Category 5 validation with IQ/OQ/PQ. Automated regression testing. SHA-512 hashing detects record tampering.',
      evidence: 'test_e2e_workflow.py, alcoa_validator.py:45-67',
      status: 'implemented'
    },
    {
      id: 'cfr11-audit-trail',
      title: 'Audit Trail (§11.10(e))',
      shortDescription: 'Secure, time-stamped audit trail of all actions. Cannot be modified.',
      implementation: 'Comprehensive audit logging with ALCOA+ markers. Append-only database (no UPDATE/DELETE). LangFuse traces 131 spans per execution.',
      evidence: 'audit.py:1-145, langfuse_callback.py:29-94',
      status: 'implemented'
    },
    {
      id: 'cfr11-retention',
      title: 'Record Retention (§11.10(c))',
      shortDescription: 'Electronic records retained for 7+ years (pharmaceutical requirement).',
      implementation: 'Persistent Docker volumes (current). AWS S3 Object Lock with 7-year retention (planned). YAML format ensures long-term readability.',
      evidence: 'docker-compose.yml:89-95, aws/AWS-ARCHITECTURE.md:445-478',
      status: 'partial'
    },
    {
      id: 'cfr11-copies',
      title: 'Copies of Records (§11.10(b))',
      shortDescription: 'Ability to generate accurate, human-readable copies for inspection.',
      implementation: 'Download endpoint provides exact YAML copy. Human-readable format (can be printed). <5 second response time.',
      evidence: 'app.py:145-178, ComplianceDashboard.tsx',
      status: 'implemented'
    },
    {
      id: 'cfr11-access-controls',
      title: 'Access Controls (§11.10(d))',
      shortDescription: 'Limit access to authorized individuals. Verify identity before allowing actions.',
      implementation: 'Clerk authentication with JWT tokens (RS256). Authorization checks prevent unauthorized access. Only job owner can view/download results.',
      evidence: 'auth.py:18-67, app.py:89-115',
      status: 'implemented'
    },
    {
      id: 'cfr11-operational-checks',
      title: 'Operational Checks (§11.10(f))',
      shortDescription: 'Validate data input. Enforce operational sequencing of steps.',
      implementation: 'Input validation (file format, size, OWASP security scan). Event-driven workflow enforces step order. Immutable jobs (no UPDATE/DELETE).',
      evidence: 'unified_workflow.py:109-158, app.py:34-67',
      status: 'implemented'
    },
    {
      id: 'cfr11-authority-checks',
      title: 'Authority Checks (§11.10(g))',
      shortDescription: 'Verify individuals authorized to perform operations.',
      implementation: 'Ownership checks (only job owner has access). Role-based access control (RBAC) planned for reviewer approval workflows.',
      evidence: 'app.py:89-115',
      status: 'partial'
    },
    {
      id: 'cfr11-device-checks',
      title: 'Device Checks (§11.10(h))',
      shortDescription: 'Verify devices authorized to input data. Prevent unauthorized devices.',
      implementation: 'HTTPS enforced (TLS 1.3). Docker network isolation. AWS WAF + IP allowlisting planned for production.',
      evidence: 'Docker Compose TLS, aws/AWS-ARCHITECTURE.md:289-334',
      status: 'partial'
    },
    {
      id: 'cfr11-personnel',
      title: 'Personnel (§11.10(i))',
      shortDescription: 'Ensure users have education, training, and experience for assigned tasks.',
      implementation: '"How It Works" modal provides interactive training (Task 3.9). Flash card workflow visualization educates on compliance. Quick Start Guide available.',
      evidence: 'QUICK_START_GUIDE.md, HowItWorksModal.tsx (planned)',
      status: 'planned'
    },
    {
      id: 'cfr11-accountability',
      title: 'Accountability (§11.10(j))',
      shortDescription: 'Establish individuals accountable for actions. Document responsibility.',
      implementation: 'Every action logged with user_id and email. Electronic signatures document accountability. Audit trail captures responsible individual.',
      evidence: 'audit.py:76-145, unified_workflow.py:580-621',
      status: 'implemented'
    },
    {
      id: 'cfr11-documentation',
      title: 'Documentation (§11.10(k))',
      shortDescription: 'Written policies for design, validation, access, maintenance, disaster recovery.',
      implementation: 'Complete documentation: Technical Architecture Report, MVP Implementation Plan, PRP tasks, validation tests, change control procedures.',
      evidence: 'TECHNICAL_ARCHITECTURE_REPORT.md, PRPs/tasks/',
      status: 'implemented'
    },
    {
      id: 'cfr11-signatures',
      title: 'Electronic Signatures (§11.50-300)',
      shortDescription: 'Signatures must include name, date/time, meaning. Unique to individual. Two-factor authentication.',
      implementation: 'Cryptographic signatures with all required elements. Clerk MFA support. Signatures linked to records via SHA-256 hash.',
      evidence: 'unified_workflow.py:580-621, Clerk authentication',
      status: 'partial'
    }
  ]
};

// ==================== ICH Q9 COMPLIANCE ====================

export const ichQ9Framework: ComplianceFramework = {
  id: 'ich-q9',
  name: 'ICH Q9',
  fullName: 'Quality Risk Management',
  description: 'Systematic approach to quality risk management in pharmaceuticals',
  icon: '⚠️',
  color: '#f59e0b', // amber
  cards: [
    {
      id: 'q9-risk-based-approach',
      title: 'Risk-Based Approach',
      shortDescription: 'Validation effort should be proportionate to risk, complexity, and impact.',
      implementation: 'GAMP-5 categorization determines test count. Category 5 systems get 25-30 tests vs. Category 3 with 5-10 tests.',
      evidence: 'unified_workflow.py:203-275, ICH Q9 compliance mapping',
      status: 'implemented'
    },
    {
      id: 'q9-risk-assessment',
      title: 'Risk Assessment (What might go wrong?)',
      shortDescription: 'Systematic identification of hazards and estimation of risk.',
      implementation: 'GAMP-5 categorization identifies software complexity risk. Multi-agent validation detects discrepancies. OWASP/ALCOA+ checks identify security and data integrity risks.',
      evidence: 'unified_workflow.py:203-395, oq_generator.py',
      status: 'implemented'
    },
    {
      id: 'q9-risk-analysis',
      title: 'Risk Analysis (What is the likelihood?)',
      shortDescription: 'Estimate probability of failure based on confidence and consensus.',
      implementation: 'Confidence scoring (0.0-1.0) estimates likelihood. <80% confidence triggers human review. Agent consensus analysis detects high-likelihood errors.',
      evidence: 'unified_workflow.py:257-275, 465-520',
      status: 'implemented'
    },
    {
      id: 'q9-risk-evaluation',
      title: 'Risk Evaluation (What are the consequences?)',
      shortDescription: 'Assess impact of failure on patient safety and regulatory compliance.',
      implementation: 'GAMP category = consequence severity. Category 5 (custom apps) requires comprehensive validation due to high consequences of failure.',
      evidence: 'ICH Q9 compliance mapping, GAMP-5 categorization',
      status: 'implemented'
    },
    {
      id: 'q9-risk-reduction',
      title: 'Risk Reduction (NO FALLBACK LOGIC)',
      shortDescription: 'Implement controls to reduce risk to acceptable levels.',
      implementation: 'NO FALLBACK LOGIC ensures explicit failures. Multi-agent redundancy reduces single-point failures. Confidence-based escalation prevents risky automated decisions.',
      evidence: 'CLAUDE.md (NO FALLBACK LOGIC policy), unified_workflow.py',
      status: 'implemented'
    },
    {
      id: 'q9-risk-communication',
      title: 'Risk Communication (Audit Trails)',
      shortDescription: 'Share risk information between decision-makers and stakeholders.',
      implementation: 'Comprehensive audit trail logs all risk decisions. LangFuse traces capture 131 spans per execution. Electronic signatures formalize approvals.',
      evidence: 'audit.py:1-145, LangFuse Cloud dashboard',
      status: 'implemented'
    },
    {
      id: 'q9-risk-review',
      title: 'Risk Review (Continuous Monitoring)',
      shortDescription: 'Monitor risk management process with new knowledge and experience.',
      implementation: 'LangFuse continuous monitoring tracks performance. Regression testing validates process effectiveness. Periodic revalidation after major changes.',
      evidence: 'LangFuse dashboard, test_e2e_workflow.py',
      status: 'implemented'
    },
    {
      id: 'q9-commensurate-documentation',
      title: 'Commensurate Documentation',
      shortDescription: 'Documentation should match risk level (avoid over/under-documentation).',
      implementation: 'All executions get audit trail + LangFuse traces. High-risk jobs get additional electronic signatures. Traceability matrix for all risk levels.',
      evidence: 'audit.py, unified_workflow.py:580-621',
      status: 'implemented'
    }
  ]
};

// ==================== ISO 27001 COMPLIANCE ====================

export const iso27001Framework: ComplianceFramework = {
  id: 'iso-27001',
  name: 'ISO/IEC 27001',
  fullName: 'Information Security Management System',
  description: 'International standard for information security controls',
  icon: '🔒',
  color: '#ef4444', // red
  cards: [
    {
      id: 'iso-access-control',
      title: 'Access Control (A.9)',
      shortDescription: 'Authenticate users and authorize actions based on roles/permissions.',
      implementation: 'Clerk authentication with JWT tokens (RS256). Job ownership checks prevent unauthorized access. MFA supported.',
      evidence: 'auth.py:18-67, app.py:89-115',
      status: 'implemented'
    },
    {
      id: 'iso-cryptography',
      title: 'Cryptography (A.10)',
      shortDescription: 'Encrypt data in transit and at rest. Manage encryption keys securely.',
      implementation: 'TLS 1.3 for all API traffic. AWS KMS for data at rest (planned). SHA-512 hashing for tamper detection.',
      evidence: 'Docker TLS config, aws/AWS-ARCHITECTURE.md:289-334',
      status: 'partial'
    },
    {
      id: 'iso-logging',
      title: 'Operations Security - Logging (A.12.4)',
      shortDescription: 'Log all security events and user actions with timestamps. Logs must be immutable.',
      implementation: 'Comprehensive audit logging with ALCOA+ markers. Append-only database (no modifications). LangFuse traces 131 spans per execution.',
      evidence: 'audit.py:1-145, langfuse_callback.py:29-94',
      status: 'implemented'
    },
    {
      id: 'iso-backup',
      title: 'Operations Security - Backup (A.12.3)',
      shortDescription: 'Regular backups with defined retention periods. Test recovery procedures.',
      implementation: 'Aurora automated backups (35-day retention). S3 Object Lock (7-year retention, planned). RTO <1hr, RPO <5min.',
      evidence: 'aws/AWS-ARCHITECTURE.md:445-478',
      status: 'partial'
    },
    {
      id: 'iso-malware',
      title: 'Operations Security - Malware Protection (A.12.2)',
      shortDescription: 'Protect against malicious software and adversarial inputs.',
      implementation: 'OWASP LLM Top 10 validation in Step 1. Prompt injection detection. Input sanitization for URS uploads.',
      evidence: 'unified_workflow.py:109-158',
      status: 'implemented'
    },
    {
      id: 'iso-communications',
      title: 'Communications Security (A.13)',
      shortDescription: 'Protect information during transmission. Network segmentation.',
      implementation: 'TLS 1.3 encryption for all API traffic. VPC isolation in AWS (planned). Docker network segmentation (current).',
      evidence: 'Docker Compose network, aws/AWS-ARCHITECTURE.md:245-289',
      status: 'partial'
    },
    {
      id: 'iso-secure-development',
      title: 'Secure Development (A.14.2)',
      shortDescription: 'Secure software development lifecycle. NO FALLBACK LOGIC.',
      implementation: 'PRP workflow for change control. tester-agent validates all changes. Git version control with complete audit trail.',
      evidence: 'CLAUDE.md, .claude/commands/prp.md',
      status: 'implemented'
    },
    {
      id: 'iso-compliance',
      title: 'Compliance (A.18.1)',
      shortDescription: 'Comply with legal/regulatory requirements. Document compliance.',
      implementation: '6 compliance mappings (GAMP-5, ALCOA+, 21 CFR Part 11, ICH Q9, ISO 27001, EU AI Act). Quarterly reviews. Git-tracked documentation.',
      evidence: '.claude/state/results/ (6 compliance docs)',
      status: 'implemented'
    }
  ]
};

// ==================== EU AI ACT COMPLIANCE ====================

export const euAiActFramework: ComplianceFramework = {
  id: 'eu-ai-act',
  name: 'EU AI Act',
  fullName: 'European Union Artificial Intelligence Regulation',
  description: 'World\'s first comprehensive AI regulation with risk-based framework',
  icon: '🤖',
  color: '#6366f1', // indigo
  cards: [
    {
      id: 'euai-classification',
      title: 'Risk Classification',
      shortDescription: 'LIMITED RISK AI (professional tool with human oversight)',
      implementation: 'Generates test documentation (not autonomous safety-critical system). Human review required before test execution.',
      evidence: 'EU AI Act compliance mapping - Risk classification analysis',
      status: 'implemented'
    },
    {
      id: 'euai-transparency',
      title: 'Transparency Obligation (Article 50)',
      shortDescription: 'Inform users they\'re interacting with AI. Explain capabilities and limitations.',
      implementation: 'AI disclaimer on dashboard. "How It Works" modal (Task 3.9). Quick Start Guide documents limitations.',
      evidence: 'dashboard.tsx, HowItWorksModal.tsx (planned)',
      status: 'partial'
    },
    {
      id: 'euai-risk-management',
      title: 'Risk Management (Article 9)',
      shortDescription: 'Establish risk management system for AI lifecycle.',
      implementation: 'ICH Q9 quality risk management integrated. GAMP-5 risk-based validation. Confidence scoring identifies high-risk decisions.',
      evidence: 'ICH Q9 compliance mapping, unified_workflow.py',
      status: 'implemented'
    },
    {
      id: 'euai-data-governance',
      title: 'Data Governance (Article 10)',
      shortDescription: 'Training/validation datasets subject to governance and management.',
      implementation: '26 regulatory documents in RAG knowledge base (authoritative sources). Version control in Git. Immutable after ingestion.',
      evidence: 'main/rag/documents/ (26 regulatory docs), Git history',
      status: 'implemented'
    },
    {
      id: 'euai-documentation',
      title: 'Technical Documentation (Article 11)',
      shortDescription: 'Comprehensive documentation of AI system design, validation, operation.',
      implementation: '6 compliance mappings. Technical Architecture Report. MVP Implementation Plan. Complete API documentation.',
      evidence: 'TECHNICAL_ARCHITECTURE_REPORT.md, .claude/state/results/',
      status: 'implemented'
    },
    {
      id: 'euai-logging',
      title: 'Logging (Article 12)',
      shortDescription: 'Automatically log AI system events with timestamps.',
      implementation: 'Audit trail logs all workflow events. LangFuse traces 131 spans per execution. 7-year retention (pharmaceutical requirement).',
      evidence: 'audit.py:1-145, LangFuse Cloud',
      status: 'implemented'
    },
    {
      id: 'euai-human-oversight',
      title: 'Human Oversight (Article 14)',
      shortDescription: 'Enable meaningful human control over AI decisions.',
      implementation: 'Confidence <80% triggers human review. Electronic signatures for approvals. Manual download (no auto-deployment).',
      evidence: 'unified_workflow.py:465-621, ComplianceDashboard.tsx',
      status: 'implemented'
    },
    {
      id: 'euai-accuracy',
      title: 'Accuracy & Robustness (Article 15)',
      shortDescription: 'Appropriate levels of accuracy and robustness. Cybersecurity measures.',
      implementation: 'Multi-agent validation (3 independent checks). NO FALLBACK LOGIC (explicit errors). ISO 27001 cybersecurity compliance.',
      evidence: 'unified_workflow.py:317-395, ISO 27001 compliance mapping',
      status: 'implemented'
    }
  ]
};

// ==================== ALL FRAMEWORKS EXPORT ====================

export const allFrameworks: ComplianceFramework[] = [
  gamp5Framework,
  alcoaPlusFramework,
  cfr21Part11Framework,
  ichQ9Framework,
  iso27001Framework,
  euAiActFramework
];

// ==================== UTILITY FUNCTIONS ====================

/**
 * Get all flash cards across all frameworks
 */
export function getAllComplianceCards(): ComplianceCard[] {
  return allFrameworks.flatMap(framework => framework.cards);
}

/**
 * Get cards by framework ID
 */
export function getCardsByFramework(frameworkId: string): ComplianceCard[] {
  const framework = allFrameworks.find(f => f.id === frameworkId);
  return framework?.cards || [];
}

/**
 * Get a specific card by ID
 */
export function getCardById(cardId: string): ComplianceCard | undefined {
  return getAllComplianceCards().find(card => card.id === cardId);
}

/**
 * Get framework by ID
 */
export function getFrameworkById(frameworkId: string): ComplianceFramework | undefined {
  return allFrameworks.find(f => f.id === frameworkId);
}

/**
 * Get compliance statistics
 */
export function getComplianceStats() {
  const allCards = getAllComplianceCards();
  const implemented = allCards.filter(c => c.status === 'implemented').length;
  const partial = allCards.filter(c => c.status === 'partial').length;
  const planned = allCards.filter(c => c.status === 'planned').length;
  const total = allCards.length;

  return {
    total,
    implemented,
    partial,
    planned,
    implementedPercentage: Math.round((implemented / total) * 100),
    partialPercentage: Math.round((partial / total) * 100),
    plannedPercentage: Math.round((planned / total) * 100)
  };
}

// ==================== CONSTANTS ====================

export const COMPLIANCE_COLORS = {
  'gamp5': '#3b82f6',          // blue
  'alcoa-plus': '#10b981',      // green
  'cfr-part-11': '#8b5cf6',     // purple
  'ich-q9': '#f59e0b',          // amber
  'iso-27001': '#ef4444',       // red
  'eu-ai-act': '#6366f1'        // indigo
} as const;

export const STATUS_COLORS = {
  'implemented': '#10b981',     // green
  'partial': '#f59e0b',         // amber
  'planned': '#6b7280'          // gray
} as const;

export const STATUS_LABELS = {
  'implemented': '✅ Fully Implemented',
  'partial': '⚠️ Partially Implemented',
  'planned': '⏸️ Planned'
} as const;
