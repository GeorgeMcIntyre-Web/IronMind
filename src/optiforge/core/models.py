from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, model_validator


CellValue = StrictInt | StrictFloat | StrictStr


class TableSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StrictStr = Field(min_length=1)
    columns: list[StrictStr] = Field(min_length=1)
    rows: list[list[CellValue]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_rows(self) -> "TableSpec":
        column_count = len(self.columns)
        if column_count == 0:
            raise ValueError("tables.columns must include at least one column")
        if len(set(self.columns)) != column_count:
            raise ValueError("tables.columns must be unique")
        for row in self.rows:
            if len(row) != column_count:
                raise ValueError("each row must match the number of columns")
        return self


class ProblemSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: StrictStr = Field(min_length=1)
    tables: list[TableSpec] = Field(default_factory=list)


class LinearTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    var: StrictStr = Field(min_length=1)
    coeff: StrictInt


class Constraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["linear"]
    terms: list[LinearTerm] = Field(min_length=1)
    operator: Literal["<=", ">=", "="]
    rhs: StrictInt


class Objective(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sense: Literal["minimize", "maximize"]
    terms: list[LinearTerm] = Field(min_length=1)
    constant: StrictInt = 0


class Variable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: StrictStr = Field(min_length=1)
    type: Literal["int"]
    lower_bound: StrictInt
    upper_bound: StrictInt

    @model_validator(mode="after")
    def validate_bounds(self) -> "Variable":
        if self.lower_bound > self.upper_bound:
            raise ValueError("variable lower_bound must be <= upper_bound")
        return self


class OptimizationModelIR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: StrictStr
    name: StrictStr = Field(min_length=1)
    description: StrictStr | None = None
    variables: list[Variable] = Field(min_length=1)
    constraints: list[Constraint] = Field(default_factory=list)
    objective: Objective

    @model_validator(mode="after")
    def validate_variables(self) -> "OptimizationModelIR":
        names = [variable.name for variable in self.variables]
        if len(set(names)) != len(names):
            raise ValueError("variable names must be unique")
        return self

    @model_validator(mode="after")
    def validate_terms(self) -> "OptimizationModelIR":
        name_set = {variable.name for variable in self.variables}
        for constraint in self.constraints:
            for term in constraint.terms:
                if term.var not in name_set:
                    raise ValueError(f"constraint term references unknown variable: {term.var}")
        for term in self.objective.terms:
            if term.var not in name_set:
                raise ValueError(f"objective term references unknown variable: {term.var}")
        return self


class SolveResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["optimal", "feasible", "infeasible", "unknown"]
    objective_value: StrictInt | None = None
    variables: dict[StrictStr, StrictInt]


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    at: StrictStr
    action: StrictStr
    details: dict[str, Any] = Field(default_factory=dict)


class AuditLog(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metadata: dict[str, Any] = Field(default_factory=dict)
    events: list[AuditEvent] = Field(default_factory=list)


RunStatus = Literal["created", "ir_generated", "solved", "infeasible", "error"]


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictStr
    status: RunStatus
    created_at: StrictStr
    updated_at: StrictStr
    problem_spec: ProblemSpec
    ir: OptimizationModelIR | None = None
    solution: SolveResult | None = None
    audit: AuditLog
    error: StrictStr | None = None
    provider_name: StrictStr | None = None
    provider_model: StrictStr | None = None