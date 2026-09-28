import pytest
from src.data_models import (
    OptimizationModel, ProblemType, VariableMeta, VariableType, 
    ConstraintMeta, ConstraintSense, SolutionRecord, SolveStatus
)
from src.global_validation import GlobalValidator

@pytest.fixture
def full_model():
    model = OptimizationModel(problem_type=ProblemType.MILP)
    model.variables["x1"] = VariableMeta(name="x1", var_type=VariableType.INTEGER, lb=0, ub=10, obj_coef=5.0)
    model.variables["x2"] = VariableMeta(name="x2", var_type=VariableType.CONTINUOUS, lb=0, ub=20, obj_coef=10.0)
    model.constraints["c1"] = ConstraintMeta(name="c1", sense=ConstraintSense.LE, rhs=15.0)
    model.constraints["c2"] = ConstraintMeta(name="c2", sense=ConstraintSense.EQ, rhs=10.0)
    model.constraints["c3"] = ConstraintMeta(name="c3", sense=ConstraintSense.GE, rhs=5.0)
    return model

@pytest.fixture
def matrix_data():
    return {
        "c1": {"x1": 1.0, "x2": 1.0},
        "c2": {"x1": 2.0},
        "c3": {"x2": 1.0}
    }

def test_valid_solution(full_model, matrix_data):
    val = GlobalValidator()
    # x1=5, x2=10
    # c1: 5 + 10 = 15 <= 15 (OK)
    # c2: 2*5 = 10 == 10 (OK)
    # c3: 10 >= 5 (OK)
    # obj = 25 + 100 = 125
    candidate = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={"x1": 5.0, "x2": 10.0},
        objective_value=125.0
    )
    
    res = val.validate(full_model, candidate, matrix_data)
    assert res.is_valid
    assert len(res.violated_constraints) == 0

def test_violate_le_constraint(full_model, matrix_data):
    val = GlobalValidator()
    # x1=5, x2=15
    # c1: 5 + 15 = 20 <= 15 (VIOLATION, max_violation = 5)
    # c2: 2*5 = 10 == 10 (OK)
    # c3: 15 >= 5 (OK)
    candidate = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={"x1": 5.0, "x2": 15.0},
        objective_value=175.0
    )
    
    res = val.validate(full_model, candidate, matrix_data)
    assert not res.is_valid
    assert "c1" in res.violated_constraints
    assert "c2" not in res.violated_constraints
    assert res.diagnostics.max_violation == 5.0
    
    # Seeds should contain variables participating in c1: x1, x2
    assert "x1" in res.expansion_seeds
    assert "x2" in res.expansion_seeds

def test_violate_bounds(full_model):
    val = GlobalValidator()
    # x2 = 25, violates upper bound (20)
    candidate = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={"x1": 5.0, "x2": 25.0})
    res = val.validate(full_model, candidate, None) # No matrix data needed for bounds
    assert not res.is_valid
    assert "x2" in res.violating_variables
    assert res.diagnostics.number_of_bound_violations == 1

def test_violate_integrality(full_model):
    val = GlobalValidator()
    # x1 is INTEGER. 5.5 violates.
    candidate = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={"x1": 5.5, "x2": 10.0})
    res = val.validate(full_model, candidate, None)
    assert not res.is_valid
    assert "x1" in res.violating_variables
    assert res.diagnostics.number_of_integrality_violations == 1

def test_objective_difference(full_model):
    val = GlobalValidator()
    candidate = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={"x1": 5.0, "x2": 10.0}, objective_value=100.0) # Wrong obj, actual is 125
    res = val.validate(full_model, candidate, None)
    
    # Validation doesn't fail purely on obj_diff in this simple mock, but it records it.
    assert res.diagnostics.objective_difference == 25.0
