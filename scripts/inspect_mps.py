import sys
import os
import time
import json
from src.datasets.netlib import NetlibLoader
from src.solver.cpu import solve_cpu
from src.data_models import OptimizationModel, ProblemType, SolveStatus, VariableType

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_mps.py <instance_name>")
        sys.exit(1)
        
    instance_name = sys.argv[1]
    
    print(f"Loading {instance_name}...")
    loader = NetlibLoader(data_dir="data/netlib")
    
    # Check if we already have it
    file_path = os.path.join("data/netlib", f"{instance_name.lower()}.mps")
    gz_path = f"{file_path}.gz"
    if not (os.path.exists(file_path) or os.path.exists(gz_path)):
        loader.download_subset([instance_name])
    
    t0 = time.time()
    try:
        model = loader.load_instance(instance_name)
    except Exception as e:
        print(f"Error parsing MPS: {e}")
        sys.exit(1)
    parse_time = time.time() - t0
    
    print(f"\n--- Model Stats ---")
    print(f"Name: {model.name}")
    print(f"Variables: {len(model.variables)}")
    print(f"Constraints: {len(model.constraints)}")
    
    int_count = sum(1 for v in model.variables.values() if v.var_type in (VariableType.INTEGER, VariableType.BINARY))
    print(f"Integer/Binary variables: {int_count}")
    
    print(f"Matrix A shape: {model.A.shape}")
    print(f"Matrix A Non-zeros: {model.A.nnz}")
    print(f"Lower bounds size: {len(model.lower_bounds)}")
    print(f"Upper bounds size: {len(model.upper_bounds)}")
    
    if int_count > 0:
        print(f"Integer variables found. Relaxing to LP for benchmark...")
        model.problem_type = ProblemType.LP
        
    t1 = time.time()
    solution = solve_cpu(model)
    solve_time = time.time() - t1
        
    print(f"\n--- Solve Results ---")
    print(f"Status: {solution.status.name}")
    if solution.status == SolveStatus.OPTIMAL:
        print(f"Objective Value: {solution.objective_value}")
    print(f"Solve Time: {solve_time:.4f}s")
    
    # Save results
    os.makedirs("results/mps", exist_ok=True)
    results = {
        "instance": instance_name,
        "parse_time_s": parse_time,
        "solve_time_s": solve_time,
        "variables": len(model.variables),
        "constraints": len(model.constraints),
        "nonzeros": model.A.nnz,
        "integers": int_count,
        "status": solution.status.name,
        "objective": float(solution.objective_value) if solution.status == SolveStatus.OPTIMAL else None
    }
    
    out_path = f"results/mps/{instance_name.lower()}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {out_path}")

if __name__ == "__main__":
    main()
