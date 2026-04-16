"""Detect proxy upgrade events: EIP-1967 Upgraded(address), UUPS, Transparent Proxy."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# keccak256("Upgraded(address)")
UPGRADED_TOPIC = "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b"

# EIP-1967 implementation slot: keccak256("eip1967.proxy.implementation") - 1
EIP1967_IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"


class UpgradeDetector:
    """Detects proxy upgrade events from raw EVM log entries."""

    WATCHED_TOPICS = {UPGRADED_TOPIC}

    def process_log(self, log: dict) -> dict | None:
        """Return a structured event dict if this log is a proxy upgrade, else None."""
        try:
            topics = log.get("topics", [])
            if not topics:
                return None

            topic0 = _normalize(topics[0])

            if topic0 == UPGRADED_TOPIC:
                return self._parse_upgraded(log, topics)

        except Exception as exc:
            logger.debug("UpgradeDetector.process_log error: %s", exc)

        return None

    def _parse_upgraded(self, log: dict, topics: list) -> dict:
        new_impl = _decode_address(topics[1]) if len(topics) > 1 else "unknown"
        return {
            "event_type": "ProxyUpgraded",
            "contract_address": log["address"],
            "block_number": log["blockNumber"],
            "tx_hash": log["transactionHash"],
            "details": {
                "new_implementation": new_impl,
                "upgrade_type": "EIP-1967",
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
    """Extract a 20-byte address from a 32-byte topic (right-aligned)."""
    raw = _normalize(topic)
    # Last 40 hex chars = 20 bytes
    return "0x" + raw[-40:]
