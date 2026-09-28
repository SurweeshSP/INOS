from typing import Dict, Any, List
from src.data_models import OptimizationModel, VariableType

class LPPresolver:
    def __init__(self):
        self.fixed_vars: Dict[str, float] = {}

    def presolve(self, model: OptimizationModel) -> OptimizationModel:
        """
        Apply safe reductions: fixed variable elimination.
        """
        reduced_model = OptimizationModel(problem_type=model.problem_type)
        reduced_model.variables = {}
        reduced_model.constraints = model.constraints.copy()
        
        for name, meta in model.variables.items():
            if abs(meta.lb - meta.ub) < 1e-9:
                # Fixed variable
                self.fixed_vars[name] = meta.lb
            else:
                reduced_model.variables[name] = meta
                
        return reduced_model

    def postsolve(self, primal_values: Dict[str, float]) -> Dict[str, float]:
        """
        Restore original variables after solve.
        """
        full_solution = primal_values.copy()
        for name, val in self.fixed_vars.items():
            full_solution[name] = val
        return full_solution
