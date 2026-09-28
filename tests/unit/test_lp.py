import pytest
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, SolveStatus
from src.solver.cpu import solve_cpu

def test_lp_cpu_solve():
    import numpy as np
    import scipy.sparse as sp
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables["x1"] = VariableMeta(name="x1", var_type=VariableType.CONTINUOUS)
    model.c = np.array([0.0])
    model.lower_bounds = np.array([0.0])
    model.upper_bounds = np.array([float('inf')])
    model.A = sp.csr_matrix((0, 1))
    model.b = np.array([])
    model.senses = []
    
    # Test simplex delegator
    res_simplex = solve_cpu(model, options={'method': 'simplex'})
    assert res_simplex.status == SolveStatus.OPTIMAL
    assert res_simplex.objective_value == 0.0
    assert "x1" in res_simplex.primal_values
    
    # Test interior point delegator
    res_ip = solve_cpu(model, options={'method': 'interior_point'})
    assert res_ip.status == SolveStatus.OPTIMAL
    assert res_ip.objective_value == 0.0

def test_empty_model():
    model = OptimizationModel(problem_type=ProblemType.LP)
    res = solve_cpu(model)
    assert res.status == SolveStatus.ERROR
