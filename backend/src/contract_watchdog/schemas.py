"""Pydantic v2 response models for the Contract Watchdog API."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    block_number: int
    tx_hash: str
    contract_address: str
    event_type: str
    severity: SeverityEnum
    details: dict[str, Any]
    classified_at: str

    @classmethod
    def from_row(cls, row: dict) -> EventResponse:
        import json

        details = row.get("details", "{}")
        if isinstance(details, str):
            details = json.loads(details)
        return cls(
            id=row["id"],
            block_number=row["block_number"],
            tx_hash=row["tx_hash"],
            contract_address=row["contract_address"],
            event_type=row["event_type"],
            severity=SeverityEnum(row["severity"]),
            details=details,
            classified_at=row["classified_at"],
        )


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int


class EventListResponse(BaseModel):
    items: list[EventResponse]
    pagination: PaginationMeta


class SeverityStats(BaseModel):
    severity: SeverityEnum
    count: int


class ContractActivity(BaseModel):
    contract_address: str
    event_count: int


class StatsResponse(BaseModel):
    total_events: int
    by_severity: list[SeverityStats]
    most_active_contracts: list[ContractActivity]


class HealthResponse(BaseModel):
    status: str
    version: str
    watcher_running: bool
