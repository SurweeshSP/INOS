import pytest
import math
from src.data_models import (
    ProblemType,
    VariableType,
    ConstraintSense,
    EventType,
    NodeType,
    EdgeType,
    ConstraintRole,
    SolveStatus,
    AlgorithmType,
    VariableMeta,
    ConstraintMeta,
    NodeMeta,
    EdgeMeta,
    OptimizationModel,
    SolutionRecord,
    SupplyChainState,
    Event,
    Scenario,
    PersistentOptimizationState,
    BoundaryCondition,
    ActiveRegion,
    HarnessFeatures,
    HarnessDecision,
    SolverTelemetry,
    ExperienceRecord,
    InputRequest,
    ValidationResult
)

def test_enums():
    assert ProblemType.LP.name == "LP"
    assert VariableType.CONTINUOUS.name == "CONTINUOUS"
    assert ConstraintSense.LE.name == "LE"

def test_variable_meta_defaults():
    var = VariableMeta(name="x1", var_type=VariableType.CONTINUOUS)
    assert var.name == "x1"
    assert var.var_type == VariableType.CONTINUOUS
    assert var.lb == 0.0
    assert var.ub == float('inf')
    assert var.obj_coef == 0.0

def test_constraint_meta():
    con = ConstraintMeta(name="c1", sense=ConstraintSense.LE, rhs=10.0, role=ConstraintRole.CAPACITY)
    assert con.name == "c1"
    assert con.sense == ConstraintSense.LE
    assert con.rhs == 10.0
    assert con.role == ConstraintRole.CAPACITY

def test_event_creation():
    event = Event(
        event_type=EventType.DEMAND_CHANGE,
        affected_entities=["CustomerA"],
        affected_variables=["flow_Warehouse1_CustomerA"],
        affected_constraints=["demand_CustomerA"],
        affected_periods=[1, 2],
        old_value=100.0,
        new_value=115.0,
        magnitude=15.0
    )
    assert event.event_type == EventType.DEMAND_CHANGE
    assert len(event.affected_entities) == 1
    assert event.magnitude == 15.0

def test_serialization():
    # Test simple dataclass dict representation as a proxy for serialization
    import dataclasses
    var = VariableMeta(name="x2", var_type=VariableType.INTEGER, lb=-5.0, ub=5.0)
    d = dataclasses.asdict(var)
    assert d['name'] == 'x2'
    assert d['var_type'] == VariableType.INTEGER
    assert d['lb'] == -5.0
    assert d['ub'] == 5.0

    # Deserialize
    var2 = VariableMeta(**d)
    assert var == var2

def test_nan_inf():
    var = VariableMeta(name="x_inf", var_type=VariableType.CONTINUOUS, ub=float('inf'))
    assert math.isinf(var.ub)
