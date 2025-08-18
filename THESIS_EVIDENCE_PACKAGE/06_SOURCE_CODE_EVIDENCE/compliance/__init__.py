"""
21 CFR Part 11 Compliance Implementation

This module provides operational compliance controls for pharmaceutical
systems as required by 21 CFR Part 11 Electronic Records/Electronic Signatures.

Implements the enforced sections of Part 11:
- Electronic signature binding to records (§11.50-§11.70)
- Role-based access control (§11.10(d))
- Multi-factor authentication (operational system checks)
- WORM storage for record integrity (§11.10(c))
- User training and competency tracking (§11.10)
- System validation protocols (§11.10(a))

All controls fail explicitly rather than using fallback mechanisms
to ensure regulatory compliance integrity.
"""

from .mfa_auth import AuthenticationResult, MultiFactorAuth, get_mfa_service
from .part11_signatures import (
    ElectronicSignatureBinding,
    SignatureManifest,
    SignatureMeaning,
    get_signature_service,
)
from .rbac_system import (
    Permission,
    PharmaceuticalRole,
    RoleBasedAccessControl,
    get_rbac_system,
)
from .training_system import (
    CompetencyAssessment,
    TrainingLevel,
    TrainingModule,
    TrainingRecord,
    TrainingSystem,
    get_training_system,
)
from .validation_framework import (
    ValidationFramework,
    ValidationPhase,
    ValidationProtocol,
    ValidationResult,
    get_validation_framework,
)
from .worm_storage import RecordType, WormRecord, WormStorage, get_worm_storage

__all__ = [
    # Electronic Signatures
    "ElectronicSignatureBinding",
    "SignatureMeaning",
    "SignatureManifest",
    "get_signature_service",

    # RBAC System
    "PharmaceuticalRole",
    "Permission",
    "RoleBasedAccessControl",
    "get_rbac_system",

    # Multi-Factor Authentication
    "MultiFactorAuth",
    "AuthenticationResult",
    "get_mfa_service",

    # WORM Storage
    "WormStorage",
    "WormRecord",
    "RecordType",
    "get_worm_storage",

    # Training System
    "TrainingSystem",
    "TrainingRecord",
    "CompetencyAssessment",
    "TrainingModule",
    "TrainingLevel",
    "get_training_system",

    # Validation Framework
    "ValidationFramework",
    "ValidationProtocol",
    "ValidationResult",
    "ValidationPhase",
    "get_validation_framework",
]
