import pytest
import time
from src.profiling import ProfilingSubsystem, ProfilingRecord

def test_profiling_timers():
    prof = ProfilingSubsystem()
    prof.start_timer("test_op")
    time.sleep(0.01)
    elapsed = prof.stop_timer("test_op")
    assert elapsed >= 0.01

def test_profiling_gpu_slower():
    prof = ProfilingSubsystem()
    rec = ProfilingRecord(cpu_time=0.1, gpu_time=0.5)
    prof.record_solve(rec)
    
    assert rec.gpu_slower is True
    assert "GPU Slower: 1" in prof.get_summary()

def test_profiling_gpu_faster():
    prof = ProfilingSubsystem()
    rec = ProfilingRecord(cpu_time=0.5, gpu_time=0.1)
    prof.record_solve(rec)
    
    assert rec.gpu_slower is False
    assert "GPU Slower: 0" in prof.get_summary()
