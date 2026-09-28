from typing import Dict, Any
import numpy as np
from src.data_models import OptimizationModel, SolutionRecord, SolveStatus
from src.trust.model_validator import ModelValidator
from src.api.schemas import ValidationTelemetrySchema

class ValidationService:
    def __init__(self):
        self.validator = ModelValidator()

    def validate_solution(self, model: OptimizationModel, solution: SolutionRecord) -> ValidationTelemetrySchema:
        """
        Independent global validator gateway.
        The API MUST NEVER report a solver status as optimal without passing this.
        """
        
        # If solver already failed/infeasible, we don't upgrade it, just pass through
        if solution.status in [SolveStatus.INFEASIBLE, SolveStatus.UNBOUNDED, SolveStatus.NOT_SOLVED, SolveStatus.ERROR]:
            return ValidationTelemetrySchema(
                is_valid=False,
                primal_residual=0.0,
                bound_violation=0.0,
                integrality_violation=0.0
            )

        if solution.variables is None:
            return ValidationTelemetrySchema(
                is_valid=False,
                primal_residual=0.0,
                bound_violation=0.0,
                integrality_violation=0.0
            )

        try:
            # Recompute objective independently
            obj_val = float(model.c.T @ solution.variables)
            if hasattr(model, 'Q') and model.Q is not None:
                Q = np.array(model.Q.toarray() if hasattr(model.Q, 'toarray') else model.Q)
                x = np.array(solution.variables)
                obj_val += 0.5 * float(x.T @ Q @ x)
                
            offset = getattr(model, 'objective_offset', 0.0)
            obj_val -= offset

            
            # Primal feasibility (Ax >=, <=, == b)
            Ax = model.A @ solution.variables
            primal_residual = 0.0
            
            senses = model.senses if hasattr(model, 'senses') and model.senses is not None else []
            # if senses is not present or shorter than b, assume equality (or whatever default)
            for i in range(len(model.b)):
                sense = senses[i] if i < len(senses) else 'E'
                val = Ax[i] - model.b[i]
                if sense == 'E':
                    viol = abs(val)
                elif sense == 'L':
                    viol = max(0, val)
                elif sense == 'G':
                    viol = max(0, -val)
                else:
                    viol = abs(val)
                primal_residual = max(primal_residual, viol)
            lower_violation = float(np.max(np.maximum(0, model.lower_bounds - solution.variables)))
            upper_violation = float(np.max(np.maximum(0, solution.variables - model.upper_bounds)))
            bound_violation = max(lower_violation, upper_violation)
            
            # Integrality checking
            integrality_violation = 0.0
            col_names = list(model.variables.keys())
            from src.data_models import VariableType
            for i, name in enumerate(col_names):
                var_type = model.variables[name].var_type
                if var_type in (VariableType.INTEGER, VariableType.BINARY):
                    val = solution.variables[i]
                    violation = float(np.abs(val - np.round(val)))
                    integrality_violation = max(integrality_violation, violation)

            # Tolerances
            is_valid = (primal_residual < 1e-4) and (bound_violation < 1e-4) and (integrality_violation < 1e-4)

            return ValidationTelemetrySchema(
                is_valid=is_valid,
                primal_residual=primal_residual,
                bound_violation=bound_violation,
                integrality_violation=integrality_violation,
                objective_recomputed=obj_val
            )
        except Exception as e:
            import traceback
            traceback.print_exc()
            return ValidationTelemetrySchema(
                is_valid=False,
                primal_residual=0.0,
                bound_violation=0.0,
                integrality_violation=0.0
            )

validation_service = ValidationService()
