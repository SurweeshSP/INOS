from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class NumericalConfig:
    """
    Configurable numerical tolerances for the solver.
    """
    primal_feasibility_tol: float = 1e-6
    dual_feasibility_tol: float = 1e-6
    integrality_tol: float = 1e-5
    zero_tol: float = 1e-9
    pivot_tol: float = 1e-7
    objective_tol: float = 1e-6

@dataclass
class NumericalDiagnostics:
    """
    Numerical diagnostics produced after a solver run.
    """
    primal_residual: float = 0.0
    dual_residual: float = 0.0
    bound_violation: float = 0.0
    integrality_violation: float = 0.0
    numerical_warnings: List[str] = field(default_factory=list)

    def is_primal_feasible(self, config: NumericalConfig) -> bool:
        return (self.primal_residual <= config.primal_feasibility_tol and 
                self.bound_violation <= config.primal_feasibility_tol)

    def is_dual_feasible(self, config: NumericalConfig) -> bool:
        return self.dual_residual <= config.dual_feasibility_tol
