"""Rule-based AI severity classifier for detected contract events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Event types considered high-impact for role changes
CRITICAL_ROLE_KEYWORDS = {"admin", "upgrader", "owner", "minter", "pauser", "guardian"}


@dataclass
class ClassifiedEvent:
    severity: Severity
    reasoning: str
    original_event: dict


class SeverityClassifier:
    """Rule-based severity classifier for MVP.

    Rules (in priority order):
        CRITICAL:
          - Proxy upgrade on a top-10 TVL protocol
          - Admin/owner transfer to zero address (renouncement) or unknown EOA
        HIGH:
          - Proxy upgrade on any known protocol (not top-TVL)
          - Role changes on critical functions (is_critical_role=True)
          - AdminChanged event on any proxy
        MEDIUM:
          - Minor permission changes (is_critical_role=False)
          - Known admin rotations (non-zero addresses, both known)
        LOW:
          - Routine timelock scheduling/cancellation
          - Everything else
    """

    def __init__(self, top_tvl_protocols: set[str] | None = None) -> None:
        self.top_tvl_protocols: set[str] = {
            a.lower() for a in (top_tvl_protocols or set())
        }

    def classify(self, event: dict) -> ClassifiedEvent:
        event_type = event.get("event_type", "")
        contract = (event.get("contract_address") or "").lower()
        details = event.get("details") or {}

        severity, reasoning = self._apply_rules(event_type, contract, details)
        return ClassifiedEvent(severity=severity, reasoning=reasoning, original_event=event)

    # ------------------------------------------------------------------
    # Rule engine
    # ------------------------------------------------------------------

    def _apply_rules(self, event_type: str, contract: str, details: dict) -> tuple[Severity, str]:
        is_top_tvl = contract in self.top_tvl_protocols

        # --- ProxyUpgraded ---
        if event_type == "ProxyUpgraded":
            if is_top_tvl:
                return (
                    Severity.CRITICAL,
                    f"Proxy upgrade on top-TVL protocol {contract}. Immediate review required.",
                )
            return (
                Severity.HIGH,
                f"Proxy upgrade detected on {contract}. Implementation changed to "
                f"{details.get('new_implementation', 'unknown')}.",
            )

        # --- OwnershipTransferred ---
        if event_type == "OwnershipTransferred":
            new_owner = (details.get("new_owner") or "").lower()
            if new_owner == ZERO_ADDRESS or details.get("renounced"):
                return (
                    Severity.CRITICAL,
                    f"Ownership renounced on {contract} — contract is now ownerless.",
                )
            prev_owner = (details.get("previous_owner") or "").lower()
            # Both addresses present and non-zero = known rotation
            if new_owner and prev_owner and new_owner != ZERO_ADDRESS:
                return (
                    Severity.MEDIUM,
                    f"Ownership transferred from {prev_owner} to {new_owner} on {contract}.",
                )
            return (
                Severity.CRITICAL,
                f"Ownership transferred to unknown address on {contract}.",
            )

        # --- AdminChanged (EIP-1967) ---
        if event_type == "AdminChanged":
            return (
                Severity.HIGH,
                f"EIP-1967 admin changed on proxy {contract}. "
                f"New admin: {details.get('new_admin', 'unknown')}.",
            )

        # --- RoleGranted / RoleRevoked ---
        if event_type in ("RoleGranted", "RoleRevoked"):
            is_critical = details.get("is_critical_role", False)
            role = details.get("role", "unknown")
            account = details.get("account", "unknown")

            # Also check by name if role label is provided
            role_name = role.lower() if isinstance(role, str) else ""
            name_critical = any(kw in role_name for kw in CRITICAL_ROLE_KEYWORDS)

            if is_critical or name_critical:
                return (
                    Severity.HIGH,
                    f"{event_type} for critical role {role} on {contract}. Account: {account}.",
                )
            return (
                Severity.MEDIUM,
                f"{event_type} for role {role} on {contract}. Account: {account}.",
            )

        # --- TimelockOperation ---
        if event_type == "TimelockOperation":
            operation = details.get("operation", "unknown")
            delay = details.get("delay_seconds", 0)
            return (
                Severity.LOW,
                f"Routine timelock {operation} on {contract} with {delay}s delay.",
            )

        # --- Fallback ---
        return (
            Severity.LOW,
            f"Unclassified event {event_type} on {contract}.",
        )
