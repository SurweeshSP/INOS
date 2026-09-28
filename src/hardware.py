import logging
from typing import Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class HardwareManager:
    """
    Manages hardware detection, memory checks, and array conversion (CPU/GPU).
    Defaults to CPU if CuPy is not available.
    """
    def __init__(self):
        self._gpu_available = False
        self._cupy = None
        
        try:
            import cupy as cp
            self._cupy = cp
            # Try to get device info to ensure it actually works
            try:
                cp.cuda.Device(0).compute_capability
                self._gpu_available = True
                logger.info("GPU available. CuPy loaded successfully.")
            except cp.cuda.runtime.CUDARuntimeError:
                logger.warning("CuPy installed but no CUDA device available.")
        except ImportError:
            logger.info("CuPy not installed. GPU acceleration unavailable.")
            
    def is_gpu_available(self) -> bool:
        return self._gpu_available
        
    def get_gpu_memory_info(self) -> Tuple[int, int]:
        """
        Returns (free_mem, total_mem) in bytes if GPU available, else (0,0).
        """
        if not self._gpu_available:
            return 0, 0
            
        mempool = self._cupy.get_default_memory_pool()
        # This gives memory used by cupy, not full free/total of the device
        # but it's a proxy for memory checks.
        return mempool.free_bytes(), mempool.total_bytes()
        
    def to_gpu(self, array: Any) -> Any:
        """
        Transfers a numpy array or scipy sparse matrix to GPU using CuPy.
        """
        if not self._gpu_available:
            return array
            
        import scipy.sparse as sp
        if sp.issparse(array):
            import cupyx.scipy.sparse as csp
            return csp.csr_matrix(array)
        else:
            return self._cupy.array(array)
            
    def to_cpu(self, array: Any) -> Any:
        """
        Transfers a CuPy array or CuPy sparse matrix back to CPU (numpy/scipy).
        """
        if not self._gpu_available:
            return array
            
        if hasattr(array, 'get'):
            return array.get()
        return array
