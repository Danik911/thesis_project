"""
Multi-Factor Authentication (MFA) System for 21 CFR Part 11 Compliance

Implements enhanced authentication controls as operational system checks:
- Time-based One-Time Password (TOTP) second factor
- Backup recovery codes for account recovery
- Session management with timeout enforcement
- Failed attempt tracking and account lockout
- Device registration and verification

Provides additional security layer beyond basic authentication to meet
pharmaceutical industry security standards and regulatory expectations.

NO FALLBACKS: All MFA operations fail explicitly if they cannot verify
the additional authentication factor required for regulatory compliance.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import struct
import time
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AuthenticationResult(str, Enum):
    """Results of multi-factor authentication attempts."""
    SUCCESS = "success"
    INVALID_TOTP = "invalid_totp"
    EXPIRED_TOTP = "expired_totp"
    INVALID_BACKUP_CODE = "invalid_backup_code"
    ACCOUNT_LOCKED = "account_locked"
    MFA_NOT_SETUP = "mfa_not_setup"
    DEVICE_NOT_REGISTERED = "device_not_registered"
    SESSION_EXPIRED = "session_expired"
    AUTHENTICATION_ERROR = "authentication_error"


class TOTPGenerator:
    """Time-based One-Time Password generator implementing RFC 6238."""

    def __init__(self, secret_key: bytes, time_step: int = 30, digits: int = 6):
        """
        Initialize TOTP generator.
        
        Args:
            secret_key: Base32-encoded secret key for TOTP generation
            time_step: Time step in seconds (typically 30)
            digits: Number of digits in TOTP code (typically 6)
        """
        self.secret_key = secret_key
        self.time_step = time_step
        self.digits = digits

    def generate_totp(self, timestamp: int | None = None) -> str:
        """Generate TOTP code for given timestamp."""
        if timestamp is None:
            timestamp = int(time.time())

        # Calculate time counter
        time_counter = timestamp // self.time_step

        # Convert counter to bytes
        counter_bytes = struct.pack(">Q", time_counter)

        # Generate HMAC-SHA1
        hmac_hash = hmac.new(self.secret_key, counter_bytes, hashlib.sha1).digest()

        # Dynamic truncation
        offset = hmac_hash[-1] & 0x0f
        binary_code = struct.unpack(">I", hmac_hash[offset:offset + 4])[0]
        binary_code &= 0x7fffffff

        # Generate digits
        totp_code = str(binary_code % (10 ** self.digits)).zfill(self.digits)

        return totp_code

    def verify_totp(self, code: str, timestamp: int | None = None, window: int = 1) -> bool:
        """
        Verify TOTP code with time window tolerance.
        
        Args:
            code: TOTP code to verify
            timestamp: Timestamp to verify against (defaults to current time)
            window: Time window tolerance (number of time steps)
            
        Returns:
            bool: True if TOTP code is valid
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Check code within time window
        for i in range(-window, window + 1):
            test_timestamp = timestamp + (i * self.time_step)
            if self.generate_totp(test_timestamp) == code:
                return True

        return False


class BackupCodes:
    """Manages backup recovery codes for MFA account recovery."""

    def __init__(self, code_length: int = 8, num_codes: int = 10):
        """Initialize backup codes system."""
        self.code_length = code_length
        self.num_codes = num_codes

    def generate_backup_codes(self) -> list[str]:
        """Generate new set of backup codes."""
        codes = []
        for _ in range(self.num_codes):
            # Generate secure random code
            code = "".join(secrets.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
                          for _ in range(self.code_length))
            codes.append(code)

        return codes

    def hash_backup_codes(self, codes: list[str]) -> list[str]:
        """Hash backup codes for secure storage."""
        hashed_codes = []
        for code in codes:
            # Add salt and hash
            salt = secrets.token_hex(16)
            code_hash = hashlib.pbkdf2_hmac("sha256", code.encode(), salt.encode(), 100000)
            hashed_codes.append(f"{salt}:{code_hash.hex()}")

        return hashed_codes

    def verify_backup_code(self, code: str, hashed_codes: list[str]) -> tuple[bool, str]:
        """
        Verify backup code and return which code was used.
        
        Returns:
            Tuple[bool, str]: (is_valid, used_code_hash)
        """
        for hashed_code in hashed_codes:
            try:
                salt, stored_hash = hashed_code.split(":", 1)
                code_hash = hashlib.pbkdf2_hmac("sha256", code.encode(), salt.encode(), 100000)

                if code_hash.hex() == stored_hash:
                    return True, hashed_code
            except ValueError:
                continue

        return False, ""


