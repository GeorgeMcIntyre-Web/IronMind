# Developer Checklists

## API Developer
- Verify request/response models stay in `src/optiforge/core/models.py`.
- Run `pytest` after endpoint changes.
- Add or update E2E tests if endpoints change.
- Confirm error messages remain clear and action-specific.

## IR + Validation Developer
- Update JSON Schema and Pydantic models together.
- Add validation tests for new schema rules.
- Ensure schema errors stay descriptive and deterministic.

## Solver Developer
- Keep guard clauses and avoid 3+ nesting levels.
- Update solver conversion test if constraints change.
- Confirm infeasible cases are recorded in audit trail.

## Storage Developer
- Preserve audit metadata updates.
- Validate that new fields are serialized and read back correctly.
- Ensure migrations are backwards compatible when possible.

## Test Developer
- Keep tests fully offline and deterministic.
- Avoid network calls by using the stub provider.
- Use examples from `examples/` for regression stability.