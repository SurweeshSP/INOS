import math
import pytest
from src.analytics.statistics import (
    calc_mean,
    calc_variance,
    calc_std,
    calc_cv,
    calc_quantiles,
    rolling_statistics,
    calc_correlation,
    capacity_utilization,
    service_level
)

def test_basic_statistics():
    data = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    
    assert math.isclose(calc_mean(data), 5.0)
    assert math.isclose(calc_variance(data), 32.0 / 7.0)
    assert math.isclose(calc_std(data), math.sqrt(32.0 / 7.0))
    assert math.isclose(calc_cv(data), math.sqrt(32.0 / 7.0) / 5.0)

def test_quantiles():
    data = [1, 2, 3, 4, 5]
    q = calc_quantiles(data, [0.5, 0.75])
    assert math.isclose(q[0], 3.0)
    assert math.isclose(q[1], 4.0)

def test_correlation():
    x = [1, 2, 3, 4]
    y = [2, 4, 6, 8]
    assert math.isclose(calc_correlation(x, y), 1.0)
    
    y_inv = [-2, -4, -6, -8]
    assert math.isclose(calc_correlation(x, y_inv), -1.0)

def test_domain_metrics():
    assert math.isclose(capacity_utilization(80, 100), 0.8)
    assert math.isclose(capacity_utilization(120, 100), 1.2)
    assert math.isclose(capacity_utilization(10, 0), 1.0)
    
    assert math.isclose(service_level(95, 100), 0.95)
    assert math.isclose(service_level(100, 100), 1.0)
    assert math.isclose(service_level(110, 100), 1.0)
    assert math.isclose(service_level(0, 0), 1.0)
