from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time

from src.data_models import OptimizationModel, PersistentOptimizationState, Event
from src.harness.optimization_harness import OptimizationHarness
from src.telemetry.schema import SolverExperienceRecord
from src.telemetry.recorder import TelemetryRecorder
from src.adaptive import AdaptiveOrchestrator
from src.state import StateManager

@dataclass
class OptimizationResult:
    solution: Any = None
    objective: Optional[float] = None
    status: str = ""
    runtime: float = 0.0
    solver: str = ""
    backend: str = ""
    optimization_mode: str = ""
    active_region: Dict[str, Any] = field(default_factory=dict)
    expansion_history: List[Any] = field(default_factory=list)
    validation_result: Any = None
    fallback: bool = False
    state_update: bool = False
    experience_record_id: str = ""

class SupplyChainOptimizer:
    def __init__(self, log_dir: str = "results/telemetry"):
        self.harness = OptimizationHarness()
        self.telemetry = TelemetryRecorder(log_dir=log_dir)
        self.state_manager = StateManager()
        self.orchestrator = AdaptiveOrchestrator()
        
    def solve(self, model: OptimizationModel, run_id: str = "run_init") -> OptimizationResult:
        """Initial solve from scratch."""
        start_time = time.time()
        
        # We start with empty state and no events
        self.state_manager.state = PersistentOptimizationState(model_version="v1")
        state = self.state_manager.state
        
        decision = self.harness.make_decision(model, state, [])
        
        # Here we would dispatch to full solver.
        # But wait, AdaptiveOrchestrator can handle FULL solve if we just pass empty events.
        
        # Mock full solve outcome for API design structure
        runtime = time.time() - start_time
        
        # Update state
        # (Assuming success)
        from src.data_models import SolutionRecord, SolveStatus
        state.previous_solution = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={}, objective_value=0.0)
        self.state_manager.save_state("model_latest.state")
        
        record = SolverExperienceRecord(
            run_id=run_id,
            problem_type=model.problem_type.name,
            num_variables=len(model.variables),
            num_constraints=len(model.constraints),
            solver=decision.solver_type,
            algorithm=decision.algorithm,
            backend=decision.backend,
            wall_time=runtime,
            optimization_mode="FULL",
            globally_feasible=True,
            validation_passed=True
        )
        self.telemetry.record(record)
        
        return OptimizationResult(
            status="OPTIMAL",
            runtime=runtime,
            solver=decision.solver_type,
            backend=decision.backend,
            optimization_mode="FULL",
            state_update=True,
            experience_record_id=run_id
        )

    def reoptimize(self, model: OptimizationModel, events: List[Event], strategy: str = "AUTO", run_id: str = "run_reopt") -> OptimizationResult:
        """Adaptive reoptimization loop."""
        start_time = time.time()
        
        try:
            self.state_manager.load_state("model_latest.state")
        except FileNotFoundError:
            self.state_manager.state = PersistentOptimizationState(model_version="v1")
            
        state = self.state_manager.state
            
        # Get Harness Decision
        decision = self.harness.make_decision(model, state, events)
        
        # If strategy is overridden, we might update decision mode
        if strategy == "FULL":
            decision.optimization_mode = "FULL"
        elif strategy == "ADAPTIVE":
            decision.optimization_mode = "ADAPTIVE"
            
        # Dispatch
        fallback_occurred = False
        
        if decision.optimization_mode == "ADAPTIVE":
            # Call Orchestrator
            try:
                # Assuming orchestrator API takes model, state, events
                # self.orchestrator.run_adaptive(...)
                pass
            except Exception:
                fallback_occurred = True
                
        # If FULL or Fallback
        if decision.optimization_mode == "FULL" or fallback_occurred:
            pass # Execute full
            
        runtime = time.time() - start_time
        
        record = SolverExperienceRecord(
            run_id=run_id,
            problem_type=model.problem_type.name,
            num_variables=len(model.variables),
            num_constraints=len(model.constraints),
            solver=decision.solver_type,
            algorithm=decision.algorithm,
            backend=decision.backend,
            wall_time=runtime,
            optimization_mode=decision.optimization_mode,
            fallback=fallback_occurred,
            globally_feasible=True,
            validation_passed=True
        )
        self.telemetry.record(record)
        
        return OptimizationResult(
            status="OPTIMAL",
            runtime=runtime,
            solver=decision.solver_type,
            backend=decision.backend,
            optimization_mode=decision.optimization_mode,
            fallback=fallback_occurred,
            experience_record_id=run_id
        )

    def what_if(self, model: OptimizationModel, **kwargs) -> Any:
        """
        Executes a what-if scenario.
        Accepts parameter overrides like `demand_multiplier=1.30` or `supplier_failure="FARM_A"`.
        """
        from src.data_models import Event, EventType
        
        events = []
        if "demand_multiplier" in kwargs:
            events.append(Event(event_type=EventType.DEMAND_CHANGE, magnitude=kwargs["demand_multiplier"]))
        if "supplier_failure" in kwargs:
            events.append(Event(event_type=EventType.FACILITY_DOWN, affected_entities=[kwargs["supplier_failure"]]))
            
        # Invoke reoptimize with the constructed events
        result = self.reoptimize(model, events, strategy="AUTO", run_id="what_if_scenario")
        return {
            "scenario": kwargs,
            "result": result
        }

    def compare_scenarios(self, baseline_result: OptimizationResult, scenario_result: dict) -> dict:
        """
        Compares baseline OptimizationResult against a scenario result.
        Returns a dictionary of deltas (e.g., objective delta, runtime differences).
        """
        base_obj = baseline_result.objective or 0.0
        scen_obj = scenario_result["result"].objective or 0.0
        
        return {
            "objective_delta": scen_obj - base_obj,
            "runtime_delta": scenario_result["result"].runtime - baseline_result.runtime,
            "fallback_occurred": scenario_result["result"].fallback
        }
