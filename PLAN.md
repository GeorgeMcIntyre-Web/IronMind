# Plan

## Phase 1: MVP (done)
- API endpoints for runs and health.
- IR generation via provider abstraction (stub + OpenAI compatible).
- JSON Schema + Pydantic validation.
- OR-Tools CP-SAT solver integration.
- SQLite persistence with audit trail.
- Tests for IR validation, IR-to-solver conversion, and E2E stub flow.

## Phase 2: Reliability (done)
- CI workflow to run tests on push/PR.
- Developer checklists in `DEV_CHECKLIST.md`.
- Roadmap document in `ROADMAP.md`.

## Phase 3: Next (pending)
- Expand IR coverage (nonlinear, boolean, indicator constraints) only if needed.
- Add structured provider trace logs (no secrets).
- Add opt-in profiling for solver and provider latency.