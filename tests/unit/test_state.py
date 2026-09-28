import pytest
import os
import tempfile
from src.data_models import SolutionRecord, SolveStatus, Event, EventType
from src.state import StateManager

def test_state_manager_updates():
    sm = StateManager()
    
    sol = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        objective_value=150.0,
        primal_values={"x1": 10.0}
    )
    
    sm.update_solution(sol)
    
    assert sm.state.objective == 150.0
    assert sm.state.feasibility is True
    assert len(sm.state.solve_history) == 1
    
    evt = Event(event_type=EventType.DEMAND_CHANGE, magnitude=10.0)
    sm.record_event(evt)
    
    assert len(sm.state.event_history) == 1
    assert sm.state.event_history[0].event_type == EventType.DEMAND_CHANGE

def test_state_serialization():
    sm1 = StateManager(model_version="v2")
    sol = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        objective_value=200.0,
        primal_values={"x": 5.0}
    )
    sm1.update_solution(sol)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "state.pkl")
        sm1.save_state(filepath)
        
        # Load state
        sm2 = StateManager(model_version="v2")
        sm2.load_state(filepath)
        
        assert sm2.state.objective == 200.0
        assert sm2.state.previous_solution.primal_values["x"] == 5.0

def test_state_version_mismatch():
    sm1 = StateManager(model_version="v1")
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "state.pkl")
        sm1.save_state(filepath)
        
        sm2 = StateManager(model_version="v2")
        with pytest.raises(ValueError, match="State version mismatch"):
            sm2.load_state(filepath)
