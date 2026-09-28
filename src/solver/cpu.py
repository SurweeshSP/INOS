from typing import Any, Dict, Optional
from src.data_models import OptimizationModel, SolutionRecord, ProblemType
from src.solver.lp import solve_lp

def solve_cpu(model: OptimizationModel, options: Optional[Dict[str, Any]] = None, state: Optional[Any] = None) -> SolutionRecord:
    """
    Central CPU optimization backend.
    Delegates to appropriate solver based on problem type.
    """
    opts = options or {}
    
    if model.problem_type == ProblemType.LP:
        return solve_lp(model, method=opts.get('method', 'scipy'), options=opts, state=state)
    elif model.problem_type == ProblemType.MILP:
        from src.solver.milp import solve_milp
        return solve_milp(model, options=opts, state=state)
    elif model.problem_type == ProblemType.QP:
        from src.solver.qp import solve_qp
        return solve_qp(model, options=opts, state=state)
    
    # Other types not implemented in CPU delegator for this phase
    raise NotImplementedError(f"Solver for {model.problem_type} not implemented in CPU backend yet.")
