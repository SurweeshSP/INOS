from typing import Dict, Optional

class IncumbentManager:
    """
    Manages the best known integer-feasible solution during Branch and Bound.
    """
    def __init__(self):
        self.best_objective = float('inf')
        self.best_solution: Optional[Dict[str, float]] = None
        self.updates_count = 0
        
    def update(self, objective: float, solution: Dict[str, float]) -> bool:
        """
        Updates the incumbent if the new solution is strictly better.
        Assumes minimization.
        Returns True if updated.
        """
        if objective < self.best_objective:
            self.best_objective = objective
            self.best_solution = solution.copy()
            self.updates_count += 1
            return True
        return False
        
    def has_incumbent(self) -> bool:
        return self.best_solution is not None

class BoundManager:
    """
    Manages the global bounds for the MILP solve.
    """
    def __init__(self):
        self.global_lower_bound = -float('inf')
        
    def update_global_lower_bound(self, new_bound: float):
        """
        Updates the global lower bound.
        """
        if new_bound > self.global_lower_bound:
            self.global_lower_bound = new_bound
            
    def compute_gap(self, incumbent_objective: float) -> float:
        """
        Computes the relative optimality gap.
        """
        if incumbent_objective == float('inf'):
            return float('inf')
            
        if self.global_lower_bound == -float('inf') or self.global_lower_bound == float('inf'):
            return float('inf')
            
        # |Upper - Lower| / max(1e-10, |Upper|)
        diff = abs(incumbent_objective - self.global_lower_bound)
        return diff / max(1e-10, abs(incumbent_objective))
