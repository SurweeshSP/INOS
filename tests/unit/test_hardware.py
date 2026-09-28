import pytest
import numpy as np
from src.hardware import HardwareManager

def test_hardware_manager_cpu_fallback():
    hw = HardwareManager()
    
    # Even if GPU is available or not, to_cpu should return numpy arrays
    arr = np.array([1.0, 2.0, 3.0])
    
    gpu_arr = hw.to_gpu(arr)
    cpu_arr = hw.to_cpu(gpu_arr)
    
    assert isinstance(cpu_arr, np.ndarray)
    np.testing.assert_array_equal(arr, cpu_arr)

def test_hardware_manager_memory():
    hw = HardwareManager()
    free, total = hw.get_gpu_memory_info()
    assert isinstance(free, int)
    assert isinstance(total, int)
