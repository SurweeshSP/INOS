import pytest
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, SolutionRecord, SolveStatus, PersistentOptimizationState
from src.solver.cpu import solve_cpu
from src.solver.simplex import solve_lp_simplex
from src.solver.branch_bound import solve_branch_and_bound

def test_warm_start_lp_valid():
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables["x1"] = VariableMeta(name="x1", var_type=VariableType.CONTINUOUS)
    model.variables["x2"] = VariableMeta(name="x2", var_type=VariableType.CONTINUOUS)
    
    state = PersistentOptimizationState(model_version="v1")
    state.previous_solution = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={"x1": 1.0, "x2": 2.0}
    )
    
    res = solve_lp_simplex(model, options={'warm_start': True}, state=state)
    assert res.warm_start_requested is True
    assert res.warm_start_used is True
    assert res.warm_start_valid is True
    assert res.iterations < 50
    assert res.primal_values["x1"] == 1.0
    assert res.primal_values["x2"] == 2.0

def test_warm_start_lp_invalid():
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables["y1"] = VariableMeta(name="y1", var_type=VariableType.CONTINUOUS)
    
    state = PersistentOptimizationState(model_version="v1")
    state.previous_solution = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={"x1": 1.0}
    )
    
    res = solve_lp_simplex(model, options={'warm_start': True}, state=state)
    assert res.warm_start_requested is True
    assert res.warm_start_used is False
    assert res.warm_start_rejected is True
    assert res.warm_start_reason == "Insufficient overlap with previous solution"

def test_warm_start_qp_rejected():
    model = OptimizationModel(problem_type=ProblemType.QP)
    model.variables["x1"] = VariableMeta(name="x1", var_type=VariableType.CONTINUOUS)
    
    state = PersistentOptimizationState(model_version="v1")
    state.previous_solution = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={"x1": 1.0}
    )
    
    res = solve_cpu(model, options={'warm_start': True}, state=state)
    assert res.warm_start_requested is True
    assert res.warm_start_used is False
    assert res.warm_start_rejected is True
    assert "not support warm start" in res.warm_start_reason
