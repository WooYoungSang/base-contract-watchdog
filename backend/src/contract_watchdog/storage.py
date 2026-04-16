"""SQLite-backed event storage for classified contract events."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from contract_watchdog.classifier import ClassifiedEvent, Severity

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    block_number    INTEGER NOT NULL,
    tx_hash         TEXT    NOT NULL,
    contract_address TEXT   NOT NULL,
    event_type      TEXT    NOT NULL,
    severity        TEXT    NOT NULL,
    details         TEXT    NOT NULL,
    classified_at   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_severity
    ON events (severity);

CREATE INDEX IF NOT EXISTS idx_events_contract
    ON events (contract_address);

CREATE INDEX IF NOT EXISTS idx_events_block
    ON events (block_number);
"""


class EventStorage:
    """Persists and retrieves classified events using SQLite."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_schema(self) -> None:
        self._conn.executescript(CREATE_TABLE_SQL)
        self._conn.commit()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save(self, event: ClassifiedEvent) -> int:
        """Persist a classified event; returns the new row id."""
        orig = event.original_event
        row = {
            "block_number": orig.get("block_number", 0),
            "tx_hash": orig.get("tx_hash", ""),
            "contract_address": orig.get("contract_address", ""),
            "event_type": orig.get("event_type", ""),
            "severity": event.severity.name,
            "details": json.dumps(orig.get("details") or {}),
            "classified_at": datetime.now(timezone.utc).isoformat(),
        }
        cur = self._conn.execute(
            """
            INSERT INTO events
                (block_number, tx_hash, contract_address, event_type, severity, details, classified_at)
            VALUES
                (:block_number, :tx_hash, :contract_address, :event_type, :severity, :details, :classified_at)
            """,
            row,
        )
        self._conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_severity(self, severity: Severity, limit: int = 100) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM events WHERE severity = ? ORDER BY block_number DESC LIMIT ?",
            (severity.name, limit),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_by_contract(self, contract_address: str, limit: int = 100) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM events WHERE contract_address = ? ORDER BY block_number DESC LIMIT ?",
            (contract_address.lower(), limit),
        )
        return [dict(row) for row in cur.fetchall()]

    def get_recent(self, limit: int = 50) -> list[dict]:
        cur = self._conn.execute(
            "SELECT * FROM events ORDER BY block_number DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]

    def count(self) -> int:
        (n,) = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        return n

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._conn.close()
