import argparse
import json
import time
from pathlib import Path
import sys

# Add project root to sys.path
root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from src.datasets.miplib import load_miplib_instance
from src.datasets.qplib import load_qplib_instance
from src.datasets.dynamic import load_dynamic_scenario
from src.solver.cpu import solve_cpu
from src.global_validation import GlobalValidator
from src.data_models import SolveStatus

def main():
    parser = argparse.ArgumentParser(description="Run optimization on a real dataset instance.")
    parser.add_argument('--dataset', type=str, required=True, choices=['miplib', 'qplib', 'dynamic', 'netlib', 'isomorph', 'logior'])
    parser.add_argument('--instance', type=str, required=True, help="Path to instance file or instance name")
    
    args = parser.parse_args()
    
    instance_path = Path(args.instance)
    if not instance_path.exists():
        # Try to resolve relative to data/
        instance_path = root_dir / "data" / args.dataset / args.instance
        if not instance_path.exists():
            # For qplib try html/lp/
            if args.dataset == 'qplib':
                instance_path = root_dir / "data" / "qplib" / "qplib" / "html" / "lp" / args.instance
                
    if not instance_path.exists():
        print(f"Error: Instance file not found at {instance_path}")
        sys.exit(1)
        
    print(f"Loading {args.dataset} instance from {instance_path}...")
    start_load = time.time()
    
    if args.dataset == 'miplib':
        model = load_miplib_instance(instance_path)
    elif args.dataset == 'qplib':
        model = load_qplib_instance(instance_path)
    elif args.dataset == 'dynamic':
        model = load_dynamic_scenario(instance_path)
    else:
        print(f"Dataset {args.dataset} loader not implemented yet.")
        sys.exit(1)
        
    load_time = time.time() - start_load
    print(f"Model loaded in {load_time:.2f}s")
    print(f"Variables: {len(model.variables)}")
    print(f"Constraints: {len(model.constraints)}")
    
    print("\nSolving model...")
    start_solve = time.time()
    
    # Solve using indigenous engine
    solution = solve_cpu(model)
    
    solve_time = time.time() - start_solve
    print(f"Solve completed in {solve_time:.2f}s")
    print(f"Status: {solution.status.name}")
    print(f"Objective: {solution.objective_value}")
    
    print("\nValidating solution...")
    validator = GlobalValidator()
    val_result = validator.validate(model, solution)
    
    print(f"Validation Valid: {val_result.is_valid}")
    for violation in val_result.violated_constraints:
        print(f"  Violation: {violation}")
        
    # Save results
    results_dir = root_dir / "results"
    results_dir.mkdir(exist_ok=True)
    
    result_data = {
        "dataset": args.dataset,
        "instance": instance_path.name,
        "load_time": load_time,
        "solve_time": solve_time,
        "status": solution.status.name,
        "objective": solution.objective_value,
        "validation_passed": val_result.is_valid,
        "violations": val_result.violated_constraints,
        "vars": len(model.variables),
        "constraints": len(model.constraints)
    }
    
    out_file = results_dir / f"{args.dataset}_{instance_path.name}_result.json"
    with open(out_file, 'w') as f:
        json.dump(result_data, f, indent=2)
        
    print(f"\nResult saved to {out_file}")

if __name__ == "__main__":
    main()
