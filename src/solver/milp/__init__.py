from typing import Any, Dict, Optional
from src.data_models import OptimizationModel, SolutionRecord, ProblemType
from src.solver.milp.branch_and_bound import BranchAndBoundSolver
from src.solver.numerical import NumericalConfig

def solve_milp(model: OptimizationModel, options: Optional[Dict[str, Any]] = None, state: Optional[Any] = None) -> SolutionRecord:
    if model.problem_type != ProblemType.MILP:
        raise ValueError("Model must be a MILP")
        
    config = NumericalConfig()
    solver = BranchAndBoundSolver(config)
    
    # We could extract time_limit from options if provided
    time_limit = options.get("time_limit", 3600.0) if options else 3600.0
    node_limit = options.get("node_limit", 100000) if options else 100000
    
    return solver.solve(model, time_limit=time_limit, node_limit=node_limit)
