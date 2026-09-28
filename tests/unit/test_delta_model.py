import pytest
from src.data_models import (
    OptimizationModel, ProblemType, VariableMeta, VariableType, 
    ConstraintMeta, ConstraintSense, SolutionRecord, SolveStatus
)
from src.active_graph import ActiveDecisionSubgraph, ActiveVariable, ActiveConstraint
from src.delta_model import DeltaModelBuilder

@pytest.fixture
def full_model():
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables["x1"] = VariableMeta(name="x1", var_type=VariableType.CONTINUOUS, lb=0, ub=10, obj_coef=5.0)
    model.variables["x2"] = VariableMeta(name="x2", var_type=VariableType.CONTINUOUS, lb=0, ub=20, obj_coef=10.0)
    model.constraints["c1"] = ConstraintMeta(name="c1", sense=ConstraintSense.LE, rhs=15.0)
    return model

@pytest.fixture
def base_solution():
    return SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={"x1": 5.0, "x2": 10.0},
        objective_value=125.0
    )

def test_missing_base_solution(full_model):
    builder = DeltaModelBuilder()
    ads = ActiveDecisionSubgraph()
    
    with pytest.raises(ValueError):
        builder.build(full_model, ads, None)

def test_delta_model_creation(full_model, base_solution):
    ads = ActiveDecisionSubgraph()
    ads.variables["x1"] = ActiveVariable("x1")
    ads.constraints["c1"] = ActiveConstraint("c1")
    
    builder = DeltaModelBuilder()
    delta_model = builder.build(full_model, ads, base_solution)
    
    # Delta variable bounds adjusted
    assert "x1" in delta_model.variables
    var_x1 = delta_model.variables["x1"]
    assert var_x1.lb == 0 - 5.0  # -5.0
    assert var_x1.ub == 10 - 5.0 # 5.0
    
    # x2 shouldn't be in delta
    assert "x2" not in delta_model.variables
    
    # Check diagnostics
    assert delta_model.diagnostics.active_variable_count == 1
    assert delta_model.diagnostics.delta_variable_count == 1
    
    # Objective offset = c^T x_base for active variables
    # Only x1 is active, so its base offset is 5.0 * 5.0 = 25.0
    assert delta_model.objective_offset == 25.0

def test_reconstruct_full_solution(full_model, base_solution):
    builder = DeltaModelBuilder()
    ads = ActiveDecisionSubgraph()
    ads.variables["x1"] = ActiveVariable("x1")
    delta_model = builder.build(full_model, ads, base_solution)
    
    # Suppose Delta solve resulted in x1 = +2.0 (so absolute is 7.0)
    delta_solution = {"x1": 2.0}
    
    recon = builder.reconstruct_full_solution(full_model, delta_model, delta_solution)
    
    assert recon.primal_values["x1"] == 7.0
    assert recon.primal_values["x2"] == 10.0 # From base solution
    
    # Obj = 7.0 * 5.0 + 10.0 * 10.0 = 35.0 + 100.0 = 135.0
    assert recon.objective_value == 135.0
