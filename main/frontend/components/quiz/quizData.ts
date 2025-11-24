export interface QuizQuestion {
  id: number;
  category: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  question: string;
  options: string[];
  correctAnswer: number; // Index of correct option (0-3)
  explanation: string;
}

export const quizQuestions: QuizQuestion[] = [
  // ===== GAMP-5 Compliance Questions (4 questions) =====
  {
    id: 1,
    category: 'GAMP-5',
    difficulty: 'Easy',
    question: 'What is the primary purpose of GAMP-5 software categorization?',
    options: [
      'To determine the cost of validation activities',
      'To determine the level of validation effort commensurate with risk and complexity',
      'To classify software by vendor reputation',
      'To prioritize software purchases',
    ],
    correctAnswer: 1,
    explanation:
      'GAMP-5 categorization (Categories 1-5) determines how much validation is required based on the software\'s complexity and risk. Category 5 (custom applications) requires comprehensive validation with 25-30 tests, while Category 3 (COTS) requires only 5-10 tests.',
  },
  {
    id: 2,
    category: 'GAMP-5',
    difficulty: 'Medium',
    question:
      'Your pharmaceutical test generation system is a custom-built application with proprietary multi-agent logic. Which GAMP-5 category does it fall under?',
    options: [
      'Category 3 - Non-configured Products',
      'Category 4 - Configured Products',
      'Category 5 - Custom Applications',
      'Category 1 - Infrastructure Software',
    ],
    correctAnswer: 2,
    explanation:
      'Category 5 applies to bespoke software development with custom code. The pharmaceutical test generation app includes custom-built workflows, proprietary multi-agent systems, and bespoke compliance validation logic, requiring the highest level of validation rigor.',
  },
  {
    id: 3,
    category: 'GAMP-5',
    difficulty: 'Hard',
    question:
      'According to GAMP-5, what triggers a requirement for human consultation during automated categorization?',
    options: [
      'Any Category 5 software',
      'Confidence score below 80%',
      'Software from new vendors',
      'All pharmaceutical applications',
    ],
    correctAnswer: 1,
    explanation:
      'When the automated GAMP categorization system produces a confidence score below 80%, it triggers mandatory human oversight. This risk-based approach ensures high-uncertainty decisions receive expert review before proceeding.',
  },
  {
    id: 4,
    category: 'GAMP-5',
    difficulty: 'Medium',
    question: 'Which GAMP-5 appendix addresses the validation of AI/ML systems?',
    options: [
      'Appendix D5 - Critical Thinking',
      'Appendix D8 - Agile Software Development',
      'Appendix D11 - AI/ML Systems',
      'Appendix O - Electronic Production Records',
    ],
    correctAnswer: 2,
    explanation:
      'GAMP-5 Appendix D11 provides guidance specifically for validating AI/ML models, covering explainability, bias detection, model transparency, and validation strategies. The pharmaceutical test generation app complies by using DeepSeek V3 (open-weights model) with complete LangFuse tracing.',
  },

  // ===== ALCOA+ Compliance Questions (4 questions) =====
  {
    id: 5,
    category: 'ALCOA+',
    difficulty: 'Easy',
    question: 'What does the "A" in ALCOA+ stand for?',
    options: ['Automated', 'Attributable', 'Auditable', 'Approved'],
    correctAnswer: 1,
    explanation:
      'Attributable means all records must clearly identify who performed the action, when it was performed, and why. This requires unique user identification (not shared accounts) and secure authentication. The app implements this via Clerk user_id captured in all audit logs and LangFuse traces.',
  },
  {
    id: 6,
    category: 'ALCOA+',
    difficulty: 'Medium',
    question:
      'You discover a test suite file has been modified after generation. Which ALCOA+ principle has been violated?',
    options: ['Legible', 'Contemporaneous', 'Original', 'Available'],
    correctAnswer: 2,
    explanation:
      'The Original principle requires records to be the first (original) recording of data with immutability controls. The app uses SHA-512 hashing to detect any modifications to test suites after creation. If the hash doesn\'t match, a DataIntegrityError is raised.',
  },
  {
    id: 7,
    category: 'ALCOA+',
    difficulty: 'Hard',
    question:
      'Why does the pharmaceutical test generation system use UTC timestamps instead of local time zones?',
    options: [
      'To comply with the Contemporaneous principle',
      'To comply with the Consistent principle',
      'To reduce storage requirements',
      'To improve performance',
    ],
    correctAnswer: 1,
    explanation:
      'The Consistent principle requires standardized formats maintained across time and systems. UTC timestamps (ISO 8601 format) eliminate ambiguity from time zones and daylight saving time changes. All timestamps throughout the system use: datetime.utcnow().isoformat()',
  },
  {
    id: 8,
    category: 'ALCOA+',
    difficulty: 'Medium',
    question:
      'Which ALCOA+ principle is addressed by AWS S3 Object Lock with 7-year retention?',
    options: ['Complete', 'Consistent', 'Enduring', 'Available'],
    correctAnswer: 2,
    explanation:
      'Enduring means records must be retained for their required lifetime (7+ years for pharmaceuticals) and remain accessible throughout. S3 Object Lock prevents deletion and ensures long-term preservation. The YAML format ensures readability across technology changes.',
  },

  // ===== 21 CFR Part 11 Questions (4 questions) =====
  {
    id: 9,
    category: '21 CFR Part 11',
    difficulty: 'Easy',
    question: 'What is the primary focus of 21 CFR Part 11?',
    options: [
      'Laboratory equipment validation',
      'Electronic records and electronic signatures',
      'Clinical trial management',
      'Manufacturing process controls',
    ],
    correctAnswer: 1,
    explanation:
      '21 CFR Part 11 is the FDA regulation establishing criteria for electronic records and electronic signatures to be considered trustworthy, reliable, and equivalent to paper records. It applies to ALL FDA-regulated industries.',
  },
  {
    id: 10,
    category: '21 CFR Part 11',
    difficulty: 'Medium',
    question: 'According to 21 CFR Part 11 §11.10(e), audit trails must be:',
    options: [
      'Generated weekly and reviewed monthly',
      'Secure, computer-generated, time-stamped, and independently record operator actions',
      'Stored on paper as backup',
      'Optional for low-risk systems',
    ],
    correctAnswer: 1,
    explanation:
      'Audit trails must be secure, computer-generated (not manual), time-stamped, and independently record the date/time of operator entries and actions. Critically, audit trails cannot be modified or deleted. The app implements this with append-only database design (no UPDATE/DELETE methods).',
  },
  {
    id: 11,
    category: '21 CFR Part 11',
    difficulty: 'Hard',
    question:
      'An electronic signature under 21 CFR Part 11 must include which of the following?',
    options: [
      'Only the signer\'s name',
      'Printed name, date/time, and meaning of signature (e.g., "approved by")',
      'A scanned image of handwritten signature',
      'Social security number for verification',
    ],
    correctAnswer: 1,
    explanation:
      'Per §11.50, signed electronic records must contain the printed name of signer, date and time of signature, and the meaning of signature. The app implements this with cryptographic signatures including user_name, timestamp, action ("GAMP_CATEGORIZATION_APPROVAL"), and a SHA-256 hash for authenticity.',
  },
  {
    id: 12,
    category: '21 CFR Part 11',
    difficulty: 'Hard',
    question:
      'What did the FDA\'s 2003 Guidance clarify about 21 CFR Part 11 enforcement?',
    options: [
      'All requirements are mandatory without exception',
      'Small companies are exempt',
      'FDA exercises enforcement discretion for some requirements when predicate rules are satisfied',
      'Part 11 no longer applies',
    ],
    correctAnswer: 2,
    explanation:
      'The 2003 FDA Guidance clarified that FDA exercises enforcement discretion for some Part 11 requirements when underlying predicate rules (like ALCOA+, GAMP-5) are satisfied. This means focus compliance on predicate rules PLUS the specific Part 11 requirements FDA actively enforces (access controls, audit trails, signatures).',
  },

  // ===== ICH Q9 Quality Risk Management Questions (4 questions) =====
  {
    id: 13,
    category: 'ICH Q9',
    difficulty: 'Easy',
    question:
      'ICH Q9 states that risk management should address three fundamental questions. Which is NOT one of them?',
    options: [
      'What might go wrong?',
      'What is the likelihood it will go wrong?',
      'How much will it cost to fix?',
      'What are the consequences?',
    ],
    correctAnswer: 2,
    explanation:
      'ICH Q9\'s three fundamental questions are: (1) What might go wrong? (2) What is the likelihood? (3) What are the consequences? Cost is NOT part of the fundamental risk assessment framework. Risk management focuses on patient safety and product quality, not financial considerations.',
  },
  {
    id: 14,
    category: 'ICH Q9',
    difficulty: 'Medium',
    question: 'What does "commensurate effort" mean in the context of ICH Q9?',
    options: [
      'All systems require the same level of documentation',
      'Validation effort should be proportionate to risk, complexity, and impact',
      'Low-risk systems don\'t need validation',
      'High-risk systems should always be avoided',
    ],
    correctAnswer: 1,
    explanation:
      'A core ICH Q9 principle is that the level of effort, formality, and documentation should be commensurate with (proportional to) the level of risk. The app implements this by scaling test count with GAMP category: Category 3 = 5-10 tests, Category 5 = 25-30 tests.',
  },
  {
    id: 15,
    category: 'ICH Q9',
    difficulty: 'Hard',
    question:
      'In the pharmaceutical test generation system, what triggers mandatory human oversight for high-risk decisions?',
    options: [
      'All Category 5 software',
      'Confidence score below 80% OR lack of agent consensus',
      'Any weekend job submission',
      'User requests only',
    ],
    correctAnswer: 1,
    explanation:
      'The system implements ICH Q9 risk evaluation by triggering human consultation when automated categorization produces confidence <80% OR when the three independent agents don\'t reach consensus. This ensures high-uncertainty or high-risk decisions receive expert review.',
  },
  {
    id: 16,
    category: 'ICH Q9',
    difficulty: 'Medium',
    question:
      'Which ICH Q9 risk management tool involves identifying critical control points (CCPs) where hazards must be prevented or reduced?',
    options: [
      'Failure Mode Effects Analysis (FMEA)',
      'Risk Ranking',
      'Hazard Analysis and Critical Control Points (HACCP)',
      'Fault Tree Analysis',
    ],
    correctAnswer: 2,
    explanation:
      'HACCP identifies critical control points in a process. The app implements a HACCP-like approach with 5 CCPs: (1) URS Upload - OWASP validation, (2) GAMP Categorization - confidence scoring, (3) Multi-Agent Validation - consensus checking, (4) Human Consultation - expert review, (5) ALCOA+ Validation - data integrity verification.',
  },

  // ===== ISO 27001 Information Security Questions (4 questions) =====
  {
    id: 17,
    category: 'ISO 27001',
    difficulty: 'Easy',
    question: 'What are the three core objectives of ISO/IEC 27001?',
    options: [
      'Speed, Cost, Quality',
      'Confidentiality, Integrity, Availability',
      'Access, Backup, Compliance',
      'Encryption, Authentication, Authorization',
    ],
    correctAnswer: 1,
    explanation:
      'ISO 27001\'s core objectives are: Confidentiality (information accessible only to authorized individuals), Integrity (safeguard accuracy and completeness), and Availability (authorized users have access when needed). These three pillars form the foundation of information security management.',
  },
  {
    id: 18,
    category: 'ISO 27001',
    difficulty: 'Medium',
    question:
      'Which ISO 27001 Annex A control requires "secure, computer-generated, time-stamped audit trails"?',
    options: [
      'A.9.2 - User access management',
      'A.10.1 - Cryptographic controls',
      'A.12.4 - Logging and monitoring',
      'A.18.1 - Compliance with legal requirements',
    ],
    correctAnswer: 2,
    explanation:
      'A.12.4 (Logging and monitoring) requires comprehensive logging of security events and user actions with timestamps. This control directly maps to ALCOA+ "Contemporaneous" and "Original" principles. The app implements this with append-only audit logs and LangFuse traces capturing 131 spans per execution.',
  },
  {
    id: 19,
    category: 'ISO 27001',
    difficulty: 'Hard',
    question:
      'Why does the pharmaceutical test generation system implement "NO FALLBACK LOGIC" as a security control?',
    options: [
      'To improve performance',
      'To reduce code complexity',
      'To ensure explicit failures rather than masking security vulnerabilities',
      'To comply with GDPR requirements',
    ],
    correctAnswer: 2,
    explanation:
      'NO FALLBACK LOGIC is an ISO 27001 A.14.2 (Secure development) control. By explicitly failing and raising errors with full stack traces instead of using default values or fallbacks, the system ensures security vulnerabilities are never masked. This prevents artificial confidence scores or deceptive logic that could hide problems.',
  },
  {
    id: 20,
    category: 'ISO 27001',
    difficulty: 'Hard',
    question:
      'Which ISO 27001 control addresses protection from malicious software and adversarial inputs in LLM-based systems?',
    options: [
      'A.9.4 - System access control',
      'A.10.2 - Cryptographic keys',
      'A.12.2 - Protection from malware',
      'A.13.1 - Network security management',
    ],
    correctAnswer: 2,
    explanation:
      'A.12.2 (Protection from malware) includes protection against adversarial inputs. The app implements this through OWASP LLM Top 10 validation in Step 1 of the workflow, checking for: prompt injection, insecure output handling, training data poisoning, sensitive information disclosure, and excessive agency.',
  },
];