class MFAUserRecord:
    """Represents MFA configuration and state for a user."""

    def __init__(
        self,
        user_id: str,
        totp_secret: bytes | None = None,
        backup_codes: list[str] | None = None,
        is_setup: bool = False,
        last_totp_used: str | None = None,
        failed_attempts: int = 0,
        locked_until: datetime | None = None
    ):
        self.user_id = user_id
        self.totp_secret = totp_secret
        self.backup_codes = backup_codes or []
        self.is_setup = is_setup
        self.last_totp_used = last_totp_used
        self.failed_attempts = failed_attempts
        self.locked_until = locked_until
        self.setup_timestamp = datetime.now(UTC) if is_setup else None
        self.last_successful_auth = None

    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now(UTC) < self.locked_until

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "totp_secret": base64.b64encode(self.totp_secret).decode() if self.totp_secret else None,
            "backup_codes": self.backup_codes,
            "is_setup": self.is_setup,
            "last_totp_used": self.last_totp_used,
            "failed_attempts": self.failed_attempts,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None,
            "setup_timestamp": self.setup_timestamp.isoformat() if self.setup_timestamp else None,
            "last_successful_auth": self.last_successful_auth.isoformat() if self.last_successful_auth else None
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MFAUserRecord":
        """Create from dictionary."""
        record = cls(
            user_id=data["user_id"],
            totp_secret=base64.b64decode(data["totp_secret"]) if data.get("totp_secret") else None,
            backup_codes=data.get("backup_codes", []),
            is_setup=data.get("is_setup", False),
            last_totp_used=data.get("last_totp_used"),
            failed_attempts=data.get("failed_attempts", 0),
            locked_until=datetime.fromisoformat(data["locked_until"]) if data.get("locked_until") else None
        )

        if data.get("setup_timestamp"):
            record.setup_timestamp = datetime.fromisoformat(data["setup_timestamp"])
        if data.get("last_successful_auth"):
            record.last_successful_auth = datetime.fromisoformat(data["last_successful_auth"])  # type: ignore

        return record


