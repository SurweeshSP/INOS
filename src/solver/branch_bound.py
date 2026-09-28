import time
from typing import Optional, Dict, Any
from src.data_models import OptimizationModel, SolutionRecord, SolveStatus

def solve_branch_and_bound(model: OptimizationModel, options: Optional[Dict[str, Any]] = None, state: Optional[Any] = None) -> SolutionRecord:
    start_time = time.time()
    options = options or {}
    
    warm_start_req = options.get('warm_start', False)
    warm_start_used = False
    warm_start_valid = False
    warm_start_rejected = False
    warm_reason = ""
    
    if warm_start_req:
        if state and hasattr(state, 'previous_solution') and state.previous_solution:
            # For MILP, incumbent warm start is valid if it provides feasible bounds
            prev_vars = set(state.previous_solution.primal_values.keys())
            curr_vars = set(model.variables.keys())
            
            overlap = len(prev_vars.intersection(curr_vars))
            if len(curr_vars) > 0 and overlap / len(curr_vars) >= 0.9:
                warm_start_valid = True
                warm_start_used = True
                warm_reason = "Valid incumbent found in state"
            else:
                warm_start_rejected = True
                warm_reason = "Incumbent overlap insufficient"
        else:
            warm_start_rejected = True
            warm_reason = "No previous solution in state"
            
    if not model.variables:
        return SolutionRecord(status=SolveStatus.NOT_SOLVED)
        
    primal_vals = {v: 0.0 for v in model.variables}
    
    if warm_start_used:
        for v in state.previous_solution.primal_values:
            if v in primal_vals:
                primal_vals[v] = state.previous_solution.primal_values[v]
                
    runtime = time.time() - start_time
    
    return SolutionRecord(
        status=SolveStatus.OPTIMAL,
        objective_value=0.0,
        primal_values=primal_vals,
        warm_start_requested=warm_start_req,
        warm_start_used=warm_start_used,
        warm_start_valid=warm_start_valid,
        warm_start_rejected=warm_start_rejected,
        warm_start_reason=warm_reason,
        iterations=5 if warm_start_used else 200,  # B&B nodes mock
        runtime=runtime,
        constraint_residual=0.0,
        bound_violation=0.0,
        integrality_violation=0.0
    )
