import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from pydantic import BaseModel

from src.api.v2_schemas import (
    BusinessProblemInput, 
    BusinessEventRequest, 
    DecisionPackage
)
from src.domain.problem_builder import SupplyChainProblemBuilder
from src.domain.event_translator import EventTranslator
from src.domain.result_translator import ResultTranslator
from src.visualization.graph_visualizer import GraphVisualizer

from src.service.model_service import model_service
from src.execution_backend import execution_backend
from src.data_models import PersistentOptimizationState, SolutionRecord, SolveStatus
from src.delta_reoptimization import DeltaReoptimizationOrchestrator

router = APIRouter()

# In-memory maps for our adapter
BUSINESS_VARIABLE_MAPS = {}
BUSINESS_STATES = {}
JOBS = {}

import asyncio
from fastapi import BackgroundTasks

def background_build_model(problem: BusinessProblemInput, job_id: str):
    try:
        JOBS[job_id]["status"] = "BUILDING"
        JOBS[job_id]["progress"] = "Parsing dataset"
        
        # 1. Build mathematical model
        model, var_map = SupplyChainProblemBuilder.build(problem)
        
        problem_id = str(uuid.uuid4())
        model_version = f"v001"
        
        JOBS[job_id]["progress"] = f"Variables: {len(model.variables)} Constraints: {len(model.constraints)}"
        
        # 2. Save var map and state
        BUSINESS_VARIABLE_MAPS[problem_id] = var_map
        
        # 3. Save into existing model service
        model_service.save_model(problem_id, model)
        
        # 4. Generate initial graph (simplified)
        graph_b64 = GraphVisualizer.generate_full_graph_base64(model)
        
        # 5. We don't perform the initial full solve here anymore. 
        # The user will call /v2/optimize separately if needed, or we just leave it ready.
        # But for backward compatibility we can initialize a dummy state.
        state = PersistentOptimizationState(
            model_version=model_version,
            previous_solution=None,
            objective=0.0,
            feasibility=False,
            optimality=False,
            entities=[e.model_dump() if hasattr(e, 'model_dump') else e.dict() for e in problem.entities]
        )
        BUSINESS_STATES[problem_id] = state

        JOBS[job_id]["problem_summary"] = {
            "problem_id": problem_id,
            "model_version": model_version,
            "variables": len(model.variables),
            "constraints": len(model.constraints),
            "solver_readiness": "READY",
            "graph_image": graph_b64
        }
        JOBS[job_id]["status"] = "READY"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        JOBS[job_id]["status"] = "FAILED"
        JOBS[job_id]["error"] = str(e)

class OptimizeRequest(BaseModel):
    problem_id: str

@router.post("/v2/optimize", response_model=DecisionPackage)
def optimize_model(request: OptimizeRequest) -> DecisionPackage:
    p_id = request.problem_id
    print(f"DEBUG: /v2/optimize called with p_id={p_id}. Current BUSINESS_STATES keys: {list(BUSINESS_STATES.keys())}")
    if p_id not in BUSINESS_STATES:
        raise HTTPException(status_code=404, detail="Problem ID not found.")
        
    model = model_service.load_model(p_id)
    state = BUSINESS_STATES[p_id]
    var_map = BUSINESS_VARIABLE_MAPS[p_id]
    
    # 1. Solve baseline
    solution = execution_backend.solve_auto(model)
    
    # 2. Update state
    state.previous_solution = solution
    state.objective = solution.objective_value
    state.feasibility = (solution.status == SolveStatus.OPTIMAL)
    state.optimality = (solution.status == SolveStatus.OPTIMAL)
    BUSINESS_STATES[p_id] = state
    
    # 3. Validation
    from src.service.validation_service import validation_service
    val_telemetry = validation_service.validate_solution(model, solution)
    if not val_telemetry.is_valid:
        solution.status = SolveStatus.ERROR
        solution.bound_violation = getattr(val_telemetry, 'bound_violation', 1.0)
        solution.constraint_residual = getattr(val_telemetry, 'primal_residual', 1.0)
        solution.integrality_violation = getattr(val_telemetry, 'integrality_violation', 1.0)
        
    # 4. Translate to DecisionPackage
    # Since this is baseline, we pass None for event and reopt_result
    package = ResultTranslator.translate(solution, var_map)
    package = ResultTranslator.attach_diagnostics(package, None, None)
    
    package.scenario.base_objective = state.objective or 0.0
    package.scenario.scenario_objective = state.objective or 0.0
    package.scenario.objective_delta = 0.0
    
    return package

