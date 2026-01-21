import json
from pathlib import Path

from optiforge.core.validation import validate_ir_json


def _load_example_ir() -> dict:
    path = Path(__file__).resolve().parents[1] / "examples" / "ir.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_valid_ir_passes() -> None:
    data = _load_example_ir()
    model = validate_ir_json(data)
    assert model.name == "simple_min_cost"


def test_invalid_ir_rejected() -> None:
    data = _load_example_ir()
    data["constraints"][0]["operator"] = "<"
    try:
        validate_ir_json(data)
    except ValueError as exc:
        assert "schema validation" in str(exc)
        return
    raise AssertionError("invalid IR should raise")