import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from src.data_models import OptimizationModel, ConstraintSense, VariableType

@dataclass
class ValidationResult:
    is_valid: bool
    objective_recomputed: float
    primal_residual: float
    bound_violation: float
    integrality_violation: Optional[float] = None
    kkt_stationarity: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
class IndependentValidator:
    """
    Independently calculates mathematical residuals for a solution x against
    an OptimizationModel. This MUST NOT rely on any solver-provided metrics.
    """
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        
    def validate(self, model: OptimizationModel, x: np.ndarray, duals: Optional[np.ndarray] = None) -> ValidationResult:
        if len(x) != len(model.variables):
            return ValidationResult(
                is_valid=False,
                objective_recomputed=np.nan,
                primal_residual=np.inf,
                bound_violation=np.inf,
                details={"error": f"Solution dimension {len(x)} != variables {len(model.variables)}"}
            )
            
        # Recompute objective
        obj_val = float(model.c.dot(x))
        if model.Q is not None:
            obj_val += 0.5 * float(x.dot(model.Q.dot(x)))
            
        # Bounds validation
        lower_v = np.maximum(model.lower_bounds - x, 0)
        upper_v = np.maximum(x - model.upper_bounds, 0)
        max_bound_violation = float(max(np.max(lower_v) if len(lower_v) > 0 else 0,
                                        np.max(upper_v) if len(upper_v) > 0 else 0))
                                        
        # Integrality validation
        integrality_violation = None
        int_indices = [i for i, (k, v) in enumerate(model.variables.items()) 
                       if v.var_type in (VariableType.INTEGER, VariableType.BINARY)]
        if int_indices:
            x_int = x[int_indices]
            nearest_int = np.round(x_int)
            dist = np.abs(x_int - nearest_int)
            integrality_violation = float(np.max(dist)) if len(dist) > 0 else 0.0
            
        # Primal feasibility
        primal_residual = 0.0
        if model.A is not None and model.A.shape[0] > 0:
            Ax = model.A.dot(x)
            residuals = np.zeros(len(model.b))
            
            for i, (k, c_meta) in enumerate(model.constraints.items()):
                val = Ax[i] - model.b[i]
                if c_meta.sense == ConstraintSense.EQ:
                    residuals[i] = abs(val)
                elif c_meta.sense == ConstraintSense.LE:
                    residuals[i] = max(val, 0)
                elif c_meta.sense == ConstraintSense.GE:
                    residuals[i] = max(-val, 0)
                    
            primal_residual = float(np.max(residuals))
            
        # KKT Stationarity for QP
        kkt_stationarity = None
        if model.Q is not None and duals is not None and len(duals) == model.A.shape[0]:
            # Simple KKT check: Qx + c + A^T \lambda - \mu_lower + \mu_upper = 0
            # To avoid calculating bounds multipliers explicitly, we can check if
            # the gradient projected onto active bounds is zero.
            # For simplicity in this base validator, we just check Qx + c + A^T \lambda
            # and ignore bounds multipliers unless we build a full active-set KKT validator.
            grad = model.Q.dot(x) + model.c
            if model.A is not None:
                grad += model.A.T.dot(duals)
            
            # Allow non-zero gradient if variable is at bound (optimality condition)
            stat_res = 0.0
            for i in range(len(x)):
                g = grad[i]
                at_lb = (x[i] - model.lower_bounds[i]) <= self.tolerance
                at_ub = (model.upper_bounds[i] - x[i]) <= self.tolerance
                
                if at_lb and g >= -self.tolerance:
                    pass # Valid
                elif at_ub and g <= self.tolerance:
                    pass # Valid
                else:
                    stat_res = max(stat_res, abs(g))
                    
            kkt_stationarity = float(stat_res)
            
        # Overall validity
        is_valid = (
            primal_residual <= self.tolerance and
            max_bound_violation <= self.tolerance
        )
        if integrality_violation is not None:
            is_valid = is_valid and (integrality_violation <= self.tolerance)
            
        return ValidationResult(
            is_valid=is_valid,
            objective_recomputed=obj_val,
            primal_residual=primal_residual,
            bound_violation=max_bound_violation,
            integrality_violation=integrality_violation,
            kkt_stationarity=kkt_stationarity
        )