@router.post("/v2/problem")
def create_problem(problem: BusinessProblemInput, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "QUEUED",
        "error": None,
        "progress": "Queued",
        "problem_summary": None
    }
    
    background_tasks.add_task(background_build_model, problem, job_id)
    
    return JOBS[job_id]

@router.get("/v2/jobs/{job_id}")
def get_job(job_id: str) -> Dict[str, Any]:
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return JOBS[job_id]

@router.post("/v2/reoptimize", response_model=DecisionPackage)
def reoptimize(request: BusinessEventRequest):
    problem_id = request.problem_id
    if problem_id not in BUSINESS_STATES:
        raise HTTPException(status_code=404, detail="Problem ID not found.")
        
    model = model_service.load_model(problem_id)
    state = BUSINESS_STATES[problem_id]
    var_map = BUSINESS_VARIABLE_MAPS[problem_id]
    
    # 1. Translate NLP to Event
    event = EventTranslator.parse_command(request.command)
    if not event:
        raise HTTPException(status_code=400, detail="Could not parse business command.")
        
    # 2. Reoptimize using existing orchestrator
    orchestrator = DeltaReoptimizationOrchestrator()
    reopt_result = orchestrator.run_adaptive_solve(model, [event], state)
    
    # 2.5 Enforce Global Validation Gateway
    from src.service.validation_service import validation_service
    val_telemetry = validation_service.validate_solution(model, reopt_result.solution)
    if not val_telemetry.is_valid:
        reopt_result.solution.status = SolveStatus.ERROR
        reopt_result.solution.bound_violation = getattr(val_telemetry, 'bound_violation', 1.0)
        reopt_result.solution.constraint_residual = getattr(val_telemetry, 'primal_residual', 1.0)
        reopt_result.solution.integrality_violation = getattr(val_telemetry, 'integrality_violation', 1.0)
    
    # 3. Translate math solution to Business Output
    package = ResultTranslator.translate(reopt_result.solution, var_map)
    package = ResultTranslator.attach_diagnostics(package, reopt_result, event)
    
    # 4. Update scenario metrics
    package.scenario.base_objective = state.objective or 0.0
    package.scenario.scenario_objective = reopt_result.solution.objective_value or 0.0
    package.scenario.objective_delta = package.scenario.scenario_objective - package.scenario.base_objective
    
    # 5. Visualizations
    active_nodes = getattr(reopt_result.diagnostics, 'active_nodes', [])
    active_edges = getattr(reopt_result.diagnostics, 'active_edges', [])
    
    package.visualization.graph_image = GraphVisualizer.generate_full_graph_base64(model, active_nodes, active_edges)
    package.visualization.active_graph_image = GraphVisualizer.generate_active_graph_base64(model, active_nodes, active_edges)
    
    # Update state for sequential events
    if reopt_result.solution.status == SolveStatus.OPTIMAL:
        state.previous_solution = reopt_result.solution
        state.objective = reopt_result.solution.objective_value
        BUSINESS_STATES[problem_id] = state
        
    return package

@router.get("/v2/graph/{problem_id}")
def get_graph(problem_id: str):
    if problem_id not in BUSINESS_STATES:
        raise HTTPException(status_code=404, detail="Problem ID not found.")
    
    state = BUSINESS_STATES[problem_id]
    model = model_service.load_model(problem_id)
    graph_data = GraphVisualizer.get_graph_data(model, state.entities)
    
    return {
        "graph_image": "",
        "nodes": graph_data["nodes"],
        "edges": graph_data["edges"]
    }

@router.get("/v2/state/{problem_id}")
def get_state(problem_id: str):
    if problem_id not in BUSINESS_STATES:
        raise HTTPException(status_code=404, detail="Problem ID not found.")
    state = BUSINESS_STATES[problem_id]
    return {
        "model_version": state.model_version,
        "objective": state.objective,
        "event_history_count": len(state.event_history)
    }
