from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import ValidationError as PydanticValidationError

from optiforge.core.models import OptimizationModelIR


def _schema_path() -> Path:
    return Path(__file__).resolve().parents[3] / "schemas" / "optimization_model_ir.schema.json"


def load_ir_schema() -> dict[str, Any]:
    schema_path = _schema_path()
    schema_text = schema_path.read_text(encoding="utf-8")
    schema = json.loads(schema_text)
    return schema


def validate_ir_json(data: dict[str, Any]) -> OptimizationModelIR:
    schema = load_ir_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
    if errors:
        details = "; ".join([_format_schema_error(error) for error in errors])
        raise ValueError(f"IR schema validation failed: {details}")
    try:
        model = OptimizationModelIR.model_validate(data)
    except PydanticValidationError as exc:
        raise ValueError(f"IR pydantic validation failed: {exc}") from exc
    return model


def parse_ir_json(raw_json: str) -> OptimizationModelIR:
    data = json.loads(raw_json)
    return validate_ir_json(data)


def _format_schema_error(error: Exception) -> str:
    if not hasattr(error, "message"):
        return "invalid IR"
    path = "./" + "/".join([str(segment) for segment in error.path])
    return f"{path}: {error.message}"