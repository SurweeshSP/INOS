import time
import os
import json
from typing import Dict, Any, Tuple
from src.data_models import OptimizationModel, SolveStatus, SolutionRecord
from src.solver.cpu import solve_cpu
from src.delta_reoptimization import DeltaReoptimizationOrchestrator
from src.api.schemas import (
    SolveRequestSchema, ReoptimizeRequestSchema, SolveResponseSchema,
    ModelTelemetrySchema, ExecutionTelemetrySchema, SolutionSchema,
    ValidationTelemetrySchema
)
from src.service.model_service import model_service
from src.service.validation_service import validation_service

TELEMETRY_DIR = "data/runtime/telemetry"

class OptimizationService:
    def __init__(self):
        os.makedirs(TELEMETRY_DIR, exist_ok=True)

    def solve(self, job_id: str, request: SolveRequestSchema) -> SolveResponseSchema:
        t0 = time.time()
        
        # 1. Intake and construct model
        model = model_service.build_from_json(request.model_dump())
        model_id = model_service.generate_model_id()
        model_service.save_model(model_id, model)
        
        parse_ms = (time.time() - t0) * 1000.0
        
        # 2. Solve
        t1 = time.time()
        solution = solve_cpu(model, options=request.options.model_dump())
        solve_ms = (time.time() - t1) * 1000.0
        
        # Save state for future reoptimization
        # Usually we would save internal solver state, but for this demo we'll just save the final result
        model_service.save_model(model_id, model, state=solution)

        # 3. Validation
        validation = validation_service.validate_solution(model, solution)
        
        # 4. Final Status Enforcement
        final_status = solution.status.name
        if solution.status == SolveStatus.OPTIMAL and not validation.is_valid:
            final_status = "VALIDATION_FAILURE"

        var_dict = {}
        if solution.variables is not None:
            var_dict = {f"v{i}": float(v) for i, v in enumerate(solution.variables)}
            
        # 5. Assemble Telemetry
        model_telemetry = ModelTelemetrySchema(
            variables=len(model.c),
            constraints=len(model.b),
            nonzeros=model.A.nnz,
            integer_variables=sum(model.variable_types == 1),
            binary_variables=sum(model.variable_types == 2)
        )
        
        execution_telemetry = ExecutionTelemetrySchema(
            solver=model.problem_type.name,
            strategy="full",
            runtime_ms=solve_ms + parse_ms
        )
        
        solution_data = SolutionSchema(
            status=final_status,
            objective=solution.objective_value,
            variables=var_dict
        )
        
        resp = SolveResponseSchema(
            job_id=job_id,
            model_id=model_id,
            model=model_telemetry,
            execution=execution_telemetry,
            solution=solution_data,
            validation=validation
        )
        
        self._record_telemetry(resp)
        return resp

    def reoptimize(self, job_id: str, request: ReoptimizeRequestSchema) -> SolveResponseSchema:
        t0 = time.time()
        
        # 1. Load baseline
        baseline_model = model_service.load_model(request.model_id)
        if baseline_model is None:
            raise ValueError(f"Model {request.model_id} not found in persistence.")
            
        baseline_state = model_service.load_state(request.model_id)

        # 2. Reoptimize using ADS pipeline
        from src.data_models import Event, EventType, PersistentOptimizationState
        orchestrator = DeltaReoptimizationOrchestrator()
        
        event_objs = []
        for e in request.events:
            try:
                event_type = EventType[e.type.upper()]
            except KeyError:
                event_type = EventType.DEMAND_CHANGE
            event_objs.append(Event(event_type=event_type, old_value=e.old_value, new_value=e.new_value))
            
        p_state = PersistentOptimizationState(model_version="1", previous_solution=baseline_state)
        
        t1 = time.time()
        reopt_res = orchestrator.run_adaptive_solve(baseline_model, event_objs, p_state)
        solution = reopt_res.solution
        
        ads_metrics = {
            "fallback_used": reopt_res.diagnostics.fallback_used,
            "ads_initial_size": reopt_res.diagnostics.initial_ADS_size,
            "ads_final_size": reopt_res.diagnostics.final_ADS_size,
            "expansions": reopt_res.diagnostics.number_of_expansions
        }
        final_model = baseline_model
        
        solve_ms = (time.time() - t1) * 1000.0

        # Save new model for further chains
        new_model_id = model_service.generate_model_id()
        model_service.save_model(new_model_id, final_model, state=solution)

        # 3. Validation
        validation = validation_service.validate_solution(final_model, solution)
        
        # 4. Final Status Enforcement
        final_status = solution.status.name
        if solution.status == SolveStatus.OPTIMAL and not validation.is_valid:
            final_status = "VALIDATION_FAILURE"
            
        var_dict = {}
        if solution.variables is not None:
            var_dict = {f"v{i}": float(v) for i, v in enumerate(solution.variables)}

        model_telemetry = ModelTelemetrySchema(
            variables=len(final_model.c),
            constraints=len(final_model.b),
            nonzeros=final_model.A.nnz,
            integer_variables=sum(final_model.variable_types == 1),
            binary_variables=sum(final_model.variable_types == 2)
        )
        
        execution_telemetry = ExecutionTelemetrySchema(
            solver=final_model.problem_type.name,
            strategy="adaptive_delta" if not ads_metrics.get("fallback_used", False) else "fallback",
            ads_initial_size=ads_metrics.get("ads_initial_size", 0),
            ads_final_size=ads_metrics.get("ads_final_size", 0),
            expansions=ads_metrics.get("expansions", 0),
            fallback_used=ads_metrics.get("fallback_used", False),
            runtime_ms=solve_ms + (t1 - t0)*1000.0
        )
        
        solution_data = SolutionSchema(
            status=final_status,
            objective=solution.objective_value,
            variables=var_dict
        )
        
        resp = SolveResponseSchema(
            job_id=job_id,
            model_id=new_model_id,
            model=model_telemetry,
            execution=execution_telemetry,
            solution=solution_data,
            validation=validation
        )
        
        self._record_telemetry(resp)
        return resp

    def _record_telemetry(self, resp: SolveResponseSchema):
        path = os.path.join(TELEMETRY_DIR, f"{resp.job_id}.json")
        with open(path, "w") as f:
            json.dump(resp.model_dump(), f, indent=2)

optimization_service = OptimizationService()
