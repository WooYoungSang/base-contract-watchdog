"""Tests for AI severity classifier."""

import pytest
from contract_watchdog.classifier import ClassifiedEvent, Severity, SeverityClassifier


class TestSeverity:
    def test_severity_ordering(self):
        assert Severity.CRITICAL > Severity.HIGH
        assert Severity.HIGH > Severity.MEDIUM
        assert Severity.MEDIUM > Severity.LOW


class TestSeverityClassifier:
    @pytest.fixture
    def classifier(self, top_tvl_protocols):
        return SeverityClassifier(top_tvl_protocols=top_tvl_protocols)

    def test_proxy_upgrade_on_top_tvl_is_critical(self, classifier, top_tvl_protocols):
        """Proxy upgrade on a top-10 TVL protocol => CRITICAL."""
        top_addr = next(iter(top_tvl_protocols))
        event = {
            "event_type": "ProxyUpgraded",
            "contract_address": top_addr,
            "details": {"new_implementation": "0xdeadbeef"},
        }
        result = classifier.classify(event)
        assert result.severity == Severity.CRITICAL
        assert "top" in result.reasoning.lower() or "tvl" in result.reasoning.lower()

    def test_admin_transfer_to_unknown_is_critical(self, classifier):
        """Admin transfer to unknown/zero address => CRITICAL."""
        event = {
            "event_type": "OwnershipTransferred",
            "contract_address": "0x9999999999999999999999999999999999999999",
            "details": {
                "previous_owner": "0xcccccccccccccccccccccccccccccccccccccccc",
                "new_owner": "0x0000000000000000000000000000000000000000",
            },
        }
        result = classifier.classify(event)
        assert result.severity == Severity.CRITICAL

    def test_proxy_upgrade_on_known_protocol_is_high(self, classifier):
        """Proxy upgrade on a known (non-top-TVL) protocol => HIGH."""
        event = {
            "event_type": "ProxyUpgraded",
            "contract_address": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "details": {"new_implementation": "0xdeadbeef"},
        }
        result = classifier.classify(event)
        assert result.severity == Severity.HIGH

    def test_role_change_on_critical_function_is_high(self, classifier):
        """Role changes on critical functions => HIGH."""
        event = {
            "event_type": "RoleGranted",
            "contract_address": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "details": {
                "role": "ADMIN_ROLE",
                "account": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "is_critical_role": True,
            },
        }
        result = classifier.classify(event)
        assert result.severity == Severity.HIGH

    def test_minor_permission_change_is_medium(self, classifier):
        """Minor permission changes => MEDIUM."""
        event = {
            "event_type": "RoleGranted",
            "contract_address": "0xcccccccccccccccccccccccccccccccccccccccc",
            "details": {
                "role": "REPORTER_ROLE",
                "account": "0xffffffffffffffffffffffffffffffffffffffff",
                "is_critical_role": False,
            },
        }
        result = classifier.classify(event)
        assert result.severity == Severity.MEDIUM

    def test_routine_timelock_is_low(self, classifier):
        """Routine timelock operations => LOW."""
        event = {
            "event_type": "TimelockOperation",
            "contract_address": "0xdddddddddddddddddddddddddddddddddddddddd",
            "details": {"operation": "schedule", "delay_seconds": 172800},
        }
        result = classifier.classify(event)
        assert result.severity == Severity.LOW

    def test_classified_event_has_reasoning(self, classifier, top_tvl_protocols):
        """ClassifiedEvent must always include a non-empty reasoning string."""
        top_addr = next(iter(top_tvl_protocols))
        event = {
            "event_type": "ProxyUpgraded",
            "contract_address": top_addr,
            "details": {},
        }
        result = classifier.classify(event)
        assert isinstance(result, ClassifiedEvent)
        assert len(result.reasoning) > 0

    def test_classified_event_stores_original(self, classifier):
        """ClassifiedEvent must retain the original event data."""
        event = {
            "event_type": "AdminChanged",
            "contract_address": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
            "details": {"previous_admin": "0xaaa", "new_admin": "0xbbb"},
        }
        result = classifier.classify(event)
        assert result.original_event == event

    def test_admin_changed_is_high(self, classifier):
        """EIP-1967 AdminChanged event => HIGH."""
        event = {
            "event_type": "AdminChanged",
            "contract_address": "0xffffffffffffffffffffffffffffffffffffffff",
            "details": {
                "previous_admin": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "new_admin": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            },
        }
        result = classifier.classify(event)
        assert result.severity in (Severity.HIGH, Severity.CRITICAL)

    def test_accuracy_on_test_cases(self, top_tvl_protocols):
        """Classifier must achieve >80% accuracy on labelled test set."""
        classifier = SeverityClassifier(top_tvl_protocols=top_tvl_protocols)
        top_addr = next(iter(top_tvl_protocols))

        labelled = [
            (
                {"event_type": "ProxyUpgraded", "contract_address": top_addr, "details": {}},
                Severity.CRITICAL,
            ),
            (
                {
                    "event_type": "OwnershipTransferred",
                    "contract_address": "0x1111111111111111111111111111111111111111",
                    "details": {
                        "previous_owner": "0xaaa",
                        "new_owner": "0x0000000000000000000000000000000000000000",
                    },
                },
                Severity.CRITICAL,
            ),
            (
                {
                    "event_type": "ProxyUpgraded",
                    "contract_address": "0x2222222222222222222222222222222222222222",
                    "details": {},
                },
                Severity.HIGH,
            ),
            (
                {
                    "event_type": "RoleGranted",
                    "contract_address": "0x3333333333333333333333333333333333333333",
                    "details": {"role": "MINTER_ROLE", "is_critical_role": True},
                },
                Severity.HIGH,
            ),
            (
                {
                    "event_type": "RoleGranted",
                    "contract_address": "0x4444444444444444444444444444444444444444",
                    "details": {"role": "VIEWER_ROLE", "is_critical_role": False},
                },
                Severity.MEDIUM,
            ),
            (
                {
                    "event_type": "TimelockOperation",
                    "contract_address": "0x5555555555555555555555555555555555555555",
                    "details": {"operation": "execute", "delay_seconds": 86400},
                },
                Severity.LOW,
            ),
        ]

        correct = sum(
            1 for event, expected in labelled if classifier.classify(event).severity == expected
        )
        accuracy = correct / len(labelled)
        assert accuracy >= 0.80, f"Accuracy {accuracy:.0%} below 80% threshold"
