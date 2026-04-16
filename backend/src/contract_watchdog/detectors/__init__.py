"""Detectors for proxy upgrades, admin changes, and permission changes."""

from contract_watchdog.detectors.admin_detector import AdminDetector
from contract_watchdog.detectors.permission_detector import PermissionDetector
from contract_watchdog.detectors.upgrade_detector import UpgradeDetector

__all__ = ["UpgradeDetector", "AdminDetector", "PermissionDetector"]
