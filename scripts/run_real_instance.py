import os
import sys
import time
import json
import argparse
from typing import Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.datasets.mps_validator import MPSValidator
from src.trust.model_validator import ModelValidator
from src.solver.cpu import solve_cpu
from src.global_validation import GlobalValidator
from src.data_models import VariableType, SolveStatus, ProblemType

def find_instance(instance_name: str) -> Optional[tuple[str, str]]:
    paths = {
        "MIPLIB": f"data/miplib/{instance_name}.mps.gz",
        "NETLIB": f"data/netlib/{instance_name}.mps.gz",
        "MIPLIB_UNCOMPRESSED": f"data/miplib/{instance_name}.mps",
        "NETLIB_UNCOMPRESSED": f"data/netlib/{instance_name}.mps"
    }
    
    # Check if instance already has an extension
    if instance_name.endswith(".mps") or instance_name.endswith(".mps.gz"):
        if os.path.exists(f"data/miplib/{instance_name}"):
            return f"data/miplib/{instance_name}", "MIPLIB"
        if os.path.exists(f"data/netlib/{instance_name}"):
            return f"data/netlib/{instance_name}", "NETLIB"
            
    for source, path in paths.items():
        if os.path.exists(path):
            return path, source.split("_")[0]
            
    if os.path.exists(instance_name):
        return instance_name, "UNKNOWN"
        
    return None, None

def run_instance(instance_name: str):
    path, source = find_instance(instance_name)
    if not path:
        print(f"Error: Instance {instance_name} not found in data directories.")
        sys.exit(1)
        
    print(f"Loading {instance_name} from {source}...")
    
    t0 = time.time()
    
    # 1. & 2. Parse MPS and Convert to OptimizationModel
    if source == "MIPLIB":
        from src.datasets.miplib import MiplibLoader
        loader = MiplibLoader(data_dir=os.path.dirname(path))
        # Instance name should be without path and extension
        inst_name = os.path.basename(path).replace('.mps', '').replace('.gz', '')
        model = loader.load_instance(inst_name)
    else:
        from src.datasets.netlib import NetlibLoader
        loader = NetlibLoader(data_dir=os.path.dirname(path))
        inst_name = os.path.basename(path).replace('.mps', '').replace('.gz', '')
        model = loader.load_instance(inst_name)
    
    # 3. Model validation
    val_result = ModelValidator.validate(model)
    if not val_result.valid:
        print("Model validation failed:")
        for err in val_result.errors:
            print(f" - {err}")
        
    parse_time_ms = (time.time() - t0) * 1000.0
    
    n_vars = len(model.variables) if model.variables else (len(model.c) if hasattr(model, 'c') and model.c is not None else 0)
    n_cons = len(model.constraints) if model.constraints else (len(model.b) if hasattr(model, 'b') and model.b is not None else 0)
    n_nnz = model.A.nnz if hasattr(model, 'A') and model.A is not None else 0
    
    int_vars = 0
    bin_vars = 0
    for v in model.variables.values():
        if v.var_type == VariableType.INTEGER:
            int_vars += 1
        elif v.var_type == VariableType.BINARY:
            bin_vars += 1
            
    if not model.variables and hasattr(model, 'variable_types') and model.variable_types is not None:
        int_vars = sum(model.variable_types == 1)
        bin_vars = sum(model.variable_types == 2)

    print("Solving...")
    t1 = time.time()
    solution = solve_cpu(model)
    solve_time_ms = (time.time() - t1) * 1000.0
    
    print("Validating globally...")
    global_validator = GlobalValidator()
    
    # If the solver didn't return primal values or variables but returned an optimal status, we still validate
    validation_res = global_validator.validate(model, solution)
    
    is_validated = validation_res.is_valid and solution.status in (SolveStatus.OPTIMAL, SolveStatus.SUBOPTIMAL)
    validation_status = "VALIDATION_SUCCESS" if is_validated else "VALIDATION_FAILURE"
    
    if solution.status == SolveStatus.INFEASIBLE:
        validation_status = "INFEASIBLE"
    elif solution.status == SolveStatus.ERROR:
        validation_status = "SOLVER_FAILURE"
    elif not val_result.valid:
        validation_status = "MODEL_VALIDATION_FAILURE"
        is_validated = False

    result_payload = {
        "instance": instance_name,
        "source": source,
        "variables": n_vars,
        "constraints": n_cons,
        "nonzeros": n_nnz,
        "integer_variables": int_vars,
        "binary_variables": bin_vars,
        
        "parse_time_ms": parse_time_ms,
        "solve_time_ms": solve_time_ms,
        
        "solver_status": solution.status.name,
        
        "objective_solver": solution.objective_value,
        "objective_recomputed": None,
        
        "primal_residual": validation_res.diagnostics.max_violation,
        "bound_violation": validation_res.diagnostics.number_of_bound_violations,
        "integrality_violation": validation_res.diagnostics.number_of_integrality_violations,
        
        "validation_status": validation_status,
        "validated": is_validated
    }
    
    if solution.objective_value is not None:
        result_payload["objective_recomputed"] = solution.objective_value + validation_res.diagnostics.objective_difference
    elif validation_res.diagnostics.objective_difference:
        result_payload["objective_recomputed"] = validation_res.diagnostics.objective_difference
    else:
        result_payload["objective_recomputed"] = 0.0

    print("\n==========================================")
    print("EXECUTION REPORT")
    print("==========================================")
    print(f"problem_type:      {model.problem_type.name}")
    print(f"solver_type:       CPU (solve_cpu dispatch)")
    print(f"relaxation_used:   {'YES' if model.problem_type == ProblemType.MILP else 'NO'}")
    print(f"integer_variables: {int_vars}")
    print(f"binary_variables:  {bin_vars}")
    print(f"solver_status:     {solution.status.name}")
    print(f"validation_status: {validation_status}")
    print("==========================================\n")
    
    os.makedirs("results/realtime", exist_ok=True)
    out_path = f"results/realtime/{instance_name.split('.')[0]}.json"
    with open(out_path, "w") as f:
        json.dump(result_payload, f, indent=2)
        
    print(f"Result written to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run real MPS instance.")
    parser.add_argument("--instance", type=str, required=True, help="Name of the instance (e.g. flugpl)")
    args = parser.parse_args()
    
    run_instance(args.instance)
