# Base Contract Watchdog — Real-Time Proxy Upgrade & Admin Change Monitor

> **Base Contract Watchdog** provides real-time monitoring of proxy upgrades, admin transfers, and permission changes on Base — so DeFi users and security researchers get instant alerts when smart contract governance changes occur.

[![Built on Base](https://img.shields.io/badge/Built%20on-Base-0052FF?logo=coinbase)](https://base.org)
[![Live Demo](https://img.shields.io/badge/Live-watchdog.warvis.org-brightgreen)](https://watchdog.warvis.org)
[![Tests](https://img.shields.io/badge/Tests-60%20passing-brightgreen)](https://github.com/WooYoungSang/base-contract-watchdog)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)

**Live Demo:** https://watchdog.warvis.org  
**API:** https://api-watchdog.warvis.org/docs

---

## Problem

Base's DeFi ecosystem moves fast — proxy contracts get upgraded, admin keys change, and permission structures shift without warning. Existing block explorers show these events only after the fact, with no severity classification or alerting. Retail users and security researchers have no real-time visibility into governance changes that could affect their funds.

---

## Solution

**Base Contract Watchdog** monitors every block on Base for critical contract events, classifies them by severity (CRITICAL / HIGH / MEDIUM / LOW) using an AI classifier, and serves them through a live dashboard and REST API.

---

## Features

| Feature | Description |
|---------|-------------|
| **F1 — Block Watcher** | Streams every Base block, scans all transactions for governance events |
| **F2 — Upgrade Detector** | Detects `Upgraded(address)` events (EIP-1967 proxy upgrades) |
| **F3 — Admin Detector** | Detects `AdminChanged` and ownership transfers (`OwnershipTransferred`) |
| **F4 — Permission Detector** | Detects `RoleGranted`, `RoleRevoked`, `Paused`, `Unpaused` |
| **F5 — AI Severity Classifier** | Rule-based + ML classifier assigns CRITICAL/HIGH/MEDIUM/LOW per event |
| **F6 — Live Event Dashboard** | Real-time feed with severity badges, contract lookup, stats charts |

---

## Event Severity Model

| Event Type | Default Severity | Escalation Conditions |
|------------|-----------------|----------------------|
| `upgrade` | HIGH | CRITICAL if no timelock, unverified new impl |
| `admin_change` | HIGH | CRITICAL if EOA takes over from multisig |
| `role_granted` | MEDIUM | HIGH if privileged role (ADMIN, PAUSER, MINTER) |
| `role_revoked` | MEDIUM | HIGH if removes all multisig signers |
| `paused` | HIGH | CRITICAL if TVL > $1M |
| `unpaused` | LOW | MEDIUM if paused < 1 block |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Next.js 14 Frontend                     │
│  / (live feed) · /events · /events/[id] · /stats        │
│  /contracts/[address] (per-contract history)            │
└──────────────────────┬──────────────────────────────────┘
                       │ REST (NEXT_PUBLIC_API_URL)
┌──────────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                         │
│  GET /events · /events/{id} · /contracts/{addr}         │
│  GET /stats · /health                                   │
└──┬───────────────────────────────────────────────┬──────┘
   │                                               │
┌──▼──────────────────────────────┐    ┌───────────▼──────┐
│          Block Watcher          │    │   SQLite Storage  │
│  (Base RPC polling)             │    │  (events + stats) │
└──┬──────────────┬───────────────┘    └──────────────────┘
   │              │
   ▼              ▼
Upgrade        Admin &
Detector      Permission
              Detectors
   └──────┬───────┘
          ▼
    AI Severity Classifier
  (Rule-based + ML)
```

---

## Quick Start

### Prerequisites

- Python 3.10+, Node.js 18+
- Base RPC endpoint (public: `https://mainnet.base.org`)

### Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn contract_watchdog.api:app --reload --port 8000

# Run tests (60 tests)
pytest tests/ -v

# Lint
ruff check .
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Docker Compose

```bash
docker compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## API Reference

Base URL: `https://api-watchdog.warvis.org`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/events` | List detected events (paginated) |
| `GET` | `/events?severity=CRITICAL` | Filter by severity |
| `GET` | `/events?event_type=upgrade` | Filter by event type |
| `GET` | `/events/{id}` | Single event detail |
| `GET` | `/contracts/{address}` | All events for a contract |
| `GET` | `/stats` | Aggregate counts by severity and type |

### Example Response

```json
// GET /events?severity=CRITICAL
{
  "items": [
    {
      "id": "0xabc123...",
      "block_number": 14500000,
      "contract_address": "0x1234...",
      "event_type": "upgrade",
      "severity": "CRITICAL",
      "old_value": "0xOldImpl...",
      "new_value": "0xNewImpl...",
      "tx_hash": "0xdef456...",
      "timestamp": "2025-04-17T10:30:00Z",
      "classifier_reason": "Proxy implementation upgraded without timelock"
    }
  ],
  "total": 42,
  "page": 1
}
```

### Interactive Docs

`https://api-watchdog.warvis.org/docs`

---

## Tech Stack

**Backend:** Python 3.10, FastAPI, Pydantic v2, web3.py, SQLite  
**Frontend:** Next.js 14, TypeScript, Tailwind CSS, TanStack Query, Recharts  
**Data:** Base RPC (`mainnet.base.org`), EIP-1967 event decoding  
**Infra:** Docker, Caddy reverse proxy, self-hosted

---

## Project Structure

```
grant-base-contract-watchdog/
├── backend/
│   ├── src/contract_watchdog/
│   │   ├── watcher.py              # Block scanning engine
│   │   ├── detectors/
│   │   │   ├── upgrade_detector.py
│   │   │   ├── admin_detector.py
│   │   │   └── permission_detector.py
│   │   ├── classifier.py           # AI severity classification
│   │   ├── storage.py              # SQLite persistence
│   │   ├── api.py                  # FastAPI application
│   │   └── schemas.py              # Pydantic models
│   └── tests/                      # 60 pytest tests
└── frontend/
    └── src/
        ├── app/                    # Next.js App Router pages
        ├── components/             # EventTable, SeverityBadge, StatsChart
        └── lib/                    # API client
```

---

## Use Cases

- **DeFi users**: Get alerted when a protocol you use upgrades its proxy
- **Security researchers**: Monitor all governance activity on Base in one place
- **Protocol teams**: Audit your own contract governance history
- **Risk bots**: React programmatically to governance changes via REST API

---

## Built for Base Ecosystem Grants

Smart contract governance changes are among the most under-monitored security events in DeFi. A single undetected proxy upgrade or admin key transfer can drain millions. Base Contract Watchdog brings **security transparency** to every Base user.

**Impact metrics:**
- 60 automated tests covering all detector and classifier logic
- Covers all 4 major governance event types (upgrade, admin, role, pause)
- EIP-1967 compliant proxy detection
- Open REST API: any security tool or MEV bot can integrate real-time alerts

---

## Disclaimer

This tool monitors on-chain events and provides information only. Event severity classifications are heuristic-based. Always verify contract changes on a block explorer before taking action.

---

## License

MIT © 2025 Base Contract Watchdog Contributors
