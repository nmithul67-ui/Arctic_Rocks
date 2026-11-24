# GuardPay – Secure Payment Middleware for AI Agents

**GuardPay** is a complete, runnable MVP that demonstrates a policy‑driven escrow and human‑in‑the‑loop (HITL) payment middleware for AI agents. It consists of four components:

1. **backend/** – FastAPI + SQLite engine that enforces budgets, mandates, and policy checks.
2. **mock_merchant/** – A simulated merchant API that returns HTTP 402 payment‑required responses.
3. **mcp_server/** – An Antigravity MCP server exposing GuardPay tools to any MCP‑compatible agent.
4. **frontend/** – A minimal Next.js + Tailwind UI that shows an operator console with live audit logs and approval queues.

The whole stack can be started with a single command (`docker‑compose up`) or via the helper script `start.sh`.

---

## Quick Start (Docker Compose)

```bash
# From the project root directory
./start.sh
```

The script will:
- Build and run all services (backend, merchant, MCP server, frontend).
- Initialise an SQLite database with a default *Daily Ops Mandate* (budget $25, max $10/tx, auto‑approve $5).
- Open the operator console at `http://localhost:3000`.

---

## Directory Layout

```
guardpay/
├─ backend/               # FastAPI policy & escrow engine
│   ├─ app/
│   │   ├─ main.py        # API entry point
│   │   ├─ models.py      # SQLAlchemy models
│   │   ├─ schemas.py     # Pydantic schemas
│   │   └─ policy.py      # Policy evaluation pipeline
│   └─ requirements.txt
├─ mock_merchant/         # Simulated merchant & 402 endpoint
│   ├─ app/
│   │   └─ main.py
│   └─ requirements.txt
├─ mcp_server/            # Antigravity MCP server exposing GuardPay tools
│   ├─ server.py
│   └─ requirements.txt
├─ frontend/              # Next.js UI (dark mode, split‑screen console)
│   ├─ pages/
│   │   └─ index.tsx
│   ├─ components/
│   │   ├─ AuditFeed.tsx
│   │   └─ PendingQueue.tsx
│   ├─ tailwind.config.js
│   └─ package.json
├─ docker-compose.yml
├─ start.sh                # Convenience wrapper
└─ README.md               # (this file)
```

---

## Core Concepts

- **Mandate** – Defines a budget, per‑transaction caps, allowed categories/merchants, and an auto‑approve threshold.
- **PaymentIntent** – Represents a requested spend; moves through states `APPROVED → SETTLED`, `PENDING_HUMAN`, `DENIED`, etc.
- **AuditEvent** – Immutable log of every rule evaluation, stored in SQLite and streamed to the UI via Server‑Sent Events.
- **Human‑in‑the‑Loop** – When a request exceeds the auto‑approve limit, an operator must approve/reject it from the UI before settlement.

---

## Development

- All Python services use FastAPI, SQLAlchemy, and uvicorn. No external API keys are required.
- The frontend uses the standard Next.js + Tailwind starter (`npx create-next-app`).
- The project is deliberately **self‑contained** – you can run it on any machine with Docker.

---

## License

MIT – feel free to fork, extend, and experiment!
