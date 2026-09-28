from typing import List, Dict, Any
from src.harness.decision import OptimizationDecision
from src.data_models import ProblemType

class SafetyGate:
    """
    Ensures that decisions made by the harness (deterministic or learned)
    are mathematically and systemically safe before execution.
    """
    
    def validate_decision(self, decision: OptimizationDecision, features: Dict[str, Any]) -> OptimizationDecision:
        reasons = list(decision.reason)
        
        # 1. Hardware availability
        if decision.backend == "GPU" and not features.get("gpu_available", False):
            decision.backend = "CPU"
            reasons.append("SAFETY_OVERRIDE: GPU not available")
            
        # 2. Solver type matching
        prob_type = features.get("problem_type")
        if prob_type == ProblemType.LP.name and decision.solver_type != "LP":
            decision.solver_type = "LP"
            reasons.append("SAFETY_OVERRIDE: Problem is LP")
        elif prob_type == ProblemType.MILP.name and decision.solver_type != "MILP":
            decision.solver_type = "MILP"
            reasons.append("SAFETY_OVERRIDE: Problem is MILP")
        elif prob_type == ProblemType.QP.name and decision.solver_type != "QP":
            decision.solver_type = "QP"
            reasons.append("SAFETY_OVERRIDE: Problem is QP")
            
        # 3. State prerequisites
        if decision.optimization_mode in ["ADS", "ADAPTIVE"] or decision.warm_start:
            if not features.get("warm_state", False):
                decision.optimization_mode = "FULL"
                decision.warm_start = False
                decision.ads_enabled = False
                reasons.append("SAFETY_OVERRIDE: Warm state required for ADS/Adaptive/Warm-start")
                
        decision.reason = reasons
        return decision
