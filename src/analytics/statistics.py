import numpy as np
import pandas as pd
from typing import List, Union, Tuple, Dict

def calc_mean(data: Union[List[float], np.ndarray]) -> float:
    return float(np.mean(data))

def calc_variance(data: Union[List[float], np.ndarray]) -> float:
    if len(data) < 2:
        return 0.0
    return float(np.var(data, ddof=1))

def calc_std(data: Union[List[float], np.ndarray]) -> float:
    return float(np.std(data, ddof=1) if len(data) > 1 else 0.0)

def calc_cv(data: Union[List[float], np.ndarray]) -> float:
    mean_val = calc_mean(data)
    if mean_val == 0:
        return 0.0
    return calc_std(data) / mean_val

def calc_quantiles(data: Union[List[float], np.ndarray], q: List[float]) -> List[float]:
    return np.quantile(data, q).tolist()

def rolling_statistics(data: Union[List[float], np.ndarray], window: int) -> Dict[str, List[float]]:
    s = pd.Series(data)
    return {
        "mean": s.rolling(window).mean().fillna(0.0).tolist(),
        "std": s.rolling(window).std().fillna(0.0).tolist()
    }

def calc_correlation(x: Union[List[float], np.ndarray], y: Union[List[float], np.ndarray]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])

def capacity_utilization(load: float, capacity: float) -> float:
    if capacity == 0:
        return 1.0 if load > 0 else 0.0
    return load / capacity

def capacity_stress(loads: List[float], capacity: float) -> float:
    # average utilization
    utils = [capacity_utilization(l, capacity) for l in loads]
    return calc_mean(utils)

def service_level(fulfilled: float, demand: float) -> float:
    if demand == 0:
        return 1.0
    return min(1.0, fulfilled / demand)

def demand_risk(demand_data: List[float]) -> float:
    # simple metric based on CV
    return calc_cv(demand_data)

def inventory_risk(inventory: float, avg_demand: float) -> float:
    # simple coverage ratio reciprocal
    if inventory == 0:
        return 1.0
    return min(1.0, avg_demand / inventory)

def disruption_severity(lost_capacity: float, original_capacity: float) -> float:
    if original_capacity == 0:
        return 0.0
    return lost_capacity / original_capacity
