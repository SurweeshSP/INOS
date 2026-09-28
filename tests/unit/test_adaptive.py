import pytest
import numpy as np
from src.adaptive import AdaptiveOrchestrator
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense, PersistentOptimizationState, SolutionRecord, SolveStatus, Event, EventType

def test_adaptive_orchestrator():
    orchestrator = AdaptiveOrchestrator(max_expansions=1)
    
    full_model = OptimizationModel(problem_type=ProblemType.LP)
    full_model.variables["x1"] = VariableMeta("x1", VariableType.CONTINUOUS)
    full_model.variables["x2"] = VariableMeta("x2", VariableType.CONTINUOUS)
    full_model.constraints["c1"] = ConstraintMeta("c1", ConstraintSense.LE, 15.0)
    
    full_model.A = np.array([[1.0, 1.0]])
    full_model.b = np.array([15.0])
    full_model.c = np.array([1.0, 1.0])
    full_model.bounds = [(0, 10), (0, 10)]
    full_model.senses = ['L']
    
    state = PersistentOptimizationState(model_version="v1")
    state.previous_solution = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={"x1": 5.0, "x2": 5.0})
    
    evt = Event(event_type=EventType.DEMAND_CHANGE, affected_variables=["x1"])
    
    # Run adaptive solve
    sol = orchestrator.run_adaptive_solve(full_model, [evt], state)
    
    assert sol.status == SolveStatus.OPTIMAL
    # Since it's a mock test it should pass with some values.
    # We mainly test it doesn't crash and returns a SolutionRecord
    assert isinstance(sol, SolutionRecord)
