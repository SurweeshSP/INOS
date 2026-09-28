import os
import json
import time
import subprocess
import argparse
import numpy as np
from typing import List, Dict
from src.data_models import ProblemType

def generate_markdown_report(results: List[Dict], output_file: str):
    with open(output_file, "w") as f:
        f.write("# SupplyChainOptii Benchmark Results\n\n")
        f.write("## Section A: Real vs Synthetic Integrity\n")
        real_count = sum(1 for r in results if not r.get('is_synthetic', False) and r['status'] != 'ERROR')
        synth_count = sum(1 for r in results if r.get('is_synthetic', False) and r['status'] != 'ERROR')
        f.write(f"- Real Instances Processed: {real_count}\n")
        f.write(f"- Synthetic Fallbacks: {synth_count}\n\n")
        
        f.write("## Section B: Validation & Correctness\n")
        valid_count = sum(1 for r in results if r.get('valid', False))
        f.write(f"- Independent Validation Pass Rate: {valid_count}/{len(results)}\n\n")
        
        f.write("## Section C: Solver Performance vs HiGHS Reference\n")
        f.write("| Instance | Type | Status | Objective | Time (s) | HiGHS Status | HiGHS Obj | HiGHS Time (s) |\n")
        f.write("|----------|------|--------|-----------|----------|--------------|-----------|----------------|\n")
        for r in results:
            if r['status'] == 'ERROR': continue
            itype = "Synth" if r.get('is_synthetic', False) else "Real"
            ref = r.get('reference', {})
            ref_stat = ref.get('status', 'N/A')
            ref_obj = f"{ref.get('objective'):.4f}" if ref.get('objective') is not None else "N/A"
            ref_time = f"{ref.get('time', 0):.4f}"
            obj = f"{r.get('objective'):.4f}" if r.get('objective') is not None else "N/A"
            time_val = f"{r.get('time', 0):.4f}"
            f.write(f"| {r['instance']} | {itype} | {r['status']} | {obj} | {time_val} | {ref_stat} | {ref_obj} | {ref_time} |\n")

def main():
    parser = argparse.ArgumentParser(description="SupplyChainOptii Final Benchmark Suite")
    parser.add_argument("--mode", choices=["fast", "full"], default="fast", help="fast (smoke test) or full (paper benchmark)")
    args = parser.parse_args()

    results_dir = "results/benchmarks"
    os.makedirs(results_dir, exist_ok=True)
    
    # 1. Netlib LP Instances
    netlib_instances = ["afiro", "adlittle", "sc50a", "blend"]
    if args.mode == "full":
        netlib_instances.extend(["kb2", "sc105", "sc205", "share2b", "stocfor1"])
        
    # 2. MIPLIB Instances
    miplib_instances = ["flugpl", "enclave"]
    
    # 3. QPLIB / Custom QP
    qp_instances = ["qap04"] # Example if available, fallback will trigger if not
    
    results = []
    
    print("========================================")
    print(f"Starting Benchmark Suite (Mode: {args.mode})")
    print("========================================")
    
    all_instances = [("netlib", inst) for inst in netlib_instances] + \
                    [("miplib", inst) for inst in miplib_instances] + \
                    [("qplib", inst) for inst in qp_instances]
                    
    for dataset, instance in all_instances:
        print(f"\n--- Benchmarking {dataset}/{instance} ---")
        
        from src.datasets.netlib import NetlibLoader
        from src.solver.cpu import solve_cpu
        from src.service.validation_service import validation_service
        
        loader = NetlibLoader()
        try:
            loader.download_subset([instance])
            model = loader.load_instance(instance)
            
            t0 = time.time()
            solution = solve_cpu(model, options={'time_limit': 60.0})
            elapsed = time.time() - t0
            
            validation = validation_service.validate_solution(model, solution)
            
            print(f"Status: {solution.status.name}")
            print(f"Objective: {solution.objective_value}")
            print(f"Validation: {'VALID' if validation.is_valid else 'INVALID'}")
            print(f"Time: {elapsed:.2f}s")
            
            is_synthetic = getattr(model, 'is_synthetic_fallback', False)
            
            # --- Reference Solver (HiGHS) ---
            ref_status = "NOT_RUN"
            ref_objective = None
            ref_time = 0.0
            
            if model.problem_type == ProblemType.LP and not is_synthetic:
                try:
                    from src.solver.lp.standardization import Standardizer
                    stdizer = Standardizer()
                    std_lp = stdizer.standardize(model)
                    
                    bounds = [(lb, ub if ub != np.inf else None) for lb, ub in zip(std_lp.lower_bounds, std_lp.upper_bounds)]
                    
                    t_ref0 = time.time()
                    import scipy.optimize
                    res = scipy.optimize.linprog(
                        c=std_lp.c,
                        A_ub=std_lp.A_ub if len(std_lp.b_ub) > 0 else None,
                        b_ub=std_lp.b_ub if len(std_lp.b_ub) > 0 else None,
                        A_eq=std_lp.A_eq if len(std_lp.b_eq) > 0 else None,
                        b_eq=std_lp.b_eq if len(std_lp.b_eq) > 0 else None,
                        bounds=bounds,
                        method='highs',
                        options={'disp': False}
                    )
                    ref_time = time.time() - t_ref0
                    
                    if res.success:
                        ref_status = "OPTIMAL"
                        ref_objective = res.fun
                        if hasattr(model, 'objective_offset'):
                            ref_objective -= model.objective_offset
                    else:
                        ref_status = "INFEASIBLE"
                except Exception as e:
                    print(f"HiGHS error: {e}")
            
            telemetry = {
                "primal_residual": validation.primal_residual,
                "bound_violation": validation.bound_violation,
                "iterations": solution.iterations,
                "time": elapsed
            }
            
            if not is_synthetic and validation.is_valid and solution.status.name == "OPTIMAL":
                certificate = {
                    "instance": instance,
                    "dataset": dataset,
                    "status": solution.status.name,
                    "objective": solution.objective_value,
                    "validation_telemetry": telemetry,
                    "timestamp": time.time(),
                    "version": "1.0.0"
                }
                with open(f"{results_dir}/certificate_{instance}.json", "w") as f:
                    json.dump(certificate, f, indent=2)
            
            results.append({
                "dataset": dataset,
                "instance": instance,
                "is_synthetic": is_synthetic,
                "status": solution.status.name,
                "objective": solution.objective_value,
                "time": elapsed,
                "valid": validation.is_valid,
                "telemetry": telemetry,
                "reference": {
                    "status": ref_status,
                    "objective": ref_objective,
                    "time": ref_time
                }
            })
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "dataset": dataset,
                "instance": instance,
                "status": "ERROR",
                "error": str(e)
            })
            
    with open(f"{results_dir}/benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    generate_markdown_report(results, "reports/BENCHMARK_RESULTS.md")
        
    print("\nBenchmark Suite Complete.")
    print(f"Results saved to {results_dir}/benchmark_results.json")
    print(f"Markdown report generated at reports/BENCHMARK_RESULTS.md")
    
if __name__ == "__main__":
    main()
