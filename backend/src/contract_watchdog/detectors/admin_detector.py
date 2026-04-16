"""Detect admin change events: OwnershipTransferred, AdminChanged (EIP-1967), Timelock."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# keccak256("OwnershipTransferred(address,address)")
OWNERSHIP_TRANSFERRED_TOPIC = "0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0"

# keccak256("AdminChanged(address,address)")
ADMIN_CHANGED_TOPIC = "0x7e644d79422f17c01e4894b5f4f588d331ebfa28653d42ae832dc59e38c9798f"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


class AdminDetector:
    """Detects admin/ownership change events from raw EVM log entries."""

    WATCHED_TOPICS = {OWNERSHIP_TRANSFERRED_TOPIC, ADMIN_CHANGED_TOPIC}

    def process_log(self, log: dict) -> dict | None:
        try:
            topics = log.get("topics", [])
            if not topics:
                return None

            topic0 = _normalize(topics[0])

            if topic0 == OWNERSHIP_TRANSFERRED_TOPIC:
                return self._parse_ownership_transferred(log, topics)

            if topic0 == ADMIN_CHANGED_TOPIC:
                return self._parse_admin_changed(log, topics)

        except Exception as exc:
            logger.debug("AdminDetector.process_log error: %s", exc)

        return None

    def _parse_ownership_transferred(self, log: dict, topics: list) -> dict:
        previous_owner = _decode_address(topics[1]) if len(topics) > 1 else "unknown"
        new_owner = _decode_address(topics[2]) if len(topics) > 2 else "unknown"
        return {
            "event_type": "OwnershipTransferred",
            "contract_address": log["address"],
            "block_number": log["blockNumber"],
            "tx_hash": log["transactionHash"],
            "details": {
                "previous_owner": previous_owner,
                "new_owner": new_owner,
                "renounced": new_owner == ZERO_ADDRESS,
            },
        }

    def _parse_admin_changed(self, log: dict, topics: list) -> dict:
        previous_admin = _decode_address(topics[1]) if len(topics) > 1 else "unknown"
        new_admin = _decode_address(topics[2]) if len(topics) > 2 else "unknown"
        return {
            "event_type": "AdminChanged",
            "contract_address": log["address"],
            "block_number": log["blockNumber"],
            "tx_hash": log["transactionHash"],
            "details": {
                "previous_admin": previous_admin,
                "new_admin": new_admin,
            },
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return "0x" + value.hex()
    return value.lower() if value.startswith("0x") else value


def _decode_address(topic: str | bytes) -> str:
    raw = _normalize(topic)
    return "0x" + raw[-40:]
