from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from optiforge.core.models import AuditEvent, AuditLog, OptimizationModelIR, ProblemSpec, RunRecord, SolveResult


class RunStore:
    def __init__(self, database_url: str) -> None:
        self._db_path = _db_path(database_url)
        self._ensure_directory(self._db_path)
        self._init_db()

    def create_run(
        self, problem_spec: ProblemSpec, provider_name: str | None, provider_model: str | None
    ) -> str:
        run_id = str(uuid.uuid4())
        created_at = _now_iso()
        audit = AuditLog(
            metadata={"provider_name": provider_name, "provider_model": provider_model},
            events=[AuditEvent(at=created_at, action="created", details={})],
        )
        payload = {
            "id": run_id,
            "status": "created",
            "created_at": created_at,
            "updated_at": created_at,
            "problem_spec_json": _serialize(problem_spec),
            "ir_json": None,
            "solution_json": None,
            "audit_json": _serialize(audit),
            "error": None,
            "provider_name": provider_name,
            "provider_model": provider_model,
        }
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    id, status, created_at, updated_at, problem_spec_json, ir_json,
                    solution_json, audit_json, error, provider_name, provider_model
                ) VALUES (
                    :id, :status, :created_at, :updated_at, :problem_spec_json, :ir_json,
                    :solution_json, :audit_json, :error, :provider_name, :provider_model
                )
                """,
                payload,
            )
        return run_id

    def get_run(self, run_id: str) -> RunRecord:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if not row:
            raise KeyError("run not found")
        return _row_to_run_record(row)

    def update_run_ir(
        self, run_id: str, ir: OptimizationModelIR, provider_name: str | None, provider_model: str | None
    ) -> RunRecord:
        return self._update_run(
            run_id,
            status="ir_generated",
            ir_json=_serialize(ir),
            provider_name=provider_name,
            provider_model=provider_model,
            audit_action="ir_generated",
            audit_details={"schema_version": ir.version},
            error=None,
        )

    def update_run_solution(self, run_id: str, solution: SolveResult, status: str) -> RunRecord:
        return self._update_run(
            run_id,
            status=status,
            solution_json=_serialize(solution),
            audit_action="solved",
            audit_details={"status": status},
            error=None,
        )

    def update_run_error(self, run_id: str, message: str) -> RunRecord:
        return self._update_run(
            run_id,
            status="error",
            audit_action="error",
            audit_details={"message": message},
            error=message,
        )

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    problem_spec_json TEXT NOT NULL,
                    ir_json TEXT,
                    solution_json TEXT,
                    audit_json TEXT NOT NULL,
                    error TEXT,
                    provider_name TEXT,
                    provider_model TEXT
                )
                """
            )

    def _update_run(
        self,
        run_id: str,
        status: str,
        ir_json: str | None = None,
        solution_json: str | None = None,
        provider_name: str | None = None,
        provider_model: str | None = None,
        audit_action: str | None = None,
        audit_details: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> RunRecord:
        run = self.get_run(run_id)
        audit = run.audit
        if audit_action:
            audit.events.append(
                AuditEvent(at=_now_iso(), action=audit_action, details=audit_details or {})
            )
        if provider_name is not None:
            audit.metadata["provider_name"] = provider_name
        if provider_model is not None:
            audit.metadata["provider_model"] = provider_model
        final_ir_json = ir_json
        if final_ir_json is None and run.ir:
            final_ir_json = run.ir.model_dump_json()
        final_solution_json = solution_json
        if final_solution_json is None and run.solution:
            final_solution_json = run.solution.model_dump_json()
        final_provider_name = provider_name
        if final_provider_name is None:
            final_provider_name = run.provider_name
        final_provider_model = provider_model
        if final_provider_model is None:
            final_provider_model = run.provider_model
        payload = {
            "id": run_id,
            "status": status,
            "updated_at": _now_iso(),
            "ir_json": final_ir_json,
            "solution_json": final_solution_json,
            "audit_json": _serialize(audit),
            "error": error,
            "provider_name": final_provider_name,
            "provider_model": final_provider_model,
        }
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = :status,
                    updated_at = :updated_at,
                    ir_json = :ir_json,
                    solution_json = :solution_json,
                    audit_json = :audit_json,
                    error = :error,
                    provider_name = :provider_name,
                    provider_model = :provider_model
                WHERE id = :id
                """,
                payload,
            )
        return self.get_run(run_id)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _ensure_directory(path: str) -> None:
        directory = Path(path).parent
        directory.mkdir(parents=True, exist_ok=True)


def _db_path(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        return database_url.replace("sqlite:///", "", 1)
    if database_url.startswith("sqlite://"):
        raise ValueError("sqlite URL must be sqlite:///path")
    return database_url


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize(obj: Any) -> str:
    payload = obj
    if hasattr(obj, "model_dump"):
        payload = obj.model_dump()
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def _row_to_run_record(row: sqlite3.Row) -> RunRecord:
    problem_spec = ProblemSpec.model_validate(json.loads(row["problem_spec_json"]))
    ir = None
    if row["ir_json"]:
        ir = OptimizationModelIR.model_validate(json.loads(row["ir_json"]))
    solution = None
    if row["solution_json"]:
        solution = SolveResult.model_validate(json.loads(row["solution_json"]))
    audit = AuditLog.model_validate(json.loads(row["audit_json"]))
    return RunRecord(
        id=row["id"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        problem_spec=problem_spec,
        ir=ir,
        solution=solution,
        audit=audit,
        error=row["error"],
        provider_name=row["provider_name"],
        provider_model=row["provider_model"],
    )
