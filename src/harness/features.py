from typing import Dict, Any, List
from src.data_models import OptimizationModel, PersistentOptimizationState, Event, VariableType
from src.hardware import HardwareManager

class FeatureExtractor:
    def __init__(self):
        self.hw = HardwareManager()

    def extract_all(self, 
                   full_model: OptimizationModel, 
                   state: PersistentOptimizationState, 
                   events: List[Event]) -> Dict[str, Any]:
                   
        features = {}
        features.update(self._extract_model_features(full_model))
        features.update(self._extract_state_features(state))
        features.update(self._extract_event_features(events))
        features.update(self._extract_hardware_features())
        
        return features

    def _extract_model_features(self, full_model: OptimizationModel) -> Dict[str, Any]:
        integer_count = sum(1 for v in full_model.variables.values() if v.var_type == VariableType.INTEGER)
        binary_count = sum(1 for v in full_model.variables.values() if v.var_type == VariableType.BINARY)
        
        return {
            "problem_type": full_model.problem_type.name,
            "num_variables": len(full_model.variables),
            "num_constraints": len(full_model.constraints),
            "integer_count": integer_count,
            "binary_count": binary_count,
            "is_milp": (integer_count + binary_count) > 0,
            "has_q_matrix": hasattr(full_model, "Q") and full_model.Q is not None
        }

    def _extract_state_features(self, state: PersistentOptimizationState) -> Dict[str, Any]:
        has_valid_state = state.previous_solution is not None
        return {
            "cold_state": not has_valid_state,
            "warm_state": has_valid_state,
            "previous_objective": state.previous_solution.objective_value if has_valid_state else None,
            "state_version": state.model_version
        }

    def _extract_event_features(self, events: List[Event]) -> Dict[str, Any]:
        changed_vars = set()
        changed_cons = set()
        for e in events:
            changed_vars.update(e.affected_variables)
            changed_cons.update(e.affected_constraints)
            
        return {
            "num_events": len(events),
            "changed_variable_count": len(changed_vars),
            "changed_constraint_count": len(changed_cons)
        }

    def _extract_hardware_features(self) -> Dict[str, Any]:
        gpu_available = self.hw.is_gpu_available()
        return {
            "cpu_available": True,
            "gpu_available": gpu_available
        }
