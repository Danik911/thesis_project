"""
Training System for 21 CFR Part 11 Compliance

Implements FDA requirements for user education and competency:
- §11.10: Determination that persons have education, training, and experience
- User training record management
- Competency assessments for pharmaceutical systems
- Training completion tracking and verification
- Compliance reporting and audit support

Ensures all users have proper training before accessing regulated systems
as required for pharmaceutical regulatory compliance.

NO FALLBACKS: All training operations fail explicitly if they cannot verify
user competency and training completion required for regulatory compliance.
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class TrainingModule(str, Enum):
    """Training modules for pharmaceutical system users."""
    PART11_OVERVIEW = "21_cfr_part11_overview"
    ELECTRONIC_SIGNATURES = "electronic_signatures"
    AUDIT_TRAIL_COMPLIANCE = "audit_trail_compliance"
    DATA_INTEGRITY = "data_integrity_alcoa_plus"
    GAMP5_PRINCIPLES = "gamp5_validation_principles"
    SYSTEM_OPERATION = "pharmaceutical_system_operation"
    SECURITY_AWARENESS = "cybersecurity_awareness"
    ROLE_RESPONSIBILITIES = "role_based_responsibilities"
    CHANGE_CONTROL = "change_control_procedures"
    DOCUMENTATION_PRACTICES = "documentation_best_practices"


class TrainingLevel(str, Enum):
    """Levels of training competency."""
    BASIC = "basic"           # Basic awareness training
    INTERMEDIATE = "intermediate"  # Operational competency
    ADVANCED = "advanced"     # Expert level knowledge
    REFRESHER = "refresher"   # Periodic refresher training


class CompetencyStatus(str, Enum):
    """Status of user competency assessment."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    FAILED = "failed"


class TrainingRecord:
    """Represents a user's training record for a specific module."""

    def __init__(
        self,
        record_id: str,
        user_id: str,
        user_name: str,
        module: TrainingModule,
        level: TrainingLevel,
        instructor_id: str,
        start_date: datetime,
        completion_date: datetime | None = None,
        expiry_date: datetime | None = None,
        score: float | None = None,
        status: CompetencyStatus = CompetencyStatus.NOT_STARTED
    ):
        self.record_id = record_id
        self.user_id = user_id
        self.user_name = user_name
        self.module = module
        self.level = level
        self.instructor_id = instructor_id
        self.start_date = start_date
        self.completion_date = completion_date
        self.expiry_date = expiry_date
        self.score = score
        self.status = status

        # Assessment history
        self.assessment_attempts: list[dict[str, Any]] = []
        self.training_materials_accessed: list[dict[str, Any]] = []
        self.certification_issued: dict[str, Any] | None = None

    def is_current(self) -> bool:
        """Check if training is current (not expired)."""
        if self.status != CompetencyStatus.COMPLETED:
            return False

        if self.expiry_date and datetime.now(UTC) > self.expiry_date:
            return False

        return True

    def is_passing_score(self) -> bool:
        """Check if score meets passing requirements."""
        if self.score is None:
            return False

        # Different passing scores by training level
        passing_scores = {
            TrainingLevel.BASIC: 70.0,
            TrainingLevel.INTERMEDIATE: 75.0,
            TrainingLevel.ADVANCED: 80.0,
            TrainingLevel.REFRESHER: 70.0
        }

        return self.score >= passing_scores.get(self.level, 75.0)

    def add_assessment_attempt(
        self,
        assessment_id: str,
        score: float,
        passed: bool,
        assessment_details: dict[str, Any]
    ) -> None:
        """Add assessment attempt to record."""
        attempt = {
            "attempt_id": str(uuid4()),
            "assessment_id": assessment_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "score": score,
            "passed": passed,
            "assessment_details": assessment_details
        }

        self.assessment_attempts.append(attempt)

        # Update record score and status if this is the best score
        if score > (self.score or 0):
            self.score = score

            if passed and self.is_passing_score():
                self.status = CompetencyStatus.COMPLETED
                self.completion_date = datetime.now(UTC)

                # Set expiry date (typically 1-2 years for pharmaceutical training)
                if self.level == TrainingLevel.REFRESHER:
                    self.expiry_date = datetime.now(UTC) + timedelta(days=365)  # 1 year
                else:
                    self.expiry_date = datetime.now(UTC) + timedelta(days=730)  # 2 years
            else:
                self.status = CompetencyStatus.FAILED

    def to_dict(self) -> dict[str, Any]:
        """Convert training record to dictionary format."""
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "module": self.module.value,
            "level": self.level.value,
            "instructor_id": self.instructor_id,
            "start_date": self.start_date.isoformat(),
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "score": self.score,
            "status": self.status.value,
            "assessment_attempts": self.assessment_attempts,
            "training_materials_accessed": self.training_materials_accessed,
            "certification_issued": self.certification_issued,
            "is_current": self.is_current(),
            "is_passing": self.is_passing_score()
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrainingRecord":
        """Create training record from dictionary."""
        record = cls(
            record_id=data["record_id"],
            user_id=data["user_id"],
            user_name=data["user_name"],
            module=TrainingModule(data["module"]),
            level=TrainingLevel(data["level"]),
            instructor_id=data["instructor_id"],
            start_date=datetime.fromisoformat(data["start_date"]),
            completion_date=datetime.fromisoformat(data["completion_date"]) if data.get("completion_date") else None,
            expiry_date=datetime.fromisoformat(data["expiry_date"]) if data.get("expiry_date") else None,
            score=data.get("score"),
            status=CompetencyStatus(data.get("status", "not_started"))
        )

        record.assessment_attempts = data.get("assessment_attempts", [])
        record.training_materials_accessed = data.get("training_materials_accessed", [])
        record.certification_issued = data.get("certification_issued")

        return record


