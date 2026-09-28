import pytest
import os
from src.telemetry.schema import SolverExperienceRecord
from src.telemetry.recorder import TelemetryRecorder

def test_telemetry_recorder(tmp_path):
    recorder = TelemetryRecorder(log_dir=str(tmp_path))
    
    record1 = SolverExperienceRecord(
        run_id="run_1",
        problem_type="LP",
        wall_time=1.5
    )
    
    recorder.record(record1)
    
    loaded = recorder.load_all()
    assert len(loaded) == 1
    assert loaded[0].run_id == "run_1"
    assert loaded[0].problem_type == "LP"
    assert loaded[0].wall_time == 1.5
