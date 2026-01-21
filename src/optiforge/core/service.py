from __future__ import annotations

from optiforge.core.config import Settings
from optiforge.core.models import ProblemSpec, RunRecord
from optiforge.core.provider import get_provider
from optiforge.core.solver import solve_ir
from optiforge.core.storage import RunStore
from optiforge.core.validation import validate_ir_json


def create_run(problem_spec: ProblemSpec, settings: Settings, store: RunStore) -> RunRecord:
    run_id = store.create_run(problem_spec, settings.provider, settings.provider_model)
    return store.get_run(run_id)


def generate_ir(run_id: str, settings: Settings, store: RunStore) -> RunRecord:
    run = store.get_run(run_id)
    api_key = None
    if settings.provider_api_key:
        api_key = settings.provider_api_key.get_secret_value()
    provider = get_provider(
        settings.provider,
        settings.provider_base_url,
        api_key,
        settings.provider_model,
    )
    try:
        ir_data = provider.generate_ir(run.problem_spec)
        ir = validate_ir_json(ir_data)
    except Exception as exc:
        store.update_run_error(run_id, str(exc))
        raise
    return store.update_run_ir(run_id, ir, settings.provider, settings.provider_model)


def solve_run(run_id: str, settings: Settings, store: RunStore) -> RunRecord:
    run = store.get_run(run_id)
    if run.ir is None:
        raise ValueError("run has no IR to solve")
    try:
        result = solve_ir(run.ir, settings.solver_max_seconds)
    except Exception as exc:
        store.update_run_error(run_id, str(exc))
        raise
    status = "solved"
    if result.status == "infeasible":
        status = "infeasible"
    if result.status == "unknown":
        status = "error"
    return store.update_run_solution(run_id, result, status)
