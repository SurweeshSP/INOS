import pytest
import numpy as np
from src.data_models import OptimizationModel, ProblemType, VariableMeta, ConstraintMeta, ConstraintSense
from src.solver.cpu import solve_cpu
from src.service.validation_service import validation_service

def create_model(offset, problem_type=ProblemType.LP):
    """
    Creates a simple bounded model:
    min (or max) 2*x + 3*y + offset
    s.t.
    x + y = 10
    0 <= x <= 5
    0 <= y <= 10
    
    If LP: Optimal is x=5, y=5. (Cost = 2*5 + 3*5 + offset = 25 + offset)
    """
    import scipy.sparse as sp
    
    c = np.array([2.0, 3.0])
    A = sp.csr_matrix([[1.0, 1.0]])
    b = np.array([10.0])
    lb = np.array([0.0, 0.0])
    ub = np.array([5.0, 10.0])
    senses = ['E']
    
    variables = {
        "x": VariableMeta("x", var_type=1, lb=0.0, ub=5.0, obj_coef=2.0),
        "y": VariableMeta("y", var_type=1, lb=0.0, ub=10.0, obj_coef=3.0)
    }
    
    constraints = {
        "eq1": ConstraintMeta("eq1", sense=ConstraintSense.EQ, rhs=10.0)
    }
    
    return OptimizationModel(
        problem_type=problem_type,
        c=c, A=A, b=b,
        lower_bounds=lb, upper_bounds=ub, senses=senses,
        variables=variables, constraints=constraints,
        objective_offset=offset
    )

@pytest.mark.parametrize("offset", [0.0, 10.0, -10.0])
@pytest.mark.parametrize("problem_type", [ProblemType.LP, ProblemType.MILP, ProblemType.QP])
def test_objective_offset_combinations(offset, problem_type):
    model = create_model(offset, problem_type)
    
    if problem_type == ProblemType.QP:
        import scipy.sparse as sp
        model.Q = sp.eye(2).tocsr() * 0.1 # Add a small quadratic term 0.05*x^2 + 0.05*y^2
        # Optimal LP is x=5, y=5.
        # Cost with Q = 25 + offset + 0.05(25) + 0.05(25) = 25 + 2.5 + offset = 27.5 + offset
    
    # Solve
    solution = solve_cpu(model, options={'time_limit': 5.0})
    
    assert solution.status.name in ("OPTIMAL", "SUBOPTIMAL")
    
    # Validation Service must explicitly recompute
    validation = validation_service.validate_solution(model, solution)
    
    # Verify objective matches
    assert validation.is_valid
    
    # Solver internal objective should exactly match independent recomputation
    # Notice `validation_service` computes `c.T @ x + 0.5 * x.T @ Q @ x + objective_offset` if we update it.
    
    # Due to float precision, we use pytest.approx
    assert solution.objective_value == pytest.approx(validation.objective_recomputed, rel=1e-5)
    
    # Explicitly check the absolute value
    if problem_type in (ProblemType.LP, ProblemType.MILP):
        assert solution.objective_value == pytest.approx(25.0 - offset, rel=1e-5)
    elif problem_type == ProblemType.QP:
        assert solution.objective_value == pytest.approx(35.0 - offset, rel=1e-5)
