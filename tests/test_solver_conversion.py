import json
from pathlib import Path

from optiforge.core.solver import solve_ir
from optiforge.core.validation import validate_ir_json


def _load_example_ir() -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / "ir.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_ir_to_solver_solution() -> None:
    ir = validate_ir_json(_load_example_ir())
    result = solve_ir(ir, max_seconds=5)
    assert result.status in {"optimal", "feasible"}
    assert result.variables["x"] == 0
    assert result.variables["y"] == 5
    assert result.objective_value == 10