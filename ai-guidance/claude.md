# claude.md

AI guidance for contributors using Claude/Copilot/other assistants on this repository.

## Project Goal

Build a small, correct, and maintainable API rate limiter with a simple React dashboard.

## Non-Negotiable Rules

1. Rate-limit decisions live in one place:
- `backend/app/services/rate_limiter.py`

2. Routes stay thin:
- validate inputs
- call service functions
- format responses

3. Models stay simple:
- relationships + serialization only
- no business rules in models

4. Keep logic testable:
- every behavior change must include tests under `backend/app/tests`

5. Preserve interface safety:
- invalid payloads return `422`
- missing entities return `404`
- conflicts return `409`
- auth failures return `401`
- exceeded quota returns `429`

## Allowed and Preferred Changes

- Add routes under `backend/app/routes`
- Add service helpers under `backend/app/services`
- Add dashboard views/components in `frontend/src`
- Improve test coverage for edge cases

## Avoid

- Raw SQL strings
- Hidden global state
- Business logic in route handlers
- Over-engineered abstractions for this project size

## Extension Strategy

- Sliding window algorithm: replace counting logic in `rate_limiter.py`
- Distributed scaling: Redis counters + atomic operations
- Security hardening: hash API keys and add admin auth

## Review Focus After AI Generation

- correctness of rate-limit math
- boundary validation and status codes
- test realism (prefer real DB fixture over mocks)
- code readability and local change impact
