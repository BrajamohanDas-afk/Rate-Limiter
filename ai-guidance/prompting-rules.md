# prompting-rules.md

Prompting rules used when working with AI coding tools on this project.

## Required Prompt Sections

1. Goal and scope
2. File ownership and allowed edit paths
3. Non-negotiable architecture constraints
4. Validation and test expectations
5. Output format (diff, changed files, reasoning)

## Default Prompt Template

```text
Task:
<specific change>

Constraints:
- Do not move rate-limit decisions outside backend/app/services/rate_limiter.py
- Keep routes thin and validation-first
- Do not add raw SQL
- Keep changes minimal and local

Tests:
- Add/update tests in backend/app/tests for changed behavior
- Keep existing tests passing

Output:
- List changed files
- Explain tradeoffs and risks
- Mention any unverified assumptions
```

## Red Flags (Reject AI Output)

- Adds logic to route handlers that belongs in service layer
- Introduces hidden side effects or global mutable state
- Skips validation for new fields
- Changes response shapes without migration plan
- Adds dependencies without clear need

## Acceptance Criteria

- Behavior is deterministic and test-covered
- Invalid states are prevented at boundaries
- Change impact remains localized
- Code remains readable under future modifications
