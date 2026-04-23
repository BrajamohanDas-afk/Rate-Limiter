# Walkthrough Script (10-15 Minutes)

## 1) Problem and Scope (1 minute)

- Goal: enforce per-client API limits and expose operator visibility.
- Scope intentionally small: correctness, structure, and testability over feature count.

## 2) Architecture (2 minutes)

- Frontend (React): two pages, Dashboard and Clients.
- Backend (Flask): route layer, middleware, service layer, ORM models.
- Database (relational): clients, rate limit config, request logs.

Key boundary:
- Routes call `rate_limiter.check_and_record()` and do not own algorithm decisions.

## 3) Data Model and Invariants (2 minutes)

- `Client` has one `RateLimitConfig` and many `RequestLog` entries.
- Invariants:
  - requests/window and window seconds must be positive integers.
  - inactive client cannot call gateway (API key auth checks active state).
  - every gateway call is logged with `was_throttled` and `status_code`.

## 4) Core Rate-Limit Flow (3 minutes)

Show `backend/app/services/rate_limiter.py`:

1. Resolve config.
2. Compute window start.
3. Count requests in current window.
4. Decide allowed vs throttled.
5. Record request log.
6. Return limit metadata and retry-after.

Why this design:
- One decision point means algorithm changes stay local.
- Simple to reason about and test.

## 5) API Safety and Validation (2 minutes)

Show examples in `routes/clients.py` and `routes/stats.py`:
- Reject non-object JSON payloads.
- Reject invalid types and out-of-range values.
- Return clear 422/409/404 responses.

## 6) Verification (2 minutes)

Run tests:

```bash
cd backend
pytest app/tests -v
```

Mention what is covered:
- service-level rate-limit invariants
- gateway auth and 429 behavior
- invalid input handling
- stats query validation

## 7) Observability (1 minute)

- Dashboard shows traffic over time and top throttled clients.
- Logs persisted in relational DB make failures and throttling diagnosable.

## 8) AI Usage and Constraints (1 minute)

- AI used for scaffold and initial implementation.
- Constraints documented in `ai-guidance/`.
- Manual review focused on correctness and architecture boundaries.

## 9) Risks, Tradeoffs, and Next Extensions (1-2 minutes)

### Known Weaknesses

**Fixed-window boundary burst**
The biggest algorithmic weakness. A client with a limit of 60 req/min can burst
120 requests by firing 60 at 11:59 and 60 at 12:00 — both windows are clean.
Fix: replace `_count_requests_in_window()` in `rate_limiter.py` with a sliding
window log (query logs in the last N seconds instead of since window start).
Nothing else changes.

**No distributed atomic counter**
Two simultaneous requests at the exact window boundary could both pass the check
before either writes a log. Fine for single-process deployments; fix with Redis
INCR + EXPIRE or Postgres advisory locks for multi-instance.

**API keys stored in plaintext**
Fine for a demo. Production fix: store bcrypt hash, compare on each request.
Adds ~50ms latency per request — acceptable.

**Unbounded request log growth**
Logs are never pruned. Fix: a scheduled job deleting logs older than 24h.
No schema changes required.

### What I'd do next (in order of impact)
1. Sliding window — one function swap, highest correctness gain
2. Log pruning job — prevents eventual DB bloat
3. Redis counters — only needed at multi-instance scale
4. Key hashing — security hardening before any production use