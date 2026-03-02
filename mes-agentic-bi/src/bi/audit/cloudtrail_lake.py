"""CloudTrail Lake emitter (deferred, env-gated)."""

from __future__ import annotations

import json
from typing import Any

import boto3


class CloudTrailLakeEmitter:
    """Emit ALCOA+ events to CloudTrail Lake channel via PutAuditEvents."""

    def __init__(self, config: Any) -> None:
        if not config.cloudtrail_lake_channel_arn:
            raise RuntimeError(
                "BI_CLOUDTRAIL_LAKE_ENABLED=true but BI_CLOUDTRAIL_LAKE_CHANNEL_ARN is empty."
            )

        self._channel_arn = config.cloudtrail_lake_channel_arn
        self._client = boto3.client("cloudtrail-data", region_name=config.cloudtrail_lake_region)

    def emit(self, event: Any) -> None:
        payload = event.to_cloudwatch_dict()
        self._client.put_audit_events(
            channelArn=self._channel_arn,
            auditEvents=[
                {
                    "id": payload["event_id"],
                    "eventData": json.dumps(payload, default=str),
                    "eventDataChecksum": payload["alcoa"]["event_hash"],
                }
            ],
        )
