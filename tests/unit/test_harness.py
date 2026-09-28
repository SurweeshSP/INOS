import pytest
from src.harness.decision import OptimizationDecision
from src.harness.optimization_harness import OptimizationHarness
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, PersistentOptimizationState, SolutionRecord, SolveStatus, Event, EventType

def test_optimization_harness():
    harness = OptimizationHarness()
    
    # Mock model
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables["v1"] = VariableMeta("v1", VariableType.CONTINUOUS)
    
    # Mock cold state
    state = PersistentOptimizationState(model_version="v1")
    
    events = [Event(event_type=EventType.DEMAND_CHANGE, affected_variables=["v1"])]
    
    decision = harness.make_decision(model, state, events)
    
    assert decision.solver_type == "LP"
    assert decision.algorithm == "simplex"
    assert decision.optimization_mode == "FULL"
    assert decision.warm_start is False
    assert decision.backend == "CPU" # Since size is small
    
    # Mock warm state with small changes
    state.previous_solution = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={"v1": 1.0})
    
    # Let's add more variables to make change fraction small
    for i in range(10):
        model.variables[f"v_{i}"] = VariableMeta(f"v_{i}", VariableType.CONTINUOUS)
        
    decision = harness.make_decision(model, state, events)
    assert decision.optimization_mode == "ADAPTIVE"
    assert decision.warm_start is True
