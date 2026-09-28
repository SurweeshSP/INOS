import numpy as np
import pytest
from typing import Dict

from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense, SolveStatus
from src.solver.milp import solve_milp

def test_trivial_integer_problem():
    """
    min -x1 - x2
    s.t. x1 + x2 <= 1.5
         x1, x2 in {0, 1}
         
    Optimal solution is x1=1, x2=0 or x1=0, x2=1 with obj = -1.0
    """
    model = OptimizationModel(problem_type=ProblemType.MILP)
    
    model.variables["x1"] = VariableMeta("x1", VariableType.BINARY, lb=0.0, ub=1.0)
    model.variables["x2"] = VariableMeta("x2", VariableType.BINARY, lb=0.0, ub=1.0)
    
    model.constraints["c1"] = ConstraintMeta("c1", ConstraintSense.LE, 1.5)
    
    model.A = np.array([[1.0, 1.0]])
    model.b = np.array([1.5])
    model.c = np.array([-1.0, -1.0])
    model.bounds = [(0.0, 1.0), (0.0, 1.0)]
    model.senses = ['L']
    
    result = solve_milp(model)
    
    assert result.status == SolveStatus.OPTIMAL
    assert abs(result.objective_value - (-1.0)) < 1e-6
    x1 = result.primal_values["x1"]
    x2 = result.primal_values["x2"]
    assert (abs(x1 - 1.0) < 1e-6 and abs(x2 - 0.0) < 1e-6) or (abs(x1 - 0.0) < 1e-6 and abs(x2 - 1.0) < 1e-6)

def test_infeasible_milp():
    """
    min x
    s.t. x >= 1.5
         x <= 1.8
         x integer
    """
    model = OptimizationModel(problem_type=ProblemType.MILP)
    
    model.variables["x"] = VariableMeta("x", VariableType.INTEGER, lb=0.0, ub=float('inf'))
    
    model.constraints["c1"] = ConstraintMeta("c1", ConstraintSense.GE, 1.5)
    model.constraints["c2"] = ConstraintMeta("c2", ConstraintSense.LE, 1.8)
    
    model.A = np.array([[1.0], [1.0]])
    model.b = np.array([1.5, 1.8])
    model.c = np.array([1.0])
    model.bounds = [(0.0, float('inf'))]
    model.senses = ['G', 'L']
    
    result = solve_milp(model)
    
    assert result.status == SolveStatus.INFEASIBLE

def test_mixed_integer_problem():
    """
    min -5x1 - 4x2
    s.t. x1 + x2 <= 5
         10x1 + 6x2 <= 45
         x1, x2 integer >= 0
         
    LP relaxed: x1=3.75, x2=1.25, Obj=-23.75
    MILP optimum: x1=4, x2=0 -> obj = -20? No: 4+0=4<=5, 40<=45. Obj=-20.
    Wait: 
    Let's check integer feasible points:
    (4,0): obj = -20
    (3,2): obj = -15 - 8 = -23. Feasible: 3+2=5<=5, 30+12=42<=45. Yes!
    So optimal is x1=3, x2=2, obj=-23
    """
    model = OptimizationModel(problem_type=ProblemType.MILP)
    
    model.variables["x1"] = VariableMeta("x1", VariableType.INTEGER, lb=0.0, ub=float('inf'))
    model.variables["x2"] = VariableMeta("x2", VariableType.INTEGER, lb=0.0, ub=float('inf'))
    
    model.constraints["c1"] = ConstraintMeta("c1", ConstraintSense.LE, 5.0)
    model.constraints["c2"] = ConstraintMeta("c2", ConstraintSense.LE, 45.0)
    
    model.A = np.array([[1.0, 1.0], [10.0, 6.0]])
    model.b = np.array([5.0, 45.0])
    model.c = np.array([-5.0, -4.0])
    model.bounds = [(0.0, float('inf')), (0.0, float('inf'))]
    model.senses = ['L', 'L']
    
    result = solve_milp(model)
    
    assert result.status == SolveStatus.OPTIMAL
    assert abs(result.objective_value - (-23.0)) < 1e-6
    assert abs(result.primal_values["x1"] - 3.0) < 1e-6
    assert abs(result.primal_values["x2"] - 2.0) < 1e-6

def test_empty_milp_model():
    model = OptimizationModel(problem_type=ProblemType.MILP)
    res = solve_milp(model)
    assert res.status == SolveStatus.NOT_SOLVED
