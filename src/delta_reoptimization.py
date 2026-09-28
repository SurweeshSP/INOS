from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
import time

from src.data_models import (
    OptimizationModel, Event, PersistentOptimizationState, SolutionRecord, SolveStatus
)
from src.active_graph import ADSBuilder, ADSConfig, ActiveDecisionSubgraph
from src.delta_model import DeltaModelBuilder, DeltaModel
from src.global_validation import GlobalValidator, GlobalValidationResult
from src.domain.mutation_service import MutationService

# Mock of the CPU solver dispatcher 
from src.solver.cpu import solve_cpu
@dataclass
class ReoptimizationIteration:
    iteration_number: int
    ads_size: int
    delta_model_size: int
    objective: float
    is_valid: bool
    violations: int
    expansion_reason: str
    solve_time_ms: float
    solver_status: SolveStatus

@dataclass
class ReoptimizationDiagnostics:
    change_detection_time: float = 0.0
    ads_build_time: float = 0.0
    delta_model_build_time: float = 0.0
    delta_solve_time: float = 0.0
    reconstruction_time: float = 0.0
    global_validation_time: float = 0.0
    expansion_time: float = 0.0
    total_adaptive_time: float = 0.0

    number_of_expansions: int = 0
    initial_ADS_size: int = 0
    final_ADS_size: int = 0
    validation_attempts: int = 0
    
    adaptive_success: bool = False
    fallback_used: bool = False

@dataclass
class DeltaReoptimizationConfig:
    max_expansions: int = 3
    max_depth: int = 5
    max_active_variables: int = 10000
    fallback_allowed: bool = True

@dataclass
class DeltaReoptimizationResult:
    solution: SolutionRecord
    diagnostics: ReoptimizationDiagnostics = field(default_factory=ReoptimizationDiagnostics)
    iterations: List[ReoptimizationIteration] = field(default_factory=list)

class DeltaReoptimizationOrchestrator:
    def __init__(self, config: DeltaReoptimizationConfig = None):
        self.config = config or DeltaReoptimizationConfig()
        self.ads_builder = ADSBuilder(ADSConfig(max_depth=self.config.max_depth, max_variables=self.config.max_active_variables))
        self.delta_builder = DeltaModelBuilder()
        self.validator = GlobalValidator()

    def run_adaptive_solve(self, 
                           full_model: OptimizationModel, 
                           events: List[Event], 
                           state: PersistentOptimizationState,
                           matrix_A_data: Dict[str, Dict[str, float]] = None) -> DeltaReoptimizationResult:
                           
        t_start = time.time()
        result = DeltaReoptimizationResult(solution=SolutionRecord(status=SolveStatus.ERROR))
        diag = result.diagnostics
        
        # 0. Apply events to model mathematically
        mutated_model = MutationService.apply_events_to_model(full_model, events)
        
        # 0.5. Check for structural events that require immediate fallback
        from src.data_models import EventType
        structural_events = {EventType.ROUTE_BLOCKED, EventType.ROUTE_RESTORED, EventType.FACILITY_DOWN, EventType.FACILITY_RESTORED, EventType.NEW_ORDER, EventType.CANCELLATION}
        has_structural = any(e.event_type in structural_events for e in events)
        
        if has_structural:
            if self.config.fallback_allowed:
                diag.fallback_used = True
                t_f = time.time()
                full_solve_res = solve_cpu(mutated_model)
                result.solution = full_solve_res
                diag.delta_solve_time += (time.time() - t_f)
            diag.total_adaptive_time = time.time() - t_start
            return result
        
        # 1. ADS Build
        t0 = time.time()
        ads = self.ads_builder.build(mutated_model, events, state)
        diag.ads_build_time += (time.time() - t0)
        diag.initial_ADS_size = len(ads.variables)
        
        iteration = 0
        while iteration <= self.config.max_expansions:
            t0 = time.time()
            delta_model = self.delta_builder.build(mutated_model, ads, state.previous_solution)
            diag.delta_model_build_time += (time.time() - t0)
            
            # 2. Delta Solve
            t1 = time.time()
            solve_res = solve_cpu(delta_model)
            diag.delta_solve_time += (time.time() - t1)
            
            # 3. Reconstruction
            t2 = time.time()
            candidate = self.delta_builder.reconstruct_full_solution(mutated_model, delta_model, solve_res.primal_values or {})
            diag.reconstruction_time += (time.time() - t2)
            
            # 4. Global Validation
            t3 = time.time()
            diag.validation_attempts += 1
            val_res = self.validator.validate(mutated_model, candidate, matrix_A_data)
            diag.global_validation_time += (time.time() - t3)
            
            # 5. Semantic consistency validation
            # Adaptive success requires solver success AND global validation success AND solution consistency
            is_semantically_valid = val_res.is_valid and solve_res.status == SolveStatus.OPTIMAL
            
            # Record iteration
            result.iterations.append(ReoptimizationIteration(
                iteration_number=iteration,
                ads_size=len(ads.variables),
                delta_model_size=len(delta_model.variables),
                objective=candidate.objective_value or 0.0,
                is_valid=is_semantically_valid,
                violations=val_res.diagnostics.number_of_violated_constraints + val_res.diagnostics.number_of_bound_violations + val_res.diagnostics.number_of_integrality_violations,
                expansion_reason="Validation Fail" if not is_semantically_valid else "None",
                solve_time_ms=(time.time() - t1) * 1000,
                solver_status=solve_res.status
            ))
            
            if is_semantically_valid:
                # SUCCESS!
                diag.adaptive_success = True
                diag.final_ADS_size = len(ads.variables)
                result.solution = candidate
                break
                
            # Expand ADS
            if iteration < self.config.max_expansions:
                t4 = time.time()
                diag.number_of_expansions += 1
                # Mock expansion logic: forcibly add the violating seeds into the ADS
                for v in val_res.expansion_seeds:
                    if v not in ads.variables:
                        from src.active_graph import ActiveVariable, RelevanceReason
                        ads.variables[v] = ActiveVariable(v)
                        ads.variables[v].relevance.add_reason(RelevanceReason.CONSTRAINT_CLOSURE, 1.0)
                
                # Expand constraints based on new variables (mock simple closure again)
                self.ads_builder._apply_constraint_closure(ads, mutated_model, state)
                diag.expansion_time += (time.time() - t4)
            
            iteration += 1

        if not diag.adaptive_success:
            if self.config.fallback_allowed:
                diag.fallback_used = True
                # Fallback to full model solve
                t_f = time.time()
                full_solve_res = solve_cpu(mutated_model)
                result.solution = full_solve_res
                diag.delta_solve_time += (time.time() - t_f)
            else:
                result.solution = SolutionRecord(status=SolveStatus.ERROR)

        diag.total_adaptive_time = time.time() - t_start
        return result
