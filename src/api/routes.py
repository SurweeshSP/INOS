import time
import uuid
import tempfile
import os
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, HTTPException
from src.api.schemas import (
    SolveRequestSchema, ReoptimizeRequestSchema, JobResponseSchema,
    SolveResponseSchema, BenchmarkRequestSchema, BenchmarkResponseSchema,
    ValidateRequestSchema, ValidateResponseSchema
)
from src.api.jobs import job_manager
from src.service.optimization_service import optimization_service
from src.service.model_service import model_service
from src.datasets.netlib import NetlibLoader
from src.datasets.mps_validator import MPSValidator
from src.solver.cpu import solve_cpu

router = APIRouter()

def process_solve(job_id: str, request: SolveRequestSchema):
    try:
        job_manager.update_job_status(job_id, "RUNNING")
        resp = optimization_service.solve(job_id, request)
        job_manager.update_job_status(job_id, "COMPLETED", resp.model_dump())
    except Exception as e:
        job_manager.update_job_status(job_id, "FAILED", {"error": str(e)})

def process_reoptimize(job_id: str, request: ReoptimizeRequestSchema):
    try:
        job_manager.update_job_status(job_id, "RUNNING")
        resp = optimization_service.reoptimize(job_id, request)
        job_manager.update_job_status(job_id, "COMPLETED", resp.model_dump())
    except Exception as e:
        import traceback
        traceback.print_exc()
        job_manager.update_job_status(job_id, "FAILED", {"error": str(e)})

@router.post("/v1/solve", response_model=JobResponseSchema)
def solve_endpoint(request: SolveRequestSchema, background_tasks: BackgroundTasks):
    job_id = job_manager.create_job()
    background_tasks.add_task(process_solve, job_id, request)
    return JobResponseSchema(job_id=job_id, status="QUEUED")

@router.post("/v1/reoptimize", response_model=JobResponseSchema)
def reoptimize_endpoint(request: ReoptimizeRequestSchema, background_tasks: BackgroundTasks):
    job_id = job_manager.create_job()
    background_tasks.add_task(process_reoptimize, job_id, request)
    return JobResponseSchema(job_id=job_id, status="QUEUED")

@router.get("/v1/jobs/{job_id}")
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if job.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/v1/jobs/{job_id}/result")
def get_job_result(job_id: str):
    job = job_manager.get_job(job_id)
    if job.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail="Job not found")
    if job.get("status") != "COMPLETED":
        raise HTTPException(status_code=400, detail="Job is not completed yet")
    return job.get("result")

@router.post("/v1/validate", response_model=ValidateResponseSchema)
def validate_endpoint(request: ValidateRequestSchema):
    from src.data_models import SolutionRecord, SolveStatus
    
    model = model_service.load_model(request.model_id)
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
        
    vars_array = None
    if request.solution.variables:
        n = len(model.c)
        import numpy as np
        vars_array = np.zeros(n)
        for k, v in request.solution.variables.items():
            idx = int(k.replace('v', ''))
            if idx < n:
                vars_array[idx] = v
                
    sol = SolutionRecord(
        status=SolveStatus[request.solution.status],
        objective_value=request.solution.objective,
        variables=vars_array
    )
    
    from src.service.validation_service import validation_service
    telemetry = validation_service.validate_solution(model, sol)
    return ValidateResponseSchema(is_valid=telemetry.is_valid, telemetry=telemetry)

@router.post("/v1/models/mps")
async def upload_mps(file: UploadFile = File(...)):
    """Accepts real MPS input, constructs canonical model, validates, returns metadata"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mps") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Load via existing parser
        loader = NetlibLoader(data_dir=os.path.dirname(tmp_path))
        instance_name = os.path.basename(tmp_path).split('.')[0]
        model = loader.load_instance(instance_name)
        
        # Save to persistence
        model_id = model_service.generate_model_id()
        model_service.save_model(model_id, model)

        return {
            "model_id": model_id,
            "variables": len(model.c),
            "constraints": len(model.b),
            "integer_variables": sum(model.variable_types == 1) if model.variable_types is not None else 0,
            "nonzeros": model.A.nnz if model.A is not None else 0
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.post("/v1/benchmark", response_model=BenchmarkResponseSchema)
def benchmark_endpoint(request: BenchmarkRequestSchema):
    """Run a real dataset instance locally, measure parse + solve."""
    from src.service.validation_service import validation_service
    
    from fastapi.responses import JSONResponse
    try:
        if request.instance is None:
            request.instance = request.dataset
            request.dataset = "netlib"
            
        t0 = time.time()
        # For now, default loader is NetlibLoader, but could be extended for MIPLIB/QPLIB based on request.dataset
        loader = NetlibLoader(data_dir="data/netlib")
        file_path = f"data/netlib/{request.instance}.mps"
        gz_path = f"{file_path}.gz"
        if not (os.path.exists(file_path) or os.path.exists(gz_path)):
            loader.download_subset([request.instance])
            
        model = loader.load_instance(request.instance)
        parse_ms = (time.time() - t0) * 1000.0
        
        has_integer = False
        if hasattr(model, 'variable_types') and model.variable_types is not None:
            has_integer = sum(model.variable_types == 1) > 0
        elif model.variables:
            from src.data_models import VariableType
            has_integer = any(v.var_type == VariableType.INTEGER or v.var_type == VariableType.BINARY for v in model.variables.values())
            
        t1 = time.time()
        if has_integer:
            # Integer variables exist, use node limit for safety in fast benchmark
            solution = solve_cpu(model, options={'node_limit': 100})
        else:
            solution = solve_cpu(model)
        solve_ms = (time.time() - t1) * 1000.0
        
        validation = validation_service.validate_solution(model, solution)
        
        final_status = solution.status.name
        if solution.status.name == "OPTIMAL" and not validation.is_valid:
            final_status = "VALIDATION_FAILURE"
            
        return BenchmarkResponseSchema(
            instance=request.instance,
            parse_ms=parse_ms,
            solve_ms=solve_ms,
            variables=len(model.c),
            constraints=len(model.b),
            nonzeros=model.A.nnz if model.A is not None else 0,
            integer_variables=int(sum(1 for v in model.variables.values() if v.var_type.name in ['INTEGER', 'BINARY'])) if model.variables else 0,
            status=final_status,
            validated=validation.is_valid
        )
    except Exception as e:
        import traceback
        import sys
        print(f"Benchmark execution failed: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "BENCHMARK_EXECUTION_FAILED",
                    "message": str(e),
                    "stage": "parser" if "row" in str(e).lower() or "mps" in str(e).lower() else "solver",
                    "instance": request.instance
                }
            }
        )
