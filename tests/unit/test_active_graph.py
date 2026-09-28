import pytest
from src.active_graph import (
    ADSBuilder, ADSConfig, ActiveDecisionSubgraph, RelevanceReason
)
from src.data_models import (
    OptimizationModel, ProblemType, VariableMeta, VariableType, 
    ConstraintMeta, ConstraintSense, Event, EventType,
    PersistentOptimizationState, SolutionRecord, SolveStatus
)

@pytest.fixture
def base_model():
    model = OptimizationModel(problem_type=ProblemType.LP)
    # Simple supply chain: S1 -> P1 -> W1 -> C1
    variables = [
        "flow_S1_P1_t0", "flow_P1_W1_t0", "flow_W1_C1_t0",
        "inv_W1_t0", "shortage_C1_t0"
    ]
    for v in variables:
        model.variables[v] = VariableMeta(name=v, var_type=VariableType.CONTINUOUS)
        
    constraints = [
        "balance_P1_t0", "balance_W1_t0", "demand_meet_C1_t0"
    ]
    for c in constraints:
        model.constraints[c] = ConstraintMeta(name=c, sense=ConstraintSense.EQ, rhs=0.0)
        
    import numpy as np
    # flow_S1_P1, flow_P1_W1, flow_W1_C1, inv_W1, shortage_C1
    # balance_P1: flow_S1_P1 - flow_P1_W1 = 0
    # balance_W1: flow_P1_W1 - flow_W1_C1 - inv_W1 = 0
    # demand_C1: flow_W1_C1 + shortage_C1 = 100
    model.A = np.array([
        [1.0, -1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, -1.0, -1.0, 0.0],
        [0.0, 0.0, 1.0, 0.0, 1.0]
    ])
    
    return model

@pytest.fixture
def state():
    sol = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={
            "flow_S1_P1_t0": 100,
            "flow_P1_W1_t0": 100,
            "flow_W1_C1_t0": 100,
            "inv_W1_t0": 0,
            "shortage_C1_t0": 0
        }
    )
    st = PersistentOptimizationState(model_version="v1", previous_solution=sol)
    return st

def test_empty_event(base_model, state):
    builder = ADSBuilder()
    ads = builder.build(base_model, [], state)
    
    assert len(ads.variables) == 0
    assert len(ads.constraints) == 0
    assert ads.diagnostics.active_variables == 0
    assert ads.diagnostics.variable_reduction_ratio == 1.0

def test_direct_impact_and_closure(base_model, state):
    builder = ADSBuilder()
    event = Event(
        event_type=EventType.CAPACITY_CHANGE,
        affected_variables=["flow_P1_W1_t0"]
    )
    
    ads = builder.build(base_model, [event], state)
    
    # flow_P1_W1_t0 should be directly affected
    assert "flow_P1_W1_t0" in ads.variables
    assert RelevanceReason.DIRECT_EVENT in ads.variables["flow_P1_W1_t0"].relevance.reasons
    
    # Closure should pull in balance_P1_t0 and balance_W1_t0
    assert "balance_P1_t0" in ads.constraints
    assert "balance_W1_t0" in ads.constraints
    assert RelevanceReason.CONSTRAINT_CLOSURE in ads.constraints["balance_P1_t0"].relevance.reasons
    
    # Original model preservation
    assert len(base_model.variables) == 5
    assert len(base_model.constraints) == 3

def test_dependency_expansion(base_model, state):
    config = ADSConfig(max_depth=2, min_threshold=0.2)
    builder = ADSBuilder(config)
    
    event = Event(
        event_type=EventType.CAPACITY_CHANGE,
        affected_variables=["flow_S1_P1_t0"]
    )
    
    dep_graph = {
        "flow_S1_P1_t0": ["flow_P1_W1_t0"],
        "flow_P1_W1_t0": ["flow_W1_C1_t0"]
    }
    
    ads = builder.build(base_model, [event], state, dependency_graph=dep_graph)
    
    # Seeds
    assert "flow_S1_P1_t0" in ads.variables
    # Depth 1 (score 0.5)
    assert "flow_P1_W1_t0" in ads.variables
    # Depth 2 (score 0.333)
    assert "flow_W1_C1_t0" in ads.variables
    
    # Metrics
    assert ads.diagnostics.seed_count == 1
    assert ads.diagnostics.expansion_depth == 2

def test_threshold_exclusion(base_model, state):
    config = ADSConfig(max_depth=5, min_threshold=0.4) # score 0.333 will be excluded
    builder = ADSBuilder(config)
    
    event = Event(
        event_type=EventType.CAPACITY_CHANGE,
        affected_variables=["flow_S1_P1_t0"]
    )
    
    dep_graph = {
        "flow_S1_P1_t0": ["flow_P1_W1_t0"],
        "flow_P1_W1_t0": ["flow_W1_C1_t0"]
    }
    
    ads = builder.build(base_model, [event], state, dependency_graph=dep_graph)
    
    assert "flow_S1_P1_t0" in ads.variables
    assert "flow_P1_W1_t0" in ads.variables  # score 0.5 >= 0.4
    assert "flow_W1_C1_t0" not in ads.variables  # score 0.33 < 0.4
    assert ads.diagnostics.excluded_count == 1

def test_multiple_events(base_model, state):
    builder = ADSBuilder()
    e1 = Event(event_type=EventType.CAPACITY_CHANGE, affected_variables=["flow_S1_P1_t0"])
    e2 = Event(event_type=EventType.DEMAND_CHANGE, affected_variables=["flow_W1_C1_t0"])
    
    ads = builder.build(base_model, [e1, e2], state)
    
    assert "flow_S1_P1_t0" in ads.variables
    assert "flow_W1_C1_t0" in ads.variables
    assert ads.diagnostics.seed_count == 2
    
def test_determinism(base_model, state):
    builder = ADSBuilder()
    event = Event(event_type=EventType.CAPACITY_CHANGE, affected_variables=["flow_P1_W1_t0"])
    
    ads1 = builder.build(base_model, [event], state)
    ads2 = builder.build(base_model, [event], state)
    
    # Check they have exactly the same keys
    assert set(ads1.variables.keys()) == set(ads2.variables.keys())
    assert set(ads1.constraints.keys()) == set(ads2.constraints.keys())

def test_to_active_model(base_model, state):
    builder = ADSBuilder()
    event = Event(event_type=EventType.CAPACITY_CHANGE, affected_variables=["flow_P1_W1_t0"])
    ads = builder.build(base_model, [event], state)
    
    active_model = ads.to_active_model(base_model, state)
    
    # Should only contain active variables and constraints
    assert len(active_model.variables) == len(ads.variables)
    assert len(active_model.constraints) == len(ads.constraints)
    
    # Original model is untouched
    assert len(base_model.variables) == 5
