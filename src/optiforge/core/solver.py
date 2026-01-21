from __future__ import annotations

from ortools.sat.python import cp_model

from optiforge.core.models import OptimizationModelIR, SolveResult


def solve_ir(ir: OptimizationModelIR, max_seconds: int) -> SolveResult:
    model = cp_model.CpModel()
    variables = {}
    for variable in ir.variables:
        variables[variable.name] = model.NewIntVar(
            variable.lower_bound, variable.upper_bound, variable.name
        )
    for constraint in ir.constraints:
        expr = sum(term.coeff * variables[term.var] for term in constraint.terms)
        if constraint.operator == "<=":
            model.Add(expr <= constraint.rhs)
        if constraint.operator == ">=":
            model.Add(expr >= constraint.rhs)
        if constraint.operator == "=":
            model.Add(expr == constraint.rhs)
    objective_expr = sum(
        term.coeff * variables[term.var] for term in ir.objective.terms
    ) + ir.objective.constant
    if ir.objective.sense == "minimize":
        model.Minimize(objective_expr)
    if ir.objective.sense == "maximize":
        model.Maximize(objective_expr)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_seconds
    status = solver.Solve(model)
    status_name = _status_name(status)
    if status_name in {"optimal", "feasible"}:
        values = {name: int(solver.Value(var)) for name, var in variables.items()}
        return SolveResult(
            status=status_name,
            objective_value=int(solver.ObjectiveValue()),
            variables=values,
        )
    return SolveResult(status=status_name, objective_value=None, variables={})


def _status_name(status: int) -> str:
    if status == cp_model.OPTIMAL:
        return "optimal"
    if status == cp_model.FEASIBLE:
        return "feasible"
    if status == cp_model.INFEASIBLE:
        return "infeasible"
    if status == cp_model.MODEL_INVALID:
        return "unknown"
    if status == cp_model.UNKNOWN:
        return "unknown"
    return "unknown"