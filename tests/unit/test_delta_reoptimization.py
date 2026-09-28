import pytest
from src.data_models import (
    OptimizationModel, ProblemType, VariableMeta, VariableType, 
    ConstraintMeta, ConstraintSense, SolutionRecord, SolveStatus,
    PersistentOptimizationState, Event, EventType
)
from src.delta_reoptimization import DeltaReoptimizationOrchestrator, DeltaReoptimizationConfig
import numpy as np

@pytest.fixture
def base_scenario():
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables["x1"] = VariableMeta(name="x1", var_type=VariableType.CONTINUOUS, lb=0, ub=10, obj_coef=5.0)
    model.variables["x2"] = VariableMeta(name="x2", var_type=VariableType.CONTINUOUS, lb=0, ub=20, obj_coef=10.0)
    model.constraints["c1"] = ConstraintMeta(name="c1", sense=ConstraintSense.LE, rhs=15.0)
    
    matrix = {
        "c1": {"x1": 1.0, "x2": 1.0}
    }
    
    import numpy as np
    model.A = np.array([[1.0, 1.0]])
    model.b = np.array([15.0])
    model.c = np.array([5.0, 10.0])
    model.lower_bounds = np.array([0.0, 0.0])
    model.upper_bounds = np.array([10.0, 20.0])
    model.senses = ['L']
    
    state = PersistentOptimizationState(
        model_version="v1",
        previous_solution=SolutionRecord(
            status=SolveStatus.OPTIMAL,
            primal_values={"x1": 5.0, "x2": 10.0},
            objective_value=125.0
        )
    )
    
    return model, matrix, state

def test_successful_adaptive_reopt(base_scenario):
    model, matrix, state = base_scenario
    
    # Event affects x1
    event = Event(event_type=EventType.CAPACITY_CHANGE, affected_variables=["x1"])
    
    config = DeltaReoptimizationConfig(max_expansions=3)
    orchestrator = DeltaReoptimizationOrchestrator(config)
    
    # We mock the CPUSolverDispatcher internally which usually just returns SolveStatus.OPTIMAL
    # Our delta solver mock will return some solution (0.0 delta in mock logic, making x1 stay 5.0)
    res = orchestrator.run_adaptive_solve(model, [event], state, matrix)
    
    # Should succeed without expansions
    assert res.diagnostics.adaptive_success
    assert not res.diagnostics.fallback_used
    assert res.diagnostics.number_of_expansions == 0
    assert res.solution.status == SolveStatus.OPTIMAL

def test_expansion_and_fallback(base_scenario):
    model, matrix, state = base_scenario
    
    # We create a scenario where validation will definitely fail.
    # We do this by changing the constraint sense and RHS to be impossible to satisfy
    # given the bounds (x1 <= 10, x2 <= 20).
    model.senses = ['G']
    model.b = np.array([50.0]) # x1 + x2 >= 50
    model.constraints["c1"].sense = ConstraintSense.GE
    model.constraints["c1"].rhs = 50.0
    
    bad_matrix = {
        "c1": {"x1": 1.0, "x2": 1.0}
    }
    
    event = Event(event_type=EventType.CAPACITY_CHANGE, affected_variables=["x1"])
    config = DeltaReoptimizationConfig(max_expansions=1, fallback_allowed=True)
    orchestrator = DeltaReoptimizationOrchestrator(config)
    
    res = orchestrator.run_adaptive_solve(model, [event], state, bad_matrix)
    
    # It should try 0th iteration, fail, expand once, try 1st iteration, fail, then fallback.
    assert not res.diagnostics.adaptive_success
    assert res.diagnostics.fallback_used
    assert res.diagnostics.number_of_expansions == 1
    # Check that fallback attempted a solve on the full model (which is now structurally infeasible)
    assert res.solution.status == SolveStatus.INFEASIBLE
