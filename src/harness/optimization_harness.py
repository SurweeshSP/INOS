from typing import List, Dict, Any
from src.data_models import OptimizationModel, PersistentOptimizationState, Event
from src.harness.decision import OptimizationDecision
from src.harness.features import FeatureExtractor
from src.harness.safety_gate import SafetyGate

class OptimizationHarness:
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.safety_gate = SafetyGate()

    def make_decision(self, 
                     full_model: OptimizationModel, 
                     state: PersistentOptimizationState, 
                     events: List[Event]) -> OptimizationDecision:
                     
        features = self.feature_extractor.extract_all(full_model, state, events)
        
        decision = OptimizationDecision(
            decision_features=features
        )
        
        reasons = []
        
        # Determine solver type
        prob_type = features.get("problem_type")
        decision.solver_type = prob_type
        reasons.append(f"Problem type is {prob_type}")
        
        if prob_type == "LP":
            decision.algorithm = "simplex"
        elif prob_type == "MILP":
            decision.algorithm = "branch_and_bound"
        elif prob_type == "QP":
            decision.algorithm = "active_set"
            
        # Determine mode
        # If cold state, we must do FULL solve
        if features.get("cold_state", False):
            decision.optimization_mode = "FULL"
            decision.warm_start = False
            reasons.append("Cold state -> FULL solve")
        else:
            # We have warm state. Should we use ADS/Adaptive?
            # Simple heuristic for deterministic harness:
            # If changed variables/constraints are a small fraction, use Adaptive
            num_vars = features.get("num_variables", 1)
            changed_vars = features.get("changed_variable_count", 0)
            
            if num_vars > 0 and (changed_vars / num_vars) < 0.2:
                decision.optimization_mode = "ADAPTIVE"
                decision.ads_enabled = True
                decision.initial_depth = 1
                decision.warm_start = True
                reasons.append("Change fraction < 0.2 -> ADAPTIVE solve")
            else:
                decision.optimization_mode = "FULL"
                decision.warm_start = True
                reasons.append("Change fraction >= 0.2 -> FULL solve with WARM start")
                
        # Determine backend
        if features.get("gpu_available", False):
            # Only use GPU if problem size is large enough to justify transfer overhead
            if features.get("num_variables", 0) > 1000:
                decision.backend = "GPU"
                reasons.append("Large problem and GPU available -> GPU backend")
            else:
                decision.backend = "CPU"
                reasons.append("Small problem -> CPU backend to avoid overhead")
        else:
            decision.backend = "CPU"
            reasons.append("GPU not available -> CPU backend")
            
        decision.reason = reasons
        
        # Pass through safety gate
        decision = self.safety_gate.validate_decision(decision, features)
        
        return decision
