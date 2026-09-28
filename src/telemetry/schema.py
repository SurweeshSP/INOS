from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
import time

@dataclass
class SolverExperienceRecord:
    # IDENTITY
    run_id: str = ""
    scenario_id: str = ""
    parent_run_id: str = ""
    timestamp: float = field(default_factory=time.time)
    dataset: str = ""
    instance: str = ""

    # MODEL
    problem_type: str = ""
    num_variables: int = 0
    num_constraints: int = 0
    integer_count: int = 0
    
    # EVENT
    event_type: str = ""
    changed_variables: int = 0
    changed_constraints: int = 0
    
    # STATE
    state_valid: bool = False
    warm_start: bool = False
    previous_objective: Optional[float] = None
    
    # ADS
    active_variables: int = 0
    active_constraints: int = 0
    expansion_depth: int = 0
    
    # SOLVER
    solver: str = ""
    algorithm: str = ""
    backend: str = ""
    
    # PERFORMANCE
    wall_time: float = 0.0
    solve_time: float = 0.0
    validation_time: float = 0.0
    
    # QUALITY
    objective: Optional[float] = None
    constraint_violation: float = 0.0
    
    # OUTCOME
    globally_feasible: bool = False
    validation_passed: bool = False
    fallback: bool = False
    failure_reason: str = ""
    
    # DECISION
    optimization_mode: str = ""
    decision_reason: List[str] = field(default_factory=list)

    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
