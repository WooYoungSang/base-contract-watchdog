"""Detect permission change events: RoleGranted, RoleRevoked (AccessControl)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# keccak256("RoleGranted(bytes32,address,address)")
ROLE_GRANTED_TOPIC = "0x2f8788117e7eff1d82e926ec794901d17c78024a50270940304540a733656f0d"

# keccak256("RoleRevoked(bytes32,address,address)")
ROLE_REVOKED_TOPIC = "0xf6391f5c32d9c69d2a47ea670b442974b53935d1edec2a23dd68e7d95e45fd21"

# Known critical role hashes (DEFAULT_ADMIN_ROLE, UPGRADER_ROLE, etc.)
CRITICAL_ROLES: set[str] = {
    # DEFAULT_ADMIN_ROLE = bytes32(0)
    "0x0000000000000000000000000000000000000000000000000000000000000000",
    # keccak256("UPGRADER_ROLE")
    "0x189ab7a9244df0848122154315af71fe140f3db0fe014031783b0946b8c9d2e3",
    # keccak256("ADMIN_ROLE") — common alias
    "0xa49807205ce4d355092ef5a8a18f56e8913cf4a201fbe287825b095693c21775",
    # keccak256("MINTER_ROLE")
    "0x9f2df0fed2c77648de5860a4cc508cd0818c85b8b8a1ab4ceeef8d981c8956a6",
    # keccak256("PAUSER_ROLE")
    "0x65d7a28e3265b37a6474929f336521b332c1681b933f6cb9f3376673440d862a",
}


class PermissionDetector:
    """Detects role-based permission change events from raw EVM log entries."""

    WATCHED_TOPICS = {ROLE_GRANTED_TOPIC, ROLE_REVOKED_TOPIC}

    def process_log(self, log: dict) -> dict | None:
        try:
            topics = log.get("topics", [])
            if not topics:
                return None

            topic0 = _normalize(topics[0])

            if topic0 == ROLE_GRANTED_TOPIC:
                return self._parse_role_event(log, topics, "RoleGranted")

            if topic0 == ROLE_REVOKED_TOPIC:
                return self._parse_role_event(log, topics, "RoleRevoked")

        except Exception as exc:
            logger.debug("PermissionDetector.process_log error: %s", exc)

        return None

    def _parse_role_event(self, log: dict, topics: list, event_type: str) -> dict:
        role = _normalize(topics[1]) if len(topics) > 1 else "unknown"
        account = _decode_address(topics[2]) if len(topics) > 2 else "unknown"
        is_critical = role in CRITICAL_ROLES
        return {
            "event_type": event_type,
            "contract_address": log["address"],
            "block_number": log["blockNumber"],
            "tx_hash": log["transactionHash"],
            "details": {
                "role": role,
                "account": account,
                "is_critical_role": is_critical,
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
