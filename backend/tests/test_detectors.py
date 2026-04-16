"""Tests for all 3 detectors with sample events."""

import pytest
from contract_watchdog.detectors.admin_detector import AdminDetector
from contract_watchdog.detectors.permission_detector import PermissionDetector
from contract_watchdog.detectors.upgrade_detector import UpgradeDetector


class TestUpgradeDetector:
    @pytest.fixture
    def detector(self):
        return UpgradeDetector()

    def test_detects_eip1967_upgraded_event(self, detector, upgraded_event):
        """Should detect EIP-1967 Upgraded(address) event."""
        result = detector.process_log(upgraded_event)
        assert result is not None
        assert result["event_type"] == "ProxyUpgraded"
        assert result["contract_address"] == upgraded_event["address"]

    def test_extracts_new_implementation_address(self, detector, upgraded_event):
        """Should extract the new implementation address from topic[1]."""
        result = detector.process_log(upgraded_event)
        assert "new_implementation" in result["details"]
        impl = result["details"]["new_implementation"].lower()
        assert "deadbeef" in impl

    def test_ignores_unrelated_events(self, detector, role_granted_event):
        """Non-upgrade events should return None."""
        result = detector.process_log(role_granted_event)
        assert result is None

    def test_extracts_block_number(self, detector, upgraded_event):
        """Result should include block_number and tx_hash."""
        result = detector.process_log(upgraded_event)
        assert result["block_number"] == upgraded_event["blockNumber"]
        assert result["tx_hash"] == upgraded_event["transactionHash"]

    def test_detects_admin_changed_as_upgrade_related(self, detector, admin_changed_event):
        """AdminChanged is proxy-related; detector may optionally detect it."""
        # UpgradeDetector focuses on Upgraded events; AdminChanged is for AdminDetector
        # This test confirms it does NOT misclassify AdminChanged as a proxy upgrade
        result = detector.process_log(admin_changed_event)
        # Either None or correctly typed; must NOT say "ProxyUpgraded" for AdminChanged
        if result is not None:
            assert result["event_type"] != "ProxyUpgraded"

    def test_handles_malformed_log_gracefully(self, detector):
        """Malformed log (missing topics) should return None without raising."""
        bad_log = {"address": "0x1234", "topics": [], "blockNumber": 0, "transactionHash": "0x0"}
        result = detector.process_log(bad_log)
        assert result is None


class TestAdminDetector:
    @pytest.fixture
    def detector(self):
        return AdminDetector()

    def test_detects_ownership_transferred(self, detector, ownership_transferred_event):
        """Should detect OwnershipTransferred events."""
        result = detector.process_log(ownership_transferred_event)
        assert result is not None
        assert result["event_type"] == "OwnershipTransferred"

    def test_extracts_ownership_addresses(self, detector, ownership_transferred_event):
        """Should extract previous and new owner addresses."""
        result = detector.process_log(ownership_transferred_event)
        details = result["details"]
        assert "previous_owner" in details
        assert "new_owner" in details
        # new owner is zero address (renounced)
        assert details["new_owner"] == "0x0000000000000000000000000000000000000000"

    def test_detects_admin_changed(self, detector, admin_changed_event):
        """Should detect EIP-1967 AdminChanged events."""
        result = detector.process_log(admin_changed_event)
        assert result is not None
        assert result["event_type"] == "AdminChanged"

    def test_extracts_admin_changed_addresses(self, detector, admin_changed_event):
        """Should extract previous and new admin from AdminChanged."""
        result = detector.process_log(admin_changed_event)
        details = result["details"]
        assert "previous_admin" in details
        assert "new_admin" in details

    def test_ignores_unrelated_events(self, detector, role_granted_event):
        """Non-admin events should return None."""
        result = detector.process_log(role_granted_event)
        assert result is None

    def test_handles_malformed_log_gracefully(self, detector):
        """Malformed log should return None without raising."""
        bad_log = {"address": "0x1234", "topics": [], "blockNumber": 0, "transactionHash": "0x0"}
        result = detector.process_log(bad_log)
        assert result is None


class TestPermissionDetector:
    @pytest.fixture
    def detector(self):
        return PermissionDetector()

    def test_detects_role_granted(self, detector, role_granted_event):
        """Should detect AccessControl RoleGranted events."""
        result = detector.process_log(role_granted_event)
        assert result is not None
        assert result["event_type"] == "RoleGranted"

    def test_extracts_role_details(self, detector, role_granted_event):
        """Should extract role, account, and sender from RoleGranted."""
        result = detector.process_log(role_granted_event)
        details = result["details"]
        assert "role" in details
        assert "account" in details

    def test_detects_role_revoked(self, detector):
        """Should detect RoleRevoked events."""
        role_revoked = {
            "address": "0x4444444444444444444444444444444444444444",
            "topics": [
                # keccak256("RoleRevoked(bytes32,address,address)")
                "0xf6391f5c32d9c69d2a47ea670b442974b53935d1edec2a23dd68e7d95e45fd21",
                "0x9f2df0fed2c77648de5860a4cc508cd0818c85b8b8a1ab4ceeef8d981c8956a6",
                "0x000000000000000000000000eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                "0x000000000000000000000000ffffffffffffffffffffffffffffffffffffffff",
            ],
            "data": "0x",
            "blockNumber": 12345682,
            "transactionHash": "0xaabbccddeeff00112233445566778899aabbccddeeff00112233445566778901",
        }
        result = detector.process_log(role_revoked)
        assert result is not None
        assert result["event_type"] == "RoleRevoked"

    def test_ignores_unrelated_events(self, detector, upgraded_event):
        """Non-permission events should return None."""
        result = detector.process_log(upgraded_event)
        assert result is None

    def test_handles_malformed_log_gracefully(self, detector):
        """Malformed log should return None without raising."""
        bad_log = {"address": "0x1234", "topics": [], "blockNumber": 0, "transactionHash": "0x0"}
        result = detector.process_log(bad_log)
        assert result is None

    def test_marks_critical_roles(self, detector):
        """Known critical role hashes should be flagged is_critical_role=True."""
        # DEFAULT_ADMIN_ROLE = bytes32(0)
        admin_role_event = {
            "address": "0x5555555555555555555555555555555555555555",
            "topics": [
                "0x2f8788117e7eff1d82e926ec794901d17c78024a50270940304540a733656f0d",
                # DEFAULT_ADMIN_ROLE = 0x00...00
                "0x0000000000000000000000000000000000000000000000000000000000000000",
                "0x000000000000000000000000aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "0x000000000000000000000000bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            ],
            "data": "0x",
            "blockNumber": 12345683,
            "transactionHash": "0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        }
        result = detector.process_log(admin_role_event)
        assert result is not None
        assert result["details"].get("is_critical_role") is True
