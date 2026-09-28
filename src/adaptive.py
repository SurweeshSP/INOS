import time
from typing import List, Optional, Any
import numpy as np
from src.data_models import OptimizationModel, Event, PersistentOptimizationState, SolutionRecord, SolveStatus
from src.active_graph import ADSBuilder, ActiveDecisionSubgraph
from src.delta_model import DeltaModelBuilder
from src.global_validation import GlobalValidator
from src.solver.cpu import solve_cpu

class AdaptiveOrchestrator:
    def __init__(self, max_expansions: int = 3):
        self.max_expansions = max_expansions
        self.ads_builder = ADSBuilder()
        self.delta_builder = DeltaModelBuilder()
        self.validator = GlobalValidator()

    def run_adaptive_solve(self,
                           full_model: OptimizationModel,
                           events: List[Event],
                           state: PersistentOptimizationState,
                           graph: Optional[Any] = None) -> SolutionRecord:
        
        current_depth = 0
        
        while current_depth <= self.max_expansions:
            self.ads_builder.config.max_depth = current_depth + 1
            ads = self.ads_builder.build(full_model, events, state, graph=graph)
            
            delta_model = self.delta_builder.build(full_model, ads, state.previous_solution)
            
            # Using CPU/Mathematical solver layer
            delta_sol = solve_cpu(delta_model)
            
            if delta_sol.status == SolveStatus.OPTIMAL:
                full_sol = self.delta_builder.reconstruct_full_solution(full_model, delta_model, delta_sol.primal_values)
                
                # Check globally
                validation = self.validator.validate(full_model, full_sol)
                if validation.is_valid:
                    return full_sol
            
            current_depth += 1
            
        # Fallback to full solve
        return solve_cpu(full_model)
