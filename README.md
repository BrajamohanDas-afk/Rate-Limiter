# API Rate Limiter + Dashboard

A small assessment project built specifically for this submission.

- Backend: Python + Flask API
- Frontend: React (Vite)
- Database: SQLite for local development (PostgreSQL-ready via `DATABASE_URL`)

The system enforces per-client API limits and exposes a dashboard for request volume, throttle rate, and top throttled clients.

## Why This Project

This project intentionally optimizes for structure, correctness, and safe change over feature count.

- Clear boundaries: route -> service -> database
- Single rate-limit decision point: `backend/app/services/rate_limiter.py`
- Strong input validation and explicit error codes
- Real integration-style tests over an in-memory relational DB
- Audit-friendly request logs for observability

## Repository Structure

```text
backend/
  app/
    config.py
    models.py
    services/rate_limiter.py
    middleware/auth.py
    routes/
      clients.py
      gateway.py
      stats.py
    tests/
      conftest.py
      test_rate_limiter.py
      test_routes.py
  requirements.txt
  run.py

frontend/
  src/
    api/client.js
    pages/Dashboard.jsx
    pages/Clients.jsx
    App.jsx

ai-guidance/
  claude.md
  agents.md
  prompting-rules.md

WALKTHROUGH.md
```

## Quick Start

### 1) Backend

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Backend runs at `http://localhost:5000`.

Notes:
- `run.py` creates tables automatically on startup for local setup.
- Use `DATABASE_URL` to point to PostgreSQL in non-local environments.

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` (proxied to Flask API).

### 3) Tests

```bash
cd backend
pytest app/tests -v
```

## API Summary

### Clients

- `GET /api/clients` list clients
- `POST /api/clients` create client
- `GET /api/clients/<id>` get one client
- `PATCH /api/clients/<id>` update active status and limits
- `DELETE /api/clients/<id>` delete client and related logs

### Gateway (rate-limited)

- `GET|POST|PUT|DELETE /api/gateway/<path>`
- Required header: `X-API-Key: <api_key>`

Success response includes:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`

Throttle response:
- HTTP `429`
- `Retry-After` header

### Stats

- `GET /api/stats/summary`
- `GET /api/stats/timeline?minutes=30` (`minutes` validated: 1-720)
- `GET /api/stats/throttled-clients`
- `GET /api/stats/clients/<id>`

## Key Technical Decisions

1. Rate-limit logic is centralized.
- All decisions are made in `check_and_record()` in `rate_limiter.py`.
- Routes do not implement quota decisions.

2. Validation at the API boundary.
- Routes validate payload shape and field constraints.
- Invalid input returns `422`, conflicts return `409`, missing records return `404`.

3. Fixed-window algorithm for clarity.
- Predictable and easy to verify in tests.
- Sliding-window upgrade is isolated to one service function.

4. Relational schema kept simple.
- `clients`, `rate_limit_configs`, `request_logs`
- Indexed fields support rate checks and dashboard queries.

5. Observability through persisted request logs.
- Every gateway request is recorded with status and throttle flag.
- Dashboard queries use these logs directly.

## Risks and Tradeoffs

- Fixed-window boundary burst: can allow bursts across window edge.
- Single-node DB-backed checks: not ideal for high-scale distributed traffic.
- API key storage is plaintext in this demo.
- Request logs are append-only (needs retention policy in production).

## Extension Path

- Sliding window: replace `_count_requests_in_window()` logic.
- Distributed limit checks: move counters to Redis + atomic operations.
- Secure API keys: hash keys at rest and rotate periodically.
- Log retention: scheduled cleanup or partition strategy.

## AI Usage

AI was used for scaffolding and first-pass code generation, then manually reviewed and corrected.

Review focus areas:
- Rate-limit correctness and edge conditions
- Validation and status-code discipline
- Test isolation and determinism
- Simplicity and architecture boundaries

See guidance files:
- `ai-guidance/claude.md`
- `ai-guidance/agents.md`
- `ai-guidance/prompting-rules.md`

## Walkthrough

Use `WALKTHROUGH.md` for the 10-15 minute walkthrough structure.
