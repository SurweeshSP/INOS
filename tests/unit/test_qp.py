import numpy as np
import pytest
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense, SolveStatus
from src.solver.qp import solve_qp

def test_unconstrained_convex_qp():
    """
    min x1^2 + x2^2 - 2x1 - 6x2
    which is min 1/2 x^T Q x + c^T x
    where Q = [[2, 0], [0, 2]], c = [-2, -6]
    Optimum is at x1=1, x2=3. Obj = 1+9 - 2 - 18 = -10
    """
    model = OptimizationModel(problem_type=ProblemType.QP)
    model.variables["x1"] = VariableMeta("x1", VariableType.CONTINUOUS, lb=-float('inf'))
    model.variables["x2"] = VariableMeta("x2", VariableType.CONTINUOUS, lb=-float('inf'))
    
    model.Q = np.array([[2.0, 0.0], [0.0, 2.0]])
    model.c = np.array([-2.0, -6.0])
    model.bounds = [(-float('inf'), float('inf')), (-float('inf'), float('inf'))]
    
    res = solve_qp(model)
    
    assert res.status == SolveStatus.OPTIMAL
    assert abs(res.objective_value - (-10.0)) < 1e-5
    assert abs(res.primal_values["x1"] - 1.0) < 1e-5
    assert abs(res.primal_values["x2"] - 3.0) < 1e-5

def test_equality_constrained_qp():
    """
    min x1^2 + x2^2
    s.t. x1 + x2 = 2
    
    Q = [[2, 0], [0, 2]], c = [0, 0]
    A_eq = [[1, 1]], b_eq = [2]
    Optimum: x1=1, x2=1, Obj = 2
    """
    model = OptimizationModel(problem_type=ProblemType.QP)
    model.variables["x1"] = VariableMeta("x1", VariableType.CONTINUOUS, lb=-float('inf'))
    model.variables["x2"] = VariableMeta("x2", VariableType.CONTINUOUS, lb=-float('inf'))
    
    model.Q = np.array([[2.0, 0.0], [0.0, 2.0]])
    model.c = np.array([0.0, 0.0])
    model.A = np.array([[1.0, 1.0]])
    model.b = np.array([2.0])
    model.bounds = [(-float('inf'), float('inf')), (-float('inf'), float('inf'))]
    model.senses = ['E']
    
    res = solve_qp(model)
    
    assert res.status == SolveStatus.OPTIMAL
    assert abs(res.objective_value - 2.0) < 1e-5
    assert abs(res.primal_values["x1"] - 1.0) < 1e-5
    assert abs(res.primal_values["x2"] - 1.0) < 1e-5

def test_inequality_constrained_qp():
    """
    min x1^2 + x2^2
    s.t. x1 + x2 >= 2
    
    Since we don't have constraints yet, let's encode it.
    Q = [[2, 0], [0, 2]], c = [0, 0]
    A_in = [[1, 1]], b_in = [2], sense = 'G'
    Optimum: x1=1, x2=1, Obj = 2
    """
    model = OptimizationModel(problem_type=ProblemType.QP)
    model.variables["x1"] = VariableMeta("x1", VariableType.CONTINUOUS, lb=-float('inf'))
    model.variables["x2"] = VariableMeta("x2", VariableType.CONTINUOUS, lb=-float('inf'))
    
    model.Q = np.array([[2.0, 0.0], [0.0, 2.0]])
    model.c = np.array([0.0, 0.0])
    model.A = np.array([[1.0, 1.0]])
    model.b = np.array([2.0])
    model.bounds = [(-float('inf'), float('inf')), (-float('inf'), float('inf'))]
    model.senses = ['G']
    
    res = solve_qp(model)
    
    assert res.status == SolveStatus.OPTIMAL
    assert abs(res.objective_value - 2.0) < 1e-5
    assert abs(res.primal_values["x1"] - 1.0) < 1e-5
    assert abs(res.primal_values["x2"] - 1.0) < 1e-5

def test_bounded_qp():
    """
    min x^2 - 4x
    s.t. x >= 3
    Optimum x=3, Obj = 9 - 12 = -3
    Q = [[2]], c = [-4]
    bound: [3, inf]
    """
    model = OptimizationModel(problem_type=ProblemType.QP)
    model.variables["x"] = VariableMeta("x", VariableType.CONTINUOUS, lb=3.0)
    
    model.Q = np.array([[2.0]])
    model.c = np.array([-4.0])
    model.bounds = [(3.0, float('inf'))]
    
    res = solve_qp(model)
    
    assert res.status == SolveStatus.OPTIMAL
    assert abs(res.objective_value - (-3.0)) < 1e-5
    assert abs(res.primal_values["x"] - 3.0) < 1e-5

def test_empty_qp_model():
    model = OptimizationModel(problem_type=ProblemType.QP)
    res = solve_qp(model)
    assert res.status == SolveStatus.NOT_SOLVED
