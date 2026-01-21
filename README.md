# OptiForge

OptiMind-first optimization sandbox MVP. Provide a ProblemSpec, generate an OptimizationModelIR, validate it, solve with CP-SAT, and persist runs with full audit metadata in SQLite.

## Quickstart (PowerShell)

Create venv:

```powershell
python -m venv .venv
```

Activate venv:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install:

```powershell
pip install -r requirements.txt
```

Run server:

```powershell
uvicorn optiforge.api.main:app --reload
```

Run tests:

```powershell
pytest
```

## Configuration

- Copy `.env.example` to `.env` and adjust values if needed.
- Default provider is `stub` to keep everything offline.

## Endpoints

- `POST /api/runs` - create a run
- `POST /api/runs/{id}/generate` - generate and validate IR
- `POST /api/runs/{id}/solve` - solve using CP-SAT
- `GET /api/runs/{id}` - fetch run data
- `GET /health` - health check

## Examples

- ProblemSpec: `examples/problem_spec.json`
- IR: `examples/ir.json`

## Project Docs

- Plan: `PLAN.md`
- Roadmap: `ROADMAP.md`
- Developer checklists: `DEV_CHECKLIST.md`
