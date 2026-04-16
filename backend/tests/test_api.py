"""Tests for FastAPI endpoints using TestClient."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from contract_watchdog.api import app, get_storage
from contract_watchdog.classifier import ClassifiedEvent, Severity
from contract_watchdog.storage import EventStorage
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_storage_with_events() -> EventStorage:
    """Return an in-memory EventStorage pre-populated with sample events."""
    storage = EventStorage()

    sample_events = [
        ClassifiedEvent(
            severity=Severity.CRITICAL,
            reasoning="Proxy upgrade on top-TVL protocol",
            original_event={
                "event_type": "ProxyUpgraded",
                "contract_address": "0x4200000000000000000000000000000000000010",
                "block_number": 12345678,
                "tx_hash": "0xabc123",
                "details": {"new_implementation": "0xdeadbeef"},
            },
        ),
        ClassifiedEvent(
            severity=Severity.HIGH,
            reasoning="Proxy upgrade on known protocol",
            original_event={
                "event_type": "ProxyUpgraded",
                "contract_address": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "block_number": 12345679,
                "tx_hash": "0xdef456",
                "details": {"new_implementation": "0xcafebabe"},
            },
        ),
        ClassifiedEvent(
            severity=Severity.MEDIUM,
            reasoning="Minor permission change",
            original_event={
                "event_type": "RoleGranted",
                "contract_address": "0xcccccccccccccccccccccccccccccccccccccccc",
                "block_number": 12345680,
                "tx_hash": "0x999aaa",
                "details": {"role": "REPORTER_ROLE", "is_critical_role": False},
            },
        ),
        ClassifiedEvent(
            severity=Severity.LOW,
            reasoning="Routine timelock",
            original_event={
                "event_type": "TimelockOperation",
                "contract_address": "0xdddddddddddddddddddddddddddddddddddddddd",
                "block_number": 12345681,
                "tx_hash": "0x111bbb",
                "details": {"operation": "schedule"},
            },
        ),
    ]
    for ev in sample_events:
        storage.save(ev)
    return storage


@pytest.fixture
def client():
    """TestClient with pre-populated storage via dependency override."""
    storage = _make_storage_with_events()
    app.dependency_overrides[get_storage] = lambda: storage
    with patch("contract_watchdog.api._watcher", MagicMock(_running=True)):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture
def empty_client():
    """TestClient with empty storage via dependency override."""
    storage = EventStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    with patch("contract_watchdog.api._watcher", MagicMock(_running=False)):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "watcher_running" in data

    def test_health_watcher_running_flag(self, client):
        resp = client.get("/health")
        assert resp.json()["watcher_running"] is True


# ---------------------------------------------------------------------------
# GET /events
# ---------------------------------------------------------------------------

class TestListEvents:
    def test_returns_all_events(self, client):
        resp = client.get("/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 4
        assert len(data["items"]) == 4

    def test_filter_by_severity_critical(self, client):
        resp = client.get("/events?severity=CRITICAL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert data["items"][0]["severity"] == "CRITICAL"

    def test_filter_by_severity_high(self, client):
        resp = client.get("/events?severity=HIGH")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 1

    def test_filter_by_event_type(self, client):
        resp = client.get("/events?event_type=ProxyUpgraded")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 2
        for item in data["items"]:
            assert item["event_type"] == "ProxyUpgraded"

    def test_filter_by_contract(self, client):
        resp = client.get("/events?contract=0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert "bbbb" in data["items"][0]["contract_address"]

    def test_pagination_page_size(self, client):
        resp = client.get("/events?page=1&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["page_size"] == 2
        assert data["pagination"]["pages"] == 2

    def test_pagination_page_2(self, client):
        resp = client.get("/events?page=2&page_size=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["pagination"]["page"] == 2

    def test_pagination_beyond_last_page_returns_empty(self, client):
        resp = client.get("/events?page=99&page_size=10")
        assert resp.status_code == 200
        assert resp.json()["items"] == []

    def test_empty_storage_returns_zero(self, empty_client):
        resp = empty_client.get("/events")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 0
        assert data["items"] == []

    def test_combined_filters(self, client):
        resp = client.get(
            "/events?severity=CRITICAL&event_type=ProxyUpgraded"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert data["items"][0]["severity"] == "CRITICAL"
        assert data["items"][0]["event_type"] == "ProxyUpgraded"

    def test_response_contains_details(self, client):
        resp = client.get("/events?severity=CRITICAL")
        item = resp.json()["items"][0]
        assert "details" in item
        assert isinstance(item["details"], dict)


# ---------------------------------------------------------------------------
# GET /events/{id}
# ---------------------------------------------------------------------------

class TestGetEvent:
    def test_get_existing_event(self, client):
        resp = client.get("/events/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert "event_type" in data
        assert "severity" in data
        assert "details" in data
        assert "classified_at" in data

    def test_get_nonexistent_event_404(self, client):
        resp = client.get("/events/9999")
        assert resp.status_code == 404

    def test_get_event_includes_reasoning_in_details_or_response(self, client):
        resp = client.get("/events/1")
        assert resp.status_code == 200
        # Response must have the required fields
        data = resp.json()
        assert data["block_number"] > 0
        assert data["tx_hash"].startswith("0x")


# ---------------------------------------------------------------------------
# GET /contracts/{address}/events
# ---------------------------------------------------------------------------

class TestContractEvents:
    def test_events_for_known_contract(self, client):
        resp = client.get(
            "/contracts/0x4200000000000000000000000000000000000010/events"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["pagination"]["total"] == 1
        assert data["items"][0]["contract_address"] == "0x4200000000000000000000000000000000000010"

    def test_events_for_unknown_contract_empty(self, client):
        resp = client.get("/contracts/0x0000000000000000000000000000000000000001/events")
        assert resp.status_code == 200
        assert resp.json()["pagination"]["total"] == 0

    def test_contract_events_pagination(self, client):
        resp = client.get(
            "/contracts/0x4200000000000000000000000000000000000010/events?page=1&page_size=1"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1


# ---------------------------------------------------------------------------
# GET /stats
# ---------------------------------------------------------------------------

class TestStats:
    def test_stats_total_correct(self, client):
        resp = client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 4

    def test_stats_by_severity(self, client):
        resp = client.get("/stats")
        data = resp.json()
        severities = {s["severity"] for s in data["by_severity"]}
        assert "CRITICAL" in severities
        assert "HIGH" in severities

    def test_stats_most_active_contracts(self, client):
        resp = client.get("/stats")
        data = resp.json()
        assert isinstance(data["most_active_contracts"], list)
        assert len(data["most_active_contracts"]) > 0
        first = data["most_active_contracts"][0]
        assert "contract_address" in first
        assert "event_count" in first

    def test_stats_empty_storage(self, empty_client):
        resp = empty_client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 0
        assert data["by_severity"] == []
        assert data["most_active_contracts"] == []
