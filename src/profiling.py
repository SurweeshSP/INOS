import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProfilingRecord:
    problem_id: str = "unknown"
    n_vars: int = 0
    m_cons: int = 0
    nnz: int = 0
    sparsity: float = 0.0
    cpu_time: float = 0.0
    gpu_time: float = 0.0
    transfer_time: float = 0.0
    iterations: int = 0
    gpu_slower: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

class ProfilingSubsystem:
    """
    Subsystem for capturing performance metrics of solvers and components.
    """
    def __init__(self):
        self.records = []
        self._current_timers = {}
        
    def start_timer(self, name: str):
        self._current_timers[name] = time.time()
        
    def stop_timer(self, name: str) -> float:
        if name in self._current_timers:
            elapsed = time.time() - self._current_timers[name]
            del self._current_timers[name]
            return elapsed
        return 0.0
        
    def record_solve(self, record: ProfilingRecord):
        if record.gpu_time > 0 and record.gpu_time > record.cpu_time:
            record.gpu_slower = True
            logger.warning(f"GPU_SLOWER: GPU took {record.gpu_time:.4f}s vs CPU {record.cpu_time:.4f}s")
            
        self.records.append(record)
        
    def get_summary(self) -> str:
        if not self.records:
            return "No profiling records."
            
        total_cpu = sum(r.cpu_time for r in self.records)
        total_gpu = sum(r.gpu_time for r in self.records)
        slower_count = sum(1 for r in self.records if r.gpu_slower)
        
        return (f"Profiling Summary: {len(self.records)} records. "
                f"Total CPU: {total_cpu:.4f}s, Total GPU: {total_gpu:.4f}s. "
                f"GPU Slower: {slower_count} times.")
