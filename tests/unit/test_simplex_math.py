import pytest
import numpy as np
from src.solver.numerical import NumericalConfig
from src.solver.lp.simplex import RevisedSimplexSolver
from src.data_models import SolveStatus

def test_simplex_math_optimal():
    # Simple LP: 
    # max 3x1 + 2x2 -> min -3x1 - 2x2
    # s.t. x1 + 2x2 <= 4 -> x1 + 2x2 + s1 = 4
    #      x1 + x2 <= 3  -> x1 + x2 + s2 = 3
    #      x1, x2, s1, s2 >= 0
    c = np.array([-3.0, -2.0, 0.0, 0.0])
    A = np.array([
        [1.0, 2.0, 1.0, 0.0],
        [1.0, 1.0, 0.0, 1.0]
    ])
    b = np.array([4.0, 3.0])
    
    solver = RevisedSimplexSolver(NumericalConfig())
    status, x, y, obj = solver.solve(c, A, b)
    
    assert status == SolveStatus.OPTIMAL
    # Optimal solution: x1 = 3, x2 = 0, s1 = 1, s2 = 0
    # Obj = -3(3) - 2(0) = -9
    assert np.allclose(x, [3.0, 0.0, 1.0, 0.0], atol=1e-5)
    assert abs(obj - (-9.0)) < 1e-5

def test_simplex_unbounded():
    # max x1 -> min -x1
    # s.t. x1 - x2 <= 1 -> x1 - x2 + s1 = 1
    # x1, x2, s1 >= 0
    c = np.array([-1.0, 0.0, 0.0])
    A = np.array([
        [1.0, -1.0, 1.0]
    ])
    b = np.array([1.0])
    
    solver = RevisedSimplexSolver(NumericalConfig())
    status, x, y, obj = solver.solve(c, A, b)
    
    assert status == SolveStatus.UNBOUNDED
