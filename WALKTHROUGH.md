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

## 9) Risks and Next Extensions (1 minute)

Current risks:
- fixed-window burst behavior
- no distributed atomic counter
- plaintext demo API keys
- unbounded log growth

Next changes (minimal impact path):
- swap to sliding window in one service function
- move counters to Redis
- hash API keys
- add log retention job