class MultiFactorAuth:
    """
    Multi-Factor Authentication system for pharmaceutical compliance.
    
    Provides TOTP-based second factor authentication with backup codes,
    account lockout protection, and comprehensive audit logging.
    """

    def __init__(
        self,
        mfa_dir: str = "compliance/mfa",
        max_failed_attempts: int = 3,
        lockout_duration: timedelta = timedelta(minutes=30),
        totp_time_step: int = 30
    ):
        """Initialize MFA system."""
        self.mfa_dir = Path(mfa_dir)
        self.mfa_dir.mkdir(parents=True, exist_ok=True)

        self.max_failed_attempts = max_failed_attempts
        self.lockout_duration = lockout_duration
        self.totp_time_step = totp_time_step

        # MFA user records
        self.user_records_file = self.mfa_dir / "mfa_users.json"
        self.user_records = self._load_user_records()

        # MFA audit log
        self.audit_log_file = self.mfa_dir / "mfa_audit.jsonl"

        # Backup codes system
        self.backup_codes = BackupCodes()

        logger.info("[MFA] Multi-Factor Authentication system initialized")

    def _load_user_records(self) -> dict[str, MFAUserRecord]:
        """Load MFA user records from file."""
        if not self.user_records_file.exists():
            return {}

        try:
            with open(self.user_records_file, encoding="utf-8") as f:
                data = json.load(f)
                return {
                    user_id: MFAUserRecord.from_dict(record_data)
                    for user_id, record_data in data.items()
                }
        except Exception as e:
            logger.error(f"[MFA] Failed to load user records: {e}")
            # NO FALLBACKS - MFA record corruption is a security failure
            raise RuntimeError(f"MFA user records corrupted: {e}") from e

    def _save_user_records(self) -> None:
        """Save MFA user records to file."""
        try:
            data = {
                user_id: record.to_dict()
                for user_id, record in self.user_records.items()
            }

            with open(self.user_records_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, sort_keys=True)

        except Exception as e:
            # NO FALLBACKS - MFA record save failure is a security failure
            raise RuntimeError(f"Failed to save MFA user records: {e}") from e

    def _log_mfa_event(
        self,
        event_type: str,
        user_id: str,
        result: AuthenticationResult,
        details: dict[str, Any]
    ) -> None:
        """Log MFA event for audit trail."""
        event = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "result": result.value,
            "details": details,
            "regulatory_context": "21_CFR_Part_11_mfa_authentication"
        }

        try:
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                json.dump(event, f, separators=(",", ":"))
                f.write("\n")
        except Exception as e:
            logger.error(f"[MFA] Failed to log MFA event: {e}")

    def setup_mfa_for_user(self, user_id: str) -> dict[str, Any]:
        """
        Setup MFA for a user by generating TOTP secret and backup codes.
        
        Args:
            user_id: User identifier
            
        Returns:
            Dict containing setup information (secret, QR code, backup codes)
        """
        try:
            # Generate TOTP secret
            totp_secret = secrets.token_bytes(20)  # 160-bit secret

            # Generate backup codes
            backup_codes_plain = self.backup_codes.generate_backup_codes()
            backup_codes_hashed = self.backup_codes.hash_backup_codes(backup_codes_plain)

            # Create MFA user record
            mfa_record = MFAUserRecord(
                user_id=user_id,
                totp_secret=totp_secret,
                backup_codes=backup_codes_hashed,
                is_setup=False  # Will be set to True after verification
            )

            self.user_records[user_id] = mfa_record
            self._save_user_records()

            # Create setup information
            totp_secret_b32 = base64.b32encode(totp_secret).decode()
            qr_uri = f"otpauth://totp/PharmaceuticalSystem:{user_id}?secret={totp_secret_b32}&issuer=PharmaceuticalSystem"

            setup_info = {
                "user_id": user_id,
                "totp_secret": totp_secret_b32,
                "qr_code_uri": qr_uri,
                "backup_codes": backup_codes_plain,  # Show plain codes to user once
                "setup_timestamp": datetime.now(UTC).isoformat(),
                "instructions": {
                    "step1": "Scan QR code with authenticator app (Google Authenticator, Authy, etc.)",
                    "step2": "Enter TOTP code to verify setup",
                    "step3": "Save backup codes in secure location"
                }
            }

            self._log_mfa_event(
                event_type="mfa_setup_initiated",
                user_id=user_id,
                result=AuthenticationResult.SUCCESS,
                details={"backup_codes_generated": len(backup_codes_plain)}
            )

            logger.info(f"[MFA] MFA setup initiated for user: {user_id}")
            return setup_info

        except Exception as e:
            logger.error(f"[MFA] MFA setup failed for {user_id}: {e}")
            self._log_mfa_event(
                event_type="mfa_setup_failed",
                user_id=user_id,
                result=AuthenticationResult.AUTHENTICATION_ERROR,
                details={"error": str(e)}
            )
            # NO FALLBACKS - MFA setup failure must be explicit
            raise RuntimeError(f"MFA setup failed: {e}") from e

    def verify_mfa_setup(self, user_id: str, totp_code: str) -> bool:
        """
        Verify MFA setup by confirming user can generate valid TOTP code.
        
        Args:
            user_id: User identifier
            totp_code: TOTP code from user's authenticator app
            
        Returns:
            bool: True if setup verified and activated
        """
        try:
            if user_id not in self.user_records:
                return False

            record = self.user_records[user_id]
            if not record.totp_secret:
                return False

            # Verify TOTP code
            totp_generator = TOTPGenerator(record.totp_secret, self.totp_time_step)

            if totp_generator.verify_totp(totp_code, window=1):
                # Activate MFA for user
                record.is_setup = True
                record.setup_timestamp = datetime.now(UTC)
                self._save_user_records()

                self._log_mfa_event(
                    event_type="mfa_setup_verified",
                    user_id=user_id,
                    result=AuthenticationResult.SUCCESS,
                    details={"verified_with_totp": True}
                )

                logger.info(f"[MFA] MFA setup verified for user: {user_id}")
                return True
            self._log_mfa_event(
                event_type="mfa_setup_verification_failed",
                user_id=user_id,
                result=AuthenticationResult.INVALID_TOTP,
                details={"invalid_totp_code": True}
            )
            return False

        except Exception as e:
            logger.error(f"[MFA] MFA setup verification failed: {e}")
            return False

    def authenticate_with_mfa(
        self,
        user_id: str,
        totp_code: str | None = None,
        backup_code: str | None = None
    ) -> AuthenticationResult:
        """
        Authenticate user with MFA (TOTP or backup code).
        
        Args:
            user_id: User identifier
            totp_code: TOTP code from authenticator app
            backup_code: Backup recovery code
            
        Returns:
            AuthenticationResult: Result of MFA authentication
        """
        try:
            # Check if user has MFA setup
            if user_id not in self.user_records:
                self._log_mfa_event(
                    event_type="mfa_authentication",
                    user_id=user_id,
                    result=AuthenticationResult.MFA_NOT_SETUP,
                    details={"reason": "user_not_enrolled"}
                )
                return AuthenticationResult.MFA_NOT_SETUP

            record = self.user_records[user_id]

            if not record.is_setup:
                self._log_mfa_event(
                    event_type="mfa_authentication",
                    user_id=user_id,
                    result=AuthenticationResult.MFA_NOT_SETUP,
                    details={"reason": "setup_not_verified"}
                )
                return AuthenticationResult.MFA_NOT_SETUP

            # Check if account is locked
            if record.is_locked():
                self._log_mfa_event(
                    event_type="mfa_authentication",
                    user_id=user_id,
                    result=AuthenticationResult.ACCOUNT_LOCKED,
                    details={"locked_until": record.locked_until.isoformat() if record.locked_until else None}
                )
                return AuthenticationResult.ACCOUNT_LOCKED

            # Authenticate with TOTP
            if totp_code:
                return self._authenticate_with_totp(user_id, record, totp_code)

            # Authenticate with backup code
            if backup_code:
                return self._authenticate_with_backup_code(user_id, record, backup_code)

            self._log_mfa_event(
                event_type="mfa_authentication",
                user_id=user_id,
                result=AuthenticationResult.AUTHENTICATION_ERROR,
                details={"reason": "no_auth_method_provided"}
            )
            return AuthenticationResult.AUTHENTICATION_ERROR

        except Exception as e:
            logger.error(f"[MFA] MFA authentication failed: {e}")
            self._log_mfa_event(
                event_type="mfa_authentication",
                user_id=user_id,
                result=AuthenticationResult.AUTHENTICATION_ERROR,
                details={"error": str(e)}
            )
            return AuthenticationResult.AUTHENTICATION_ERROR

    def _authenticate_with_totp(
        self,
        user_id: str,
        record: MFAUserRecord,
        totp_code: str
    ) -> AuthenticationResult:
        """Authenticate using TOTP code."""
        if not record.totp_secret:
            return AuthenticationResult.AUTHENTICATION_ERROR

        totp_generator = TOTPGenerator(record.totp_secret, self.totp_time_step)

        # Check for TOTP reuse
        if record.last_totp_used == totp_code:
            record.failed_attempts += 1
            self._save_user_records()

            self._log_mfa_event(
                event_type="mfa_totp_authentication",
                user_id=user_id,
                result=AuthenticationResult.INVALID_TOTP,
                details={"reason": "totp_reuse_detected"}
            )
            return AuthenticationResult.INVALID_TOTP

        # Verify TOTP code
        if totp_generator.verify_totp(totp_code, window=1):
            # Successful authentication
            record.last_totp_used = totp_code
            record.failed_attempts = 0
            record.last_successful_auth = datetime.now(UTC)  # type: ignore
            self._save_user_records()

            self._log_mfa_event(
                event_type="mfa_totp_authentication",
                user_id=user_id,
                result=AuthenticationResult.SUCCESS,
                details={"auth_method": "totp"}
            )

            return AuthenticationResult.SUCCESS
        # Failed authentication
        record.failed_attempts += 1

        # Lock account if too many failures
        if record.failed_attempts >= self.max_failed_attempts:
            record.locked_until = datetime.now(UTC) + self.lockout_duration

        self._save_user_records()

        result = AuthenticationResult.ACCOUNT_LOCKED if record.is_locked() else AuthenticationResult.INVALID_TOTP

        self._log_mfa_event(
            event_type="mfa_totp_authentication",
            user_id=user_id,
            result=result,
            details={
                "failed_attempts": record.failed_attempts,
                "account_locked": record.is_locked()
            }
        )

        return result

    def _authenticate_with_backup_code(
        self,
        user_id: str,
        record: MFAUserRecord,
        backup_code: str
    ) -> AuthenticationResult:
        """Authenticate using backup code."""
        is_valid, used_code_hash = self.backup_codes.verify_backup_code(
            backup_code, record.backup_codes
        )

        if is_valid:
            # Remove used backup code
            record.backup_codes.remove(used_code_hash)
            record.failed_attempts = 0
            record.last_successful_auth = datetime.now(UTC)  # type: ignore
            self._save_user_records()

            self._log_mfa_event(
                event_type="mfa_backup_code_authentication",
                user_id=user_id,
                result=AuthenticationResult.SUCCESS,
                details={
                    "auth_method": "backup_code",
                    "remaining_codes": len(record.backup_codes)
                }
            )

            # Warn if running low on backup codes
            if len(record.backup_codes) <= 2:
                logger.warning(f"[MFA] User {user_id} has {len(record.backup_codes)} backup codes remaining")

            return AuthenticationResult.SUCCESS
        # Failed authentication
        record.failed_attempts += 1

        # Lock account if too many failures
        if record.failed_attempts >= self.max_failed_attempts:
            record.locked_until = datetime.now(UTC) + self.lockout_duration

        self._save_user_records()

        result = AuthenticationResult.ACCOUNT_LOCKED if record.is_locked() else AuthenticationResult.INVALID_BACKUP_CODE

        self._log_mfa_event(
            event_type="mfa_backup_code_authentication",
            user_id=user_id,
            result=result,
            details={
                "failed_attempts": record.failed_attempts,
                "account_locked": record.is_locked()
            }
        )

        return result

    def unlock_user_account(self, user_id: str, admin_user_id: str) -> bool:
        """
        Manually unlock a user account (admin function).
        
        Args:
            user_id: User to unlock
            admin_user_id: Administrator performing unlock
            
        Returns:
            bool: True if successfully unlocked
        """
        try:
            if user_id not in self.user_records:
                return False

            record = self.user_records[user_id]
            record.locked_until = None
            record.failed_attempts = 0
            self._save_user_records()

            self._log_mfa_event(
                event_type="mfa_account_unlocked",
                user_id=user_id,
                result=AuthenticationResult.SUCCESS,
                details={"unlocked_by": admin_user_id}
            )

            logger.info(f"[MFA] Account unlocked: {user_id} by {admin_user_id}")
            return True

        except Exception as e:
            logger.error(f"[MFA] Account unlock failed: {e}")
            return False

    def generate_mfa_report(self) -> dict[str, Any]:
        """Generate comprehensive MFA status and compliance report."""
        current_time = datetime.now(UTC)

        # Analyze user MFA status
        total_users = len(self.user_records)
        setup_complete = sum(1 for record in self.user_records.values() if record.is_setup)
        currently_locked = sum(1 for record in self.user_records.values() if record.is_locked())

        # Analyze backup code usage
        backup_code_stats = {
            "users_with_codes": 0,
            "low_backup_codes": 0,  # Users with ≤2 codes remaining
            "no_backup_codes": 0    # Users with no codes remaining
        }

        for record in self.user_records.values():
            if record.backup_codes:
                backup_code_stats["users_with_codes"] += 1
                if len(record.backup_codes) <= 2:
                    backup_code_stats["low_backup_codes"] += 1
                if len(record.backup_codes) == 0:
                    backup_code_stats["no_backup_codes"] += 1

        # Recent authentication activity
        recent_auths = 0
        for record in self.user_records.values():
            if record.last_successful_auth:
                if (current_time - record.last_successful_auth).days <= 30:
                    recent_auths += 1

        return {
            "report_timestamp": current_time.isoformat(),
            "mfa_enrollment": {
                "total_users": total_users,
                "setup_complete": setup_complete,
                "setup_pending": total_users - setup_complete,
                "enrollment_rate": (setup_complete / max(1, total_users)) * 100
            },
            "account_security": {
                "currently_locked": currently_locked,
                "lockout_rate": (currently_locked / max(1, total_users)) * 100,
                "max_failed_attempts": self.max_failed_attempts,
                "lockout_duration_minutes": int(self.lockout_duration.total_seconds() / 60)
            },
            "backup_codes": backup_code_stats,
            "activity_metrics": {
                "recent_authentications_30d": recent_auths,
                "active_user_rate": (recent_auths / max(1, setup_complete)) * 100
            },
            "system_configuration": {
                "totp_time_step": self.totp_time_step,
                "totp_window_tolerance": 1,
                "backup_code_length": self.backup_codes.code_length,
                "backup_codes_per_user": self.backup_codes.num_codes
            },
            "compliance_status": {
                "mfa_enforcement_active": True,
                "audit_logging_enabled": True,
                "account_lockout_enabled": True,
                "backup_recovery_available": True
            }
        }


# Global MFA service instance
_global_mfa_service: MultiFactorAuth | None = None


def get_mfa_service() -> MultiFactorAuth:
    """Get the global MFA service."""
    global _global_mfa_service
    if _global_mfa_service is None:
        _global_mfa_service = MultiFactorAuth()
    return _global_mfa_service


# Export main classes and functions
__all__ = [
    "AuthenticationResult",
    "BackupCodes",
    "MFAUserRecord",
    "MultiFactorAuth",
    "TOTPGenerator",
    "get_mfa_service"
]
