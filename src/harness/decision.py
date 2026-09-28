from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class OptimizationDecision:
    solver_type: str = "LP"  # LP, MILP, QP
    algorithm: str = "simplex"
    backend: str = "CPU"
    optimization_mode: str = "FULL"  # FULL, ADS, ADAPTIVE
    warm_start: bool = False
    ads_enabled: bool = False
    initial_depth: int = 0
    confidence: float = 1.0
    decision_features: Dict[str, Any] = field(default_factory=dict)
    reason: List[str] = field(default_factory=list)
    fallback_policy: str = "FULL_REOPT"
