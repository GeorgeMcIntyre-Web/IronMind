from __future__ import annotations

import functools
import logging

from fastapi import FastAPI, HTTPException

from optiforge.core.config import get_settings
from optiforge.core.models import ProblemSpec, RunRecord
from optiforge.core.service import create_run, generate_ir, solve_run
from optiforge.core.storage import RunStore

logging.basicConfig(level=get_settings().log_level)

app = FastAPI(title="OptiForge")


@functools.lru_cache(maxsize=1)
def get_store() -> RunStore:
    settings = get_settings()
    return RunStore(settings.database_url)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/runs", response_model=RunRecord)
def create_run_endpoint(problem_spec: ProblemSpec) -> RunRecord:
    settings = get_settings()
    store = get_store()
    try:
        return create_run(problem_spec, settings, store)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/runs/{run_id}/generate", response_model=RunRecord)
def generate_run_endpoint(run_id: str) -> RunRecord:
    settings = get_settings()
    store = get_store()
    try:
        return generate_ir(run_id, settings, store)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/runs/{run_id}/solve", response_model=RunRecord)
def solve_run_endpoint(run_id: str) -> RunRecord:
    settings = get_settings()
    store = get_store()
    try:
        return solve_run(run_id, settings, store)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/runs/{run_id}", response_model=RunRecord)
def get_run_endpoint(run_id: str) -> RunRecord:
    store = get_store()
    try:
        return store.get_run(run_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc