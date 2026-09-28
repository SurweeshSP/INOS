import pytest
from src.active_graph import ADSBuilder, ActiveDecisionSubgraph
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense, PersistentOptimizationState, Event, EventType, SolutionRecord, SolveStatus
from src.graph import SupplyChainGraph

def test_ads_builder_with_graph():
    builder = ADSBuilder()
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables["v1"] = VariableMeta("v1", VariableType.CONTINUOUS)
    model.variables["v2"] = VariableMeta("v2", VariableType.CONTINUOUS)
    
    model.constraints["c1"] = ConstraintMeta("c1", ConstraintSense.LE, 10)
    
    import numpy as np
    model.A = np.array([[1.0, 1.0]])
    model.b = np.array([10.0])
    
    state = PersistentOptimizationState(model_version="v1")
    state.previous_solution = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={"v1": 5, "v2": 5})
    
    graph = SupplyChainGraph()
    # Mocking graph such that v1 and v2 are connected to some node N1
    graph.node_to_vars["N1"] = ["v1", "v2"]
    graph.node_to_cons["N1"] = ["c1"]
    
    evt = Event(event_type=EventType.DEMAND_CHANGE, affected_variables=["v1"])
    
    ads = builder.build(model, [evt], state, graph=graph)
    
    # Event seeds v1
    assert "v1" in ads.variables
    # Graph constraint closure should add c1 and boundary condition on v2 if v2 is not selected
    assert "c1" in ads.constraints
    assert "v2" in ads.boundary_conditions
    assert ads.boundary_conditions["v2"].fixed_value == 5
