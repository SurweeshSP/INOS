import os
import sys
import time
import json
import argparse
import copy

from src.datasets.netlib import NetlibLoader
from src.datasets.miplib import MiplibLoader
from src.solver.cpu import solve_cpu
from src.global_validation import GlobalValidator
from src.delta_reoptimization import DeltaReoptimizationOrchestrator
from src.data_models import Event, EventType

def run_realtime_reoptimization(model_name: str):
    print(f"========================================")
    print(f"REAL-TIME REOPTIMIZATION TEST")
    print(f"========================================")
    
    # 1. Load real model
    print(f"Loading base model {model_name}...")
    loader = NetlibLoader(data_dir="data/netlib")
    if os.path.exists(f"data/netlib/{model_name}.mps") or os.path.exists(f"data/netlib/{model_name}.mps.gz"):
        model = loader.load_instance(model_name)
    else:
        loader = MiplibLoader(data_dir="data/miplib")
        model = loader.load_instance(model_name)
        
    print(f"Variables: {len(model.c)}, Constraints: {len(model.b)}")
    
    # 2. Solve baseline
    t0 = time.time()
    print("Solving baseline...")
    base_solution = solve_cpu(model)
    baseline_time_ms = (time.time() - t0) * 1000.0
    print(f"Baseline objective: {base_solution.objective_value}")
    
    # 3. Save baseline solution (we just keep it in memory for the orchestrator)
    base_state = base_solution
    
    # 4. Create a real parameter event
    target_constraint_idx = 0
    old_rhs = model.b[target_constraint_idx]
    new_rhs = old_rhs * 1.1 if old_rhs != 0 else 10.0
    
    constraint_names = list(model.constraints.keys())
    target_constraint_name = constraint_names[0] if constraint_names else f"row_{target_constraint_idx}"
    
    event = Event(
        event_type=EventType.CAPACITY_CHANGE,
        affected_constraints=[target_constraint_name],
        old_value=float(old_rhs),
        new_value=float(new_rhs)
    )
    
    print(f"\nEvent generated: Changed RHS of {target_constraint_name} from {old_rhs} to {new_rhs}")
    
    # 5. Run adaptive reoptimization
    t1 = time.time()
    orchestrator = DeltaReoptimizationOrchestrator()
    from src.data_models import PersistentOptimizationState
    p_state = PersistentOptimizationState(model_version="v1", previous_solution=base_state)
    
    update_result = orchestrator.run_adaptive_solve(model, [event], p_state)
    reopt_time_ms = (time.time() - t1) * 1000.0
    
    new_solution = update_result.solution
    
    # 6. Globally validate
    print("Validating new solution globally...")
    t2 = time.time()
    global_validator = GlobalValidator()
    val_model = copy.deepcopy(model)
    val_model.b[target_constraint_idx] = new_rhs
    if target_constraint_name in val_model.constraints:
        val_model.constraints[target_constraint_name].rhs = new_rhs
    
    validation_res = global_validator.validate(val_model, new_solution)
    validation_time_ms = (time.time() - t2) * 1000.0
    
    adaptive_success = update_result.diagnostics.adaptive_success and validation_res.is_valid
    
    # 7. Print diagnostics
    print("\n==========================================")
    print("ADAPTIVE DIAGNOSTICS")
    print("==========================================")
    print(f"MODEL:                      {model_name}")
    print(f"MODEL VERSION:              v2 (Delta)")
    print(f"BASELINE OBJECTIVE:         {base_solution.objective_value}")
    print(f"EVENT:                      {event.event_type.name} on {event.affected_constraints}")
    print(f"INITIAL ADS SIZE:           {update_result.diagnostics.initial_ADS_size}")
    print(f"FINAL ADS SIZE:             {update_result.diagnostics.final_ADS_size}")
    print(f"EXPANSIONS:                 {update_result.diagnostics.number_of_expansions}")
    print(f"REOPTIMIZATION STRATEGY:    {'FALLBACK' if update_result.diagnostics.fallback_used else 'ADAPTIVE'}")
    print(f"NEW OBJECTIVE:              {new_solution.objective_value}")
    print(f"VALIDATION STATUS:          {'VALID' if validation_res.is_valid else 'INVALID'}")
    print(f"FALLBACK USED:              {update_result.diagnostics.fallback_used}")
    print(f"TOTAL RUNTIME:              {reopt_time_ms:.2f} ms")
    print("==========================================\n")
    
    # 8. Save updated result and telemetry
    os.makedirs("data/runtime/telemetry", exist_ok=True)
    os.makedirs("results/realtime", exist_ok=True)
    
    telemetry = {
        "timestamp": time.time(),
        "model_id": model_name,
        "solver": "solve_cpu",
        "strategy": "FALLBACK" if update_result.diagnostics.fallback_used else "ADAPTIVE",
        "variables": len(model.c),
        "constraints": len(model.b),
        "nonzeros": model.A.nnz,
        
        "baseline_time_ms": baseline_time_ms,
        "delta_solve_time_ms": reopt_time_ms,
        "validation_time_ms": validation_time_ms,
        "total_time_ms": baseline_time_ms + reopt_time_ms + validation_time_ms,
        
        "objective_before": base_solution.objective_value,
        "objective_after": new_solution.objective_value,
        "objective_delta": (new_solution.objective_value - base_solution.objective_value) if (new_solution.objective_value is not None and base_solution.objective_value is not None) else None,
        
        "ads_initial_size": update_result.diagnostics.initial_ADS_size,
        "ads_final_size": update_result.diagnostics.final_ADS_size,
        "expansions": update_result.diagnostics.number_of_expansions,
        "fallback_used": update_result.diagnostics.fallback_used,
        
        "solver_status": new_solution.status.name if new_solution and new_solution.status else "ERROR",
        "validation_status": "VALID" if validation_res.is_valid else "INVALID",
        "adaptive_success": adaptive_success
    }
    
    with open(f"data/runtime/telemetry/{model_name}_reopt.json", "w") as f:
        json.dump(telemetry, f, indent=2)
        
    print(f"Telemetry saved to data/runtime/telemetry/{model_name}_reopt.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run real-time reoptimization.")
    parser.add_argument("--model", type=str, required=True, help="Name of the instance (e.g. flugpl)")
    args = parser.parse_args()
    
    m_name = args.model.replace("-demo", "")
    run_realtime_reoptimization(m_name)
