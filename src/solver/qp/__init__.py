import time
from typing import Any, Dict, Optional
from src.data_models import OptimizationModel, SolutionRecord, SolveStatus, ProblemType
from src.solver.numerical import NumericalConfig
from src.solver.qp.active_set import ActiveSetQPSolver

def solve_qp(model: OptimizationModel, options: Optional[Dict[str, Any]] = None, state: Optional[Any] = None) -> SolutionRecord:
    """
    Real QP solver using the Primal Active-Set method.
    """
    if model.problem_type != ProblemType.QP:
        raise ValueError("Model must be a QP")
        
    config = NumericalConfig()
    solver = ActiveSetQPSolver(config)
    
    max_iter = options.get("max_iter", 1000) if options else 1000
    
    res = solver.solve(model, max_iter=max_iter)
    
    if options and options.get('warm_start'):
        res.warm_start_requested = True
        res.warm_start_used = False
        res.warm_start_rejected = True
        res.warm_start_reason = "ActiveSetQPSolver does not support warm start yet"
        
    return res
