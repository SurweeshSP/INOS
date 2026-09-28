from typing import Dict, Any
from src.data_models import SolutionRecord

class ImpactAnalyzer:
    def __init__(self):
        pass

    def analyze(self, base_solution: SolutionRecord, scenario_solution: SolutionRecord) -> Dict[str, Any]:
        """
        Compare base and scenario solutions to determine impact.
        """
        impact = {}
        
        # Compare objectives
        obj_base = base_solution.objective_value or 0.0
        obj_scen = scenario_solution.objective_value or 0.0
        
        impact['objective_change'] = obj_scen - obj_base
        
        # Determine variable differences
        var_diffs = {}
        for k, v in base_solution.primal_values.items():
            scen_v = scenario_solution.primal_values.get(k, 0.0)
            if v != scen_v:
                var_diffs[k] = scen_v - v
                
        for k, v in scenario_solution.primal_values.items():
            if k not in base_solution.primal_values:
                var_diffs[k] = v
                
        impact['variable_differences'] = var_diffs
        
        return impact
