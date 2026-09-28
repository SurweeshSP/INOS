import pytest
from src.change_detection import ChangeDetector
from src.data_models import EventType

def test_change_detector():
    cd = ChangeDetector()
    prev = {'demand': 100}
    curr = {'demand': 150}
    
    events = cd.detect_changes(prev, curr)
    assert len(events) == 1
    assert events[0].event_type == EventType.DEMAND_CHANGE
    assert events[0].magnitude == 50
    assert events[0].old_value == 100
    assert events[0].new_value == 150

    region = cd.map_to_active_region(events)
    assert region is not None
