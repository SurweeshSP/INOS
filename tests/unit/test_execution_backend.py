import pytest
import numpy as np
import scipy.sparse as sp
from src.solver.execution_backend import CPUBackend, GPUBackend, get_backend
from src.hardware import HardwareManager

def test_cpu_backend_dense():
    backend = CPUBackend()
    A = np.array([[1.0, 2.0], [3.0, 4.0]])
    x = np.array([1.0, 1.0])
    
    y = backend.matvec(A, x)
    np.testing.assert_array_equal(y, [3.0, 7.0])
    
    yT = backend.rmatvec(A, x)
    np.testing.assert_array_equal(yT, [4.0, 6.0])

def test_cpu_backend_sparse():
    backend = CPUBackend()
    A = sp.csr_matrix([[1.0, 0.0], [0.0, 4.0]])
    x = np.array([1.0, 1.0])
    
    y = backend.matvec(A, x)
    np.testing.assert_array_equal(y, [1.0, 4.0])

def test_gpu_backend_fallback():
    # If GPU is not available, get_backend(use_gpu=True) should return CPUBackend
    backend = get_backend(use_gpu=True)
    hw = HardwareManager()
    if not hw.is_gpu_available():
        assert isinstance(backend, CPUBackend)
    else:
        assert isinstance(backend, GPUBackend)