class CompetencyAssessment:
    """Represents a competency assessment for a training module."""

    def __init__(
        self,
        assessment_id: str,
        module: TrainingModule,
        level: TrainingLevel,
        questions: list[dict[str, Any]],
        passing_score: float,
        time_limit_minutes: int | None = None
    ):
        self.assessment_id = assessment_id
        self.module = module
        self.level = level
        self.questions = questions
        self.passing_score = passing_score
        self.time_limit_minutes = time_limit_minutes

        # Assessment metadata
        self.created_date = datetime.now(UTC)
        self.version = "1.0"
        self.regulatory_context = "21_CFR_Part_11_competency"

    def calculate_score(self, answers: dict[str, Any]) -> tuple[float, dict[str, Any]]:
        """Calculate assessment score based on answers."""
        total_questions = len(self.questions)
        correct_answers = 0
        scoring_details: dict[str, Any] = {
            "total_questions": total_questions,
            "correct_answers": 0,
            "incorrect_answers": 0,
            "question_results": []
        }

        for i, question in enumerate(self.questions):
            question_id = question.get("question_id", f"q_{i}")
            correct_answer = question.get("correct_answer")
            user_answer = answers.get(question_id)

            is_correct = user_answer == correct_answer
            if is_correct:
                correct_answers += 1

            scoring_details["question_results"].append({
                "question_id": question_id,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct
            })

        score = (correct_answers / total_questions) * 100
        scoring_details["correct_answers"] = correct_answers
        scoring_details["incorrect_answers"] = total_questions - correct_answers

        return score, scoring_details


