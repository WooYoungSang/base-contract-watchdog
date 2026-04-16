"""FastAPI application for Contract Watchdog — proxy upgrade & admin change monitoring."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from contract_watchdog.classifier import SeverityClassifier
from contract_watchdog.detectors import AdminDetector, PermissionDetector, UpgradeDetector
from contract_watchdog.schemas import (
    ContractActivity,
    EventListResponse,
    EventResponse,
    HealthResponse,
    PaginationMeta,
    SeverityEnum,
    SeverityStats,
    StatsResponse,
)
from contract_watchdog.storage import EventStorage
from contract_watchdog.watcher import BlockWatcher, WatcherConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons (set up in lifespan)
# ---------------------------------------------------------------------------
_storage: EventStorage | None = None
_watcher: BlockWatcher | None = None
_watcher_task: asyncio.Task | None = None

VERSION = "0.1.0"

# Top-10 TVL protocols on Base (sample set — extend via env/config)
TOP_TVL_PROTOCOLS: set[str] = {
    "0x4200000000000000000000000000000000000010",  # Base Bridge
    "0x3154cf16ccdb4c6d922629664174b904d80f2c35",  # Aerodrome Finance
    "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",  # USDC
    "0x2ae3f1ec7f1f5012cfeab0185bfc7aa3cf0dec22",  # cbETH
    "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca",  # USDbC
}


# ---------------------------------------------------------------------------
# Lifespan — start/stop background watcher
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _storage, _watcher, _watcher_task

    _storage = EventStorage()  # in-memory for now; pass db path via env for persistence
    detectors = [UpgradeDetector(), AdminDetector(), PermissionDetector()]
    classifier = SeverityClassifier(top_tvl_protocols=TOP_TVL_PROTOCOLS)

    async def on_block(block: dict) -> None:
        """Pipeline: block → detectors → classifier → storage."""
        import os

        from web3 import AsyncWeb3
        from web3.providers import AsyncHTTPProvider

        rpc_url = os.environ.get("BASE_RPC_HTTP", "")
        if not rpc_url:
            return  # no RPC configured; skip live log fetching

        w3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        block_num = block.get("number")
        if block_num is None:
            return

        try:
            logs = await w3.eth.get_logs(
                {
                    "fromBlock": block_num,
                    "toBlock": block_num,
                    "topics": [
                        [
                            d_topic
                            for det in detectors
                            for d_topic in det.WATCHED_TOPICS
                        ]
                    ],
                }
            )
        except Exception as exc:
            logger.warning("Failed to fetch logs for block %d: %s", block_num, exc)
            return

        for log in logs:
            for det in detectors:
                result = det.process_log(dict(log))
                if result:
                    classified = classifier.classify(result)
                    _storage.save(classified)
                    break  # one detector per log

    rpc_http = __import__("os").environ.get("BASE_RPC_HTTP", "http://localhost:8545")
    rpc_ws = __import__("os").environ.get("BASE_RPC_WS")
    config = WatcherConfig(rpc_http_url=rpc_http, rpc_ws_url=rpc_ws)
    _watcher = BlockWatcher(config=config, on_block_callbacks=[on_block])

    # Start watcher in background (non-blocking startup)
    _watcher_task = asyncio.create_task(_safe_watcher_start(_watcher))

    yield

    # Shutdown
    if _watcher:
        _watcher.stop()
    if _watcher_task:
        _watcher_task.cancel()
        try:
            await _watcher_task
        except (asyncio.CancelledError, Exception):
            pass
    if _storage:
        _storage.close()


async def _safe_watcher_start(watcher: BlockWatcher) -> None:
    try:
        await watcher.start()
    except asyncio.CancelledError:
        pass
    except Exception as exc:
        logger.error("Block watcher terminated: %s", exc)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Contract Watchdog",
    description="Real-time proxy upgrade and admin change monitoring for Base",
    version=VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def get_storage() -> EventStorage:
    if _storage is None:
        raise HTTPException(status_code=503, detail="Storage not initialised")
    return _storage


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=VERSION,
        watcher_running=_watcher is not None and _watcher._running,
    )


@app.get("/events", response_model=EventListResponse, tags=["events"])
def list_events(
    severity: Annotated[SeverityEnum | None, Query(description="Filter by severity")] = None,
    event_type: Annotated[str | None, Query(description="Filter by event_type")] = None,
    contract: Annotated[str | None, Query(description="Filter by contract address")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 20,
    storage: EventStorage = Depends(get_storage),
) -> EventListResponse:
    rows = _query_events(storage, severity=severity, event_type=event_type, contract=contract)
    return _paginate(rows, page, page_size)


@app.get("/events/{event_id}", response_model=EventResponse, tags=["events"])
def get_event(event_id: int, storage: EventStorage = Depends(get_storage)) -> EventResponse:
    row = _get_event_by_id(storage, event_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return EventResponse.from_row(row)


@app.get("/contracts/{address}/events", response_model=EventListResponse, tags=["events"])
def contract_events(
    address: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 20,
    storage: EventStorage = Depends(get_storage),
) -> EventListResponse:
    rows = storage.get_by_contract(address.lower())
    return _paginate(rows, page, page_size)


@app.get("/stats", response_model=StatsResponse, tags=["meta"])
def stats(storage: EventStorage = Depends(get_storage)) -> StatsResponse:
    conn = storage._conn

    total = storage.count()

    sev_rows = conn.execute(
        "SELECT severity, COUNT(*) as cnt FROM events GROUP BY severity ORDER BY cnt DESC"
    ).fetchall()
    by_severity = [SeverityStats(severity=SeverityEnum(r["severity"]), count=r["cnt"]) for r in sev_rows]

    contract_rows = conn.execute(
        "SELECT contract_address, COUNT(*) as cnt FROM events GROUP BY contract_address ORDER BY cnt DESC LIMIT 10"
    ).fetchall()
    most_active = [
        ContractActivity(contract_address=r["contract_address"], event_count=r["cnt"])
        for r in contract_rows
    ]

    return StatsResponse(
        total_events=total,
        by_severity=by_severity,
        most_active_contracts=most_active,
    )


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def _query_events(
    storage: EventStorage,
    severity: SeverityEnum | None,
    event_type: str | None,
    contract: str | None,
) -> list[dict]:
    clauses = []
    params: list = []

    if severity:
        clauses.append("severity = ?")
        params.append(severity.value)
    if event_type:
        clauses.append("event_type = ?")
        params.append(event_type)
    if contract:
        clauses.append("contract_address = ?")
        params.append(contract.lower())

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"SELECT * FROM events {where} ORDER BY block_number DESC"
    rows = storage._conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _get_event_by_id(storage: EventStorage, event_id: int) -> dict | None:
    row = storage._conn.execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()
    return dict(row) if row else None


def _paginate(rows: list[dict], page: int, page_size: int) -> EventListResponse:
    total = len(rows)
    pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    chunk = rows[start : start + page_size]
    return EventListResponse(
        items=[EventResponse.from_row(r) for r in chunk],
        pagination=PaginationMeta(total=total, page=page, page_size=page_size, pages=pages),
    )
