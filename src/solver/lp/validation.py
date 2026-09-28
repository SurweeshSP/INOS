import numpy as np
from src.solver.numerical import NumericalConfig, NumericalDiagnostics

class LPValidator:
    def __init__(self, config: NumericalConfig):
        self.config = config

    def validate_solution(self, A: np.ndarray, b: np.ndarray, c: np.ndarray, 
                          x: np.ndarray, y: np.ndarray) -> NumericalDiagnostics:
        """
        Calculates primal and dual residuals.
        """
        primal_res = np.max(np.abs(A @ x - b)) if A is not None and len(b) > 0 else 0.0
        # For standard form Ax = b, x >= 0, dual is A^T y <= c
        dual_res = 0.0
        if A is not None and len(c) > 0:
            dual_slacks = c - A.T @ y
            dual_res = np.max(np.maximum(0, -dual_slacks)) # violations where A^T y > c
        
        # Bound violations for x >= 0
        bound_viol = np.max(np.maximum(0, -x)) if len(x) > 0 else 0.0
        
        diag = NumericalDiagnostics(
            primal_residual=float(primal_res),
            dual_residual=float(dual_res),
            bound_violation=float(bound_viol)
        )
        return diag