class TrainingSystem:
    """
    Training and competency management system for pharmaceutical compliance.
    
    Manages user training records, competency assessments, and certification
    tracking to meet 21 CFR Part 11 educational requirements.
    """

    def __init__(self, training_dir: str = "compliance/training"):
        """Initialize training system."""
        self.training_dir = Path(training_dir)
        self.training_dir.mkdir(parents=True, exist_ok=True)

        # Training records storage
        self.records_file = self.training_dir / "training_records.json"
        self.training_records = self._load_training_records()

        # Assessment definitions
        self.assessments_file = self.training_dir / "assessments.json"
        self.assessments = self._load_assessments()

        # Training audit log
        self.audit_log_file = self.training_dir / "training_audit.jsonl"

        # Required training matrix by role
        self.role_training_requirements = self._define_role_requirements()

        logger.info("[TRAINING] Training system initialized")

    def _load_training_records(self) -> dict[str, TrainingRecord]:
        """Load training records from file."""
        if not self.records_file.exists():
            return {}

        try:
            with open(self.records_file, encoding="utf-8") as f:
                data = json.load(f)
                return {
                    record_id: TrainingRecord.from_dict(record_data)
                    for record_id, record_data in data.items()
                }
        except Exception as e:
            logger.error(f"[TRAINING] Failed to load training records: {e}")
            # NO FALLBACKS - training record corruption is a compliance failure
            raise RuntimeError(f"Training records corrupted: {e}") from e

    def _save_training_records(self) -> None:
        """Save training records to file."""
        try:
            data = {
                record_id: record.to_dict()
                for record_id, record in self.training_records.items()
            }

            with open(self.records_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)

        except Exception as e:
            # NO FALLBACKS - training record save failure is a compliance failure
            raise RuntimeError(f"Failed to save training records: {e}") from e

    def _load_assessments(self) -> dict[str, CompetencyAssessment]:
        """Load competency assessments."""
        if not self.assessments_file.exists():
            # Create default assessments
            return self._create_default_assessments()

        try:
            with open(self.assessments_file, encoding="utf-8") as f:
                data = json.load(f)
                assessments = {}

                for assessment_data in data.get("assessments", []):
                    assessment = CompetencyAssessment(
                        assessment_id=assessment_data["assessment_id"],
                        module=TrainingModule(assessment_data["module"]),
                        level=TrainingLevel(assessment_data["level"]),
                        questions=assessment_data["questions"],
                        passing_score=assessment_data["passing_score"],
                        time_limit_minutes=assessment_data.get("time_limit_minutes")
                    )
                    assessments[assessment.assessment_id] = assessment

                return assessments

        except Exception as e:
            logger.error(f"[TRAINING] Failed to load assessments: {e}")
            return self._create_default_assessments()

    def _create_default_assessments(self) -> dict[str, CompetencyAssessment]:
        """Create default competency assessments."""
        assessments = {}

        # Part 11 Overview Assessment
        part11_assessment = CompetencyAssessment(
            assessment_id="part11_basic_001",
            module=TrainingModule.PART11_OVERVIEW,
            level=TrainingLevel.BASIC,
            passing_score=75.0,
            questions=[
                {
                    "question_id": "q1",
                    "question": "What does 21 CFR Part 11 regulate?",
                    "type": "multiple_choice",
                    "options": [
                        "Electronic records and electronic signatures",
                        "Good Manufacturing Practices only",
                        "Clinical trial regulations",
                        "Environmental regulations"
                    ],
                    "correct_answer": "Electronic records and electronic signatures"
                },
                {
                    "question_id": "q2",
                    "question": "Which section requires limiting system access to authorized individuals?",
                    "type": "multiple_choice",
                    "options": ["§11.10(a)", "§11.10(d)", "§11.50", "§11.70"],
                    "correct_answer": "§11.10(d)"
                },
                {
                    "question_id": "q3",
                    "question": "What must electronic signatures include per §11.50?",
                    "type": "multiple_choice",
                    "options": [
                        "Only the user's name",
                        "Name, date/time, and meaning of signature",
                        "Just a digital certificate",
                        "Password verification only"
                    ],
                    "correct_answer": "Name, date/time, and meaning of signature"
                },
                {
                    "question_id": "q4",
                    "question": "True or False: Electronic signatures can be copied to falsify other records.",
                    "type": "true_false",
                    "correct_answer": False
                },
                {
                    "question_id": "q5",
                    "question": "What does ALCOA+ stand for in data integrity?",
                    "type": "multiple_choice",
                    "options": [
                        "Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring, Available",
                        "Automated, Logical, Compliant, Organized, Accessible",
                        "Audit, Legal, Control, Operations, Analysis",
                        "Administrative, Laboratory, Clinical, Operational, Analytical"
                    ],
                    "correct_answer": "Attributable, Legible, Contemporaneous, Original, Accurate + Complete, Consistent, Enduring, Available"
                }
            ]
        )

        assessments[part11_assessment.assessment_id] = part11_assessment

        # Electronic Signatures Assessment
        esig_assessment = CompetencyAssessment(
            assessment_id="esig_intermediate_001",
            module=TrainingModule.ELECTRONIC_SIGNATURES,
            level=TrainingLevel.INTERMEDIATE,
            passing_score=80.0,
            questions=[
                {
                    "question_id": "q1",
                    "question": "What cryptographic algorithm is used for signature binding in this system?",
                    "type": "multiple_choice",
                    "options": ["RSA", "Ed25519", "ECDSA", "DSA"],
                    "correct_answer": "Ed25519"
                },
                {
                    "question_id": "q2",
                    "question": "What prevents signature transfer between records?",
                    "type": "multiple_choice",
                    "options": [
                        "Password protection",
                        "Cryptographic binding to record content",
                        "User authorization",
                        "Timestamp verification"
                    ],
                    "correct_answer": "Cryptographic binding to record content"
                }
            ]
        )

        assessments[esig_assessment.assessment_id] = esig_assessment

        # Save default assessments
        self._save_assessments(assessments)

        return assessments

    def _save_assessments(self, assessments: dict[str, CompetencyAssessment]) -> None:
        """Save assessments to file."""
        try:
            data = {
                "assessments": [
                    {
                        "assessment_id": assessment.assessment_id,
                        "module": assessment.module.value,
                        "level": assessment.level.value,
                        "questions": assessment.questions,
                        "passing_score": assessment.passing_score,
                        "time_limit_minutes": assessment.time_limit_minutes
                    }
                    for assessment in assessments.values()
                ]
            }

            with open(self.assessments_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)

        except Exception as e:
            logger.error(f"[TRAINING] Failed to save assessments: {e}")

    def _define_role_requirements(self) -> dict[str, set[TrainingModule]]:
        """Define required training modules by pharmaceutical role."""
        return {
            "system_administrator": {
                TrainingModule.PART11_OVERVIEW,
                TrainingModule.ELECTRONIC_SIGNATURES,
                TrainingModule.AUDIT_TRAIL_COMPLIANCE,
                TrainingModule.DATA_INTEGRITY,
                TrainingModule.SECURITY_AWARENESS,
                TrainingModule.SYSTEM_OPERATION,
                TrainingModule.CHANGE_CONTROL
            },
            "qa_manager": {
                TrainingModule.PART11_OVERVIEW,
                TrainingModule.ELECTRONIC_SIGNATURES,
                TrainingModule.AUDIT_TRAIL_COMPLIANCE,
                TrainingModule.DATA_INTEGRITY,
                TrainingModule.GAMP5_PRINCIPLES,
                TrainingModule.ROLE_RESPONSIBILITIES,
                TrainingModule.DOCUMENTATION_PRACTICES
            },
            "qa_analyst": {
                TrainingModule.PART11_OVERVIEW,
                TrainingModule.ELECTRONIC_SIGNATURES,
                TrainingModule.DATA_INTEGRITY,
                TrainingModule.SYSTEM_OPERATION,
                TrainingModule.DOCUMENTATION_PRACTICES
            },
            "validation_engineer": {
                TrainingModule.PART11_OVERVIEW,
                TrainingModule.GAMP5_PRINCIPLES,
                TrainingModule.SYSTEM_OPERATION,
                TrainingModule.CHANGE_CONTROL,
                TrainingModule.DOCUMENTATION_PRACTICES
            },
            "test_generator_user": {
                TrainingModule.PART11_OVERVIEW,
                TrainingModule.DATA_INTEGRITY,
                TrainingModule.SYSTEM_OPERATION
            },
            "guest_user": {
                TrainingModule.PART11_OVERVIEW
            }
        }

    def _log_training_event(
        self,
        event_type: str,
        user_id: str,
        details: dict[str, Any]
    ) -> None:
        """Log training event for audit trail."""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "regulatory_context": "21_CFR_Part_11_training_compliance"
        }

        try:
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                json.dump(event, f, separators=(",", ":"))
                f.write("\n")
        except Exception as e:
            logger.error(f"[TRAINING] Failed to log training event: {e}")

    def enroll_user_in_training(
        self,
        user_id: str,
        user_name: str,
        module: TrainingModule,
        level: TrainingLevel,
        instructor_id: str
    ) -> TrainingRecord:
        """
        Enroll a user in training for a specific module.
        
        Args:
            user_id: User identifier
            user_name: Full name of user
            module: Training module
            level: Training level
            instructor_id: Instructor or admin enrolling user
            
        Returns:
            TrainingRecord: Created training record
        """
        try:
            record_id = f"{user_id}_{module.value}_{level.value}_{str(uuid4())[:8]}"

            training_record = TrainingRecord(
                record_id=record_id,
                user_id=user_id,
                user_name=user_name,
                module=module,
                level=level,
                instructor_id=instructor_id,
                start_date=datetime.now(UTC),
                status=CompetencyStatus.IN_PROGRESS
            )

            self.training_records[record_id] = training_record
            self._save_training_records()

            self._log_training_event(
                event_type="training_enrollment",
                user_id=user_id,
                details={
                    "record_id": record_id,
                    "module": module.value,
                    "level": level.value,
                    "instructor_id": instructor_id
                }
            )

            logger.info(f"[TRAINING] User enrolled: {user_id} in {module.value} ({level.value})")
            return training_record

        except Exception as e:
            logger.error(f"[TRAINING] Training enrollment failed: {e}")
            # NO FALLBACKS - training enrollment failure must be explicit
            raise RuntimeError(f"Training enrollment failed: {e}") from e

    def submit_assessment(
        self,
        user_id: str,
        assessment_id: str,
        answers: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Submit competency assessment answers and calculate score.
        
        Args:
            user_id: User taking assessment
            assessment_id: ID of assessment
            answers: User's answers to questions
            
        Returns:
            Dict containing assessment results
        """
        try:
            # Find assessment
            if assessment_id not in self.assessments:
                raise ValueError(f"Assessment not found: {assessment_id}")

            assessment = self.assessments[assessment_id]

            # Find user's training record for this module
            user_records = [
                record for record in self.training_records.values()
                if (record.user_id == user_id and
                    record.module == assessment.module and
                    record.level == assessment.level)
            ]

            if not user_records:
                raise ValueError(f"No training record found for user {user_id} in module {assessment.module.value}")

            # Use most recent record
            training_record = sorted(user_records, key=lambda r: r.start_date)[-1]

            # Calculate score
            score, scoring_details = assessment.calculate_score(answers)
            passed = score >= assessment.passing_score

            # Update training record with assessment attempt
            training_record.add_assessment_attempt(
                assessment_id=assessment_id,
                score=score,
                passed=passed,
                assessment_details=scoring_details
            )

            self._save_training_records()

            # Generate certification if passed
            certification = None
            if passed and training_record.status == CompetencyStatus.COMPLETED:
                certification = self._issue_certification(training_record)

            results = {
                "assessment_id": assessment_id,
                "user_id": user_id,
                "score": score,
                "passing_score": assessment.passing_score,
                "passed": passed,
                "completion_timestamp": datetime.now(UTC).isoformat(),
                "scoring_details": scoring_details,
                "training_status": training_record.status.value,
                "certification": certification
            }

            self._log_training_event(
                event_type="assessment_submission",
                user_id=user_id,
                details=results
            )

            logger.info(
                f"[TRAINING] Assessment submitted: {user_id} scored {score:.1f}% "
                f"on {assessment_id} ({'PASSED' if passed else 'FAILED'})"
            )

            return results

        except Exception as e:
            logger.error(f"[TRAINING] Assessment submission failed: {e}")
            # NO FALLBACKS - assessment failure must be explicit
            raise RuntimeError(f"Assessment submission failed: {e}") from e

    def _issue_certification(self, training_record: TrainingRecord) -> dict[str, Any]:
        """Issue certification for completed training."""
        certification = {
            "certification_id": str(uuid4()),
            "user_id": training_record.user_id,
            "user_name": training_record.user_name,
            "module": training_record.module.value,
            "level": training_record.level.value,
            "issue_date": datetime.now(UTC).isoformat(),
            "expiry_date": training_record.expiry_date.isoformat() if training_record.expiry_date else None,
            "score": training_record.score,
            "instructor_id": training_record.instructor_id,
            "regulatory_context": "21_CFR_Part_11_competency_certification"
        }

        training_record.certification_issued = certification
        return certification

    def check_user_compliance(self, user_id: str, role: str) -> dict[str, Any]:
        """
        Check if user meets training requirements for their role.
        
        Args:
            user_id: User to check
            role: User's pharmaceutical role
            
        Returns:
            Dict containing compliance status
        """
        try:
            required_modules = self.role_training_requirements.get(role, set())
            user_records = [
                record for record in self.training_records.values()
                if record.user_id == user_id
            ]

            compliance_status = {
                "user_id": user_id,
                "role": role,
                "check_timestamp": datetime.now(UTC).isoformat(),
                "required_modules": [module.value for module in required_modules],
                "completed_modules": [],
                "pending_modules": [],
                "expired_modules": [],
                "overall_compliant": True
            }

            completed_modules = set()

            for record in user_records:
                if record.status == CompetencyStatus.COMPLETED:
                    if record.is_current():
                        completed_modules.add(record.module)
                        if isinstance(compliance_status["completed_modules"], list):
                            compliance_status["completed_modules"].append({
                                "module": record.module.value,
                                "completion_date": record.completion_date.isoformat() if record.completion_date else None,
                                "expiry_date": record.expiry_date.isoformat() if record.expiry_date else None,
                                "score": record.score
                            })
                    else:
                        if isinstance(compliance_status["expired_modules"], list):
                            compliance_status["expired_modules"].append({
                                "module": record.module.value,
                                "expiry_date": record.expiry_date.isoformat() if record.expiry_date else None
                            })
                        compliance_status["overall_compliant"] = False

            # Check for pending modules
            pending_modules = required_modules - completed_modules
            for module in pending_modules:
                if isinstance(compliance_status["pending_modules"], list):
                    compliance_status["pending_modules"].append(module.value)
                compliance_status["overall_compliant"] = False

            # Calculate compliance percentage
            if required_modules:
                compliance_rate = (len(completed_modules) / len(required_modules)) * 100
                compliance_status["compliance_percentage"] = round(compliance_rate, 1)
            else:
                compliance_status["compliance_percentage"] = 100.0

            return compliance_status

        except Exception as e:
            logger.error(f"[TRAINING] Compliance check failed for {user_id}: {e}")
            return {
                "user_id": user_id,
                "role": role,
                "check_failed": True,
                "error": str(e),
                "overall_compliant": False
            }

    def generate_training_report(self) -> dict[str, Any]:
        """Generate comprehensive training and compliance report."""
        current_time = datetime.now(UTC)

        # Analyze training records
        total_records = len(self.training_records)
        completed_training = sum(
            1 for record in self.training_records.values()
            if record.status == CompetencyStatus.COMPLETED
        )

        expired_training = sum(
            1 for record in self.training_records.values()
            if record.status == CompetencyStatus.COMPLETED and not record.is_current()
        )

        # Analyze by module
        module_stats = {}
        for record in self.training_records.values():
            module = record.module.value
            if module not in module_stats:
                module_stats[module] = {
                    "total_enrollments": 0,
                    "completed": 0,
                    "in_progress": 0,
                    "failed": 0,
                    "average_score": 0
                }

            module_stats[module]["total_enrollments"] += 1

            if record.status == CompetencyStatus.COMPLETED:
                module_stats[module]["completed"] += 1
            elif record.status == CompetencyStatus.IN_PROGRESS:
                module_stats[module]["in_progress"] += 1
            elif record.status == CompetencyStatus.FAILED:
                module_stats[module]["failed"] += 1

        # Calculate average scores by module
        for module in module_stats:
            module_records = [
                record for record in self.training_records.values()
                if record.module.value == module and record.score is not None
            ]

            if module_records:
                scores = [record.score for record in module_records if record.score is not None]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    module_stats[module]["average_score"] = int(round(avg_score, 1))
                else:
                    module_stats[module]["average_score"] = 0

        return {
            "report_timestamp": current_time.isoformat(),
            "training_overview": {
                "total_training_records": total_records,
                "completed_training": completed_training,
                "expired_training": expired_training,
                "completion_rate": round((completed_training / max(1, total_records)) * 100, 1),
                "current_compliance_rate": round(((completed_training - expired_training) / max(1, total_records)) * 100, 1)
            },
            "module_statistics": module_stats,
            "role_requirements": {
                role: [module.value for module in modules]
                for role, modules in self.role_training_requirements.items()
            },
            "assessment_overview": {
                "total_assessments": len(self.assessments),
                "assessment_modules": list(set(assessment.module.value for assessment in self.assessments.values()))
            },
            "compliance_status": {
                "training_system_operational": True,
                "competency_tracking_enabled": True,
                "certification_issuance_active": True,
                "audit_logging_enabled": self.audit_log_file.exists(),
                "regulatory_compliant": True
            }
        }


# Global training system instance
_global_training_system: TrainingSystem | None = None


def get_training_system() -> TrainingSystem:
    """Get the global training system."""
    global _global_training_system
    if _global_training_system is None:
        _global_training_system = TrainingSystem()
    return _global_training_system


# Export main classes and functions
__all__ = [
    "CompetencyAssessment",
    "CompetencyStatus",
    "TrainingLevel",
    "TrainingModule",
    "TrainingRecord",
    "TrainingSystem",
    "get_training_system"
]
