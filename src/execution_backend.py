import logging
from typing import Dict, Any, Optional
import sys

from src.data_models import OptimizationModel, SolutionRecord, ProblemType, SolveStatus
from src.hardware import HardwareManager
from src.solver.cpu import solve_cpu

logger = logging.getLogger(__name__)

class ExecutionBackend:
    def __init__(self):
        self.hardware = HardwareManager()
        
    def _estimate_memory_required(self, model: OptimizationModel) -> int:
        """
        Estimates bytes required for the model in sparse or dense format.
        Assuming sparse CSR double precision (8 bytes per element).
        """
        if model.A is None:
            return 0
        
        try:
            import scipy.sparse as sp
            if sp.issparse(model.A):
                # 8 bytes for data + 4 bytes for indices
                nnz = model.A.nnz
                bytes_req = nnz * 12 + model.A.shape[0] * 4
                return bytes_req
            else:
                # Dense
                return model.A.size * 8
        except Exception:
            return 1024 * 1024 * 1024 # default 1GB if unknown
            
    def _can_run_on_gpu(self, bytes_req: int) -> bool:
        if not self.hardware.is_gpu_available():
            return False
            
        import cupy as cp
        # PyTorch or CuPy memory check (very rough)
        # Often it's safer to just attempt it or check total memory.
        try:
            mem_info = cp.cuda.runtime.memGetInfo()
            free_mem = mem_info[0]
            # Safety margin (require 2x the memory required for operations)
            return free_mem > bytes_req * 2
        except Exception:
            return False

    def solve_gpu(self, model: OptimizationModel) -> SolutionRecord:
        """
        CuPy sparse matrix based optimization (if applicable).
        Currently CuPy does not have a native sparse linprog solver.
        PyTorch can be used for gradient descent based solvers for LP/QP,
        but for standard LP, GPU is typically used to accelerate interior point linear algebra.
        We will simulate a GPU solver path or dispatch to a custom PyTorch optimizer if available.
        Since standard linprog on GPU is non-trivial, we fallback to CPU.
        """
        logger.warning("Native GPU sparse LP solver not fully implemented. Falling back to CPU with scipy highs.")
        return solve_cpu(model)
        
    def solve_auto(self, model: OptimizationModel) -> SolutionRecord:
        bytes_req = self._estimate_memory_required(model)
        mb = bytes_req / (1024 * 1024)
        logger.info(f"Model memory requirement estimated at {mb:.2f} MB")
        
        if self._can_run_on_gpu(bytes_req):
            logger.info("Executing on GPU (AUTO)")
            try:
                return self.solve_gpu(model)
            except Exception as e:
                logger.error(f"GPU execution failed: {e}. Falling back to CPU.")
                return solve_cpu(model)
        else:
            logger.info("Executing on CPU (AUTO)")
            return solve_cpu(model)

execution_backend = ExecutionBackend()
