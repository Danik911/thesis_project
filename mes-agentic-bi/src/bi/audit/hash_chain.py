"""SHA-512 hash chain manager for ALCOA+ audit event integrity.

Adapted from main/src/compliance/alcoa_validator.py (lines 72-84).
Each event is hashed with the previous event's hash, forming a
tamper-evident chain of custody.

Thread-safe via threading.Lock() for concurrent request handling.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any


class HashChainManager:
    """Maintains an in-memory SHA-512 hash chain for audit events.

    The chain resets on process restart (GENESIS block). Each running
    instance maintains its own independent chain. Cross-instance
    continuity is a future enhancement (requires persistent storage).
    """

    def __init__(self) -> None:
        self._previous_hash: str | None = None
        self._lock = threading.Lock()
        self._event_count = 0

    def compute_hash(self, event_data: dict[str, Any], timestamp: str) -> tuple[str, str]:
        """Compute SHA-512 hash for an event, chained to previous hash.

        Args:
            event_data: The event payload to hash.
            timestamp: ISO-8601 timestamp of the event.

        Returns:
            Tuple of (event_hash, previous_hash).
        """
        data_str = json.dumps(event_data, sort_keys=True, default=str)

        with self._lock:
            if self._previous_hash:
                chain_str = f"{self._previous_hash}:{data_str}:{timestamp}"
                previous = self._previous_hash
            else:
                chain_str = f"GENESIS:{data_str}:{timestamp}"
                previous = "GENESIS"

            event_hash = hashlib.sha512(chain_str.encode()).hexdigest()
            self._previous_hash = event_hash
            self._event_count += 1

        return event_hash, previous

    @property
    def event_count(self) -> int:
        """Number of events hashed since last reset."""
        return self._event_count

    @property
    def current_hash(self) -> str | None:
        """Most recent hash in the chain, or None if no events yet."""
        return self._previous_hash
