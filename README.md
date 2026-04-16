# Base Contract Watchdog — Real-Time Proxy Upgrade & Admin Change Monitor

> **Base Contract Watchdog** provides real-time monitoring of proxy upgrades, admin transfers, and permission changes on Base — so DeFi users and security researchers get instant alerts when smart contract governance changes occur.

[![Built on Base](https://img.shields.io/badge/Built%20on-Base-0052FF?logo=coinbase)](https://base.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)

---

## Problem

Base's DeFi ecosystem moves fast — proxy contracts get upgraded, admin keys change, and permission structures shift without warning. Existing block explorers show these events only after the fact, with no severity classification or alerting. Retail users and security researchers have no real-time visibility into governance changes that could affect their funds.

---

## Solution

**Base Contract Watchdog** monitors every block on Base for critical contract events, classifies them by severity using an AI classifier, and serves them through a live dashboard and REST API.

---

## Features

| Feature | Description |
|---------|-------------|
| **F1 — Block Watcher** | Streams blocks via Base RPC, scans every transaction for monitored events |
| **F2 — Upgrade Detector** | Detects `Upgraded(address)` events (EIP-1967 proxy upgrades) |
| **F3 — Admin Detector** | Detects `AdminChanged(address,address)` and ownership transfers |
| **F4 — Permission Detector** | Detects `RoleGranted`, `RoleRevoked`, `Paused`, `Unpaused` events |
| **F5 — AI Severity Classifier** | Rule-based + ML classifier assigns CRITICAL/HIGH/MEDIUM/LOW severity |
| **F6 — Event Dashboard** | Live feed of events with severity badges, contract lookup, stats charts |

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
│  (Base RPC polling/websocket)   │    │  (events + stats) │
└──┬──────────────┬───────────────┘    └──────────────────┘
   │              │
   ▼              ▼
Upgrade        Admin &
Detector      Permission
              Detectors
   │              │
   └──────┬───────┘
          ▼
    AI Classifier
  (CRITICAL/HIGH/
   MEDIUM/LOW)
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Base RPC endpoint (public: `https://mainnet.base.org`)

### Backend

```bash
cd backend
pip install -e ".[dev]"

# Run API server
uvicorn contract_watchdog.api:app --reload --port 8000

# Run tests
pytest tests/ -v

# Lint
ruff check .
```

### Frontend

```bash
cd frontend
npm install

# Development
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

# Production build
npm run build
npm run lint
```

### Docker Compose (full stack)

```bash
# Set your Alchemy API key (or use public RPC)
export ALCHEMY_API_KEY=your_key_here

docker compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

---

## API Reference

Base URL: `http://localhost:8000`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/events` | List detected events (paginated) |
| `GET` | `/events?severity=CRITICAL` | Filter by severity |
| `GET` | `/events?event_type=upgrade` | Filter by event type |
| `GET` | `/events/{id}` | Single event detail |
| `GET` | `/contracts/{address}` | All events for a contract |
| `GET` | `/stats` | Aggregate counts by severity/type |

### Event Types

| Type | Severity Range | Description |
|------|---------------|-------------|
| `upgrade` | CRITICAL–HIGH | Proxy implementation changed |
| `admin_change` | CRITICAL–HIGH | Admin/owner address changed |
| `role_granted` | HIGH–MEDIUM | Access control role assigned |
| `role_revoked` | HIGH–MEDIUM | Access control role removed |
| `paused` | HIGH | Contract emergency pause |
| `unpaused` | MEDIUM | Contract resume after pause |

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
      "timestamp": "2024-01-15T10:30:00Z",
      "classifier_reason": "Proxy implementation upgraded without timelock"
    }
  ],
  "total": 42,
  "page": 1
}
```

### Interactive Docs

Visit `http://localhost:8000/docs` for the auto-generated Swagger UI.

---

## Tech Stack

**Backend**
- Python 3.10, FastAPI, Pydantic v2
- web3.py (Base block watching & event decoding)
- Rule-based + ML severity classifier
- SQLite (event storage)

**Frontend**
- Next.js 14, TypeScript, Tailwind CSS
- TanStack Query (live polling + caching)
- Recharts (event timeline, stats charts)
- Real-time severity badges (CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=blue)

**Infrastructure**
- Docker Compose (local full-stack)
- Base RPC: `https://mainnet.base.org`

---

## Project Structure

```
grant-base-contract-watchdog/
├── backend/
│   ├── src/contract_watchdog/
│   │   ├── watcher.py           # Block scanning engine
│   │   ├── detectors/
│   │   │   ├── upgrade_detector.py
│   │   │   ├── admin_detector.py
│   │   │   └── permission_detector.py
│   │   ├── classifier.py        # AI severity classification
│   │   ├── storage.py           # SQLite persistence
│   │   ├── api.py               # FastAPI application
│   │   └── schemas.py           # Pydantic models
│   └── tests/                   # pytest test suite
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── components/              # EventTable, SeverityBadge, etc.
│   └── lib/                     # API client
└── docker-compose.yml
```

---

## Use Cases

- **DeFi users**: Get alerted when a protocol you use upgrades its proxy contract
- **Security researchers**: Monitor all upgrade activity on Base in one place
- **Protocol teams**: Audit your own contract governance history
- **MEV/risk bots**: React programmatically to governance changes via REST API

---

## Safety & Disclaimers

- This tool monitors on-chain events and provides information only
- Event severity classifications are heuristic-based and not guaranteed to be complete
- Always verify contract changes on a block explorer before taking action
- Not financial advice

---

## Built for Base Builder Grants

Base Contract Watchdog improves the safety infrastructure of the Base ecosystem by providing transparent, real-time monitoring of smart contract governance changes. This helps users make better-informed decisions and reduces the information asymmetry between protocol insiders and retail users.

---

## License

MIT © 2024 Base Contract Watchdog Contributors

---

*Built with ❤️ on Base*
