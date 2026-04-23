# agents.md

This file defines guardrails for any AI agent modifying this repository.

## Primary Constraints

- Keep architecture layered: routes -> services -> models.
- Keep rate-limit decision logic in `backend/app/services/rate_limiter.py` only.
- Do not put business logic in SQLAlchemy models.
- Validate API payloads at route boundary before DB writes.
- Prefer simple, explicit code over abstractions.

## Change Safety Rules

- Preserve public API contracts unless explicitly versioned.
- Add or update tests for every behavior change.
- Do not silently swallow exceptions.
- Keep error codes consistent (`422`, `404`, `409`, `401`, `429`).

## Frontend Rules

- Keep HTTP access centralized in `frontend/src/api/client.js`.
- Avoid embedding endpoint strings in page components.
- Maintain current page-level structure unless there is a clear benefit.

## Data Rules

- Use ORM models; avoid raw SQL strings.
- Keep relational integrity through relationships and cascades.
- Avoid nullable fields that can create invalid states.

## Review Checklist Before Commit

- Does this change preserve rate-limit invariants?
- Are new inputs validated?
- Are new failure modes visible and test-covered?
- Is the change local, or does it create wide coupling?
