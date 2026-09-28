import numpy as np
from typing import Any, Tuple
from abc import ABC, abstractmethod
from src.hardware import HardwareManager
import scipy.sparse as sp

class ExecutionBackend(ABC):
    @abstractmethod
    def matvec(self, A: Any, x: Any) -> Any:
        pass
        
    @abstractmethod
    def rmatvec(self, A: Any, y: Any) -> Any:
        pass

    @abstractmethod
    def add(self, x: Any, y: Any) -> Any:
        pass

    @abstractmethod
    def dot(self, x: Any, y: Any) -> float:
        pass

class CPUBackend(ExecutionBackend):
    def matvec(self, A: Any, x: Any) -> Any:
        return A @ x
        
    def rmatvec(self, A: Any, y: Any) -> Any:
        return A.T @ y

    def add(self, x: Any, y: Any) -> Any:
        return x + y

    def dot(self, x: Any, y: Any) -> float:
        return np.dot(x, y)

class GPUBackend(ExecutionBackend):
    def __init__(self, hardware: HardwareManager):
        self.hw = hardware
        if not self.hw.is_gpu_available():
            raise RuntimeError("GPU Backend requested but GPU is not available.")
            
    def matvec(self, A: Any, x: Any) -> Any:
        A_gpu = self.hw.to_gpu(A)
        x_gpu = self.hw.to_gpu(x)
        return self.hw.to_cpu(A_gpu @ x_gpu)
        
    def rmatvec(self, A: Any, y: Any) -> Any:
        A_gpu = self.hw.to_gpu(A)
        y_gpu = self.hw.to_gpu(y)
        return self.hw.to_cpu(A_gpu.T @ y_gpu)

    def add(self, x: Any, y: Any) -> Any:
        x_gpu = self.hw.to_gpu(x)
        y_gpu = self.hw.to_gpu(y)
        return self.hw.to_cpu(x_gpu + y_gpu)

    def dot(self, x: Any, y: Any) -> float:
        x_gpu = self.hw.to_gpu(x)
        y_gpu = self.hw.to_gpu(y)
        # Using cupy dot if available
        import cupy as cp
        return float(cp.dot(x_gpu, y_gpu))

def get_backend(use_gpu: bool = False) -> ExecutionBackend:
    hw = HardwareManager()
    if use_gpu and hw.is_gpu_available():
        return GPUBackend(hw)
    return CPUBackend()
