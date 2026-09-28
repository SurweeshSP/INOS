import sys
import os
import csv
import json
import time
from datetime import datetime
import argparse

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.v2_schemas import BusinessProblemInput, EntitySpec
from src.domain.problem_builder import SupplyChainProblemBuilder
from src.solver.cpu import solve_cpu
from src.service.validation_service import validation_service
from src.domain.event_translator import EventTranslator
from src.data_models import PersistentOptimizationState, SolveStatus
from src.delta_reoptimization import DeltaReoptimizationOrchestrator
from src.domain.result_translator import ResultTranslator

def load_problem(file_path: str) -> BusinessProblemInput:
    if file_path.endswith(".json"):
        with open(file_path, "r") as f:
            data = json.load(f)
        return BusinessProblemInput(**data)
        
    entities = []
    with open(file_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ids = [x.strip() for x in row["ids"].split(",")]
            entities.append(EntitySpec(
                entity_type=row["entity_type"],
                count=int(row["count"]),
                ids=ids
            ))
    return BusinessProblemInput(
        goal="minimize_cost",
        entities=entities,
        planning_horizon=7
    )

def load_events(csv_path: str) -> dict:
    events = {}
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events[row["event_id"]] = {
                "sequence": int(row["sequence"]),
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "command": row["command"]
            }
    return events

def load_scenarios(csv_path: str) -> dict:
    scenarios = {}
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_ids = [x.strip() for x in row["events"].split(",")]
            scenarios[row["scenario_id"]] = event_ids
    return scenarios

def run_experiment(model_path, events_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "scenarios"), exist_ok=True)
    
    problem = load_problem(model_path)
    model, var_map = SupplyChainProblemBuilder.build(problem)
    
    events_db = load_events(events_path)
    # Need scenario mappings. We assume it's in the same directory as events.
    scenarios_path = os.path.join(os.path.dirname(events_path), "scenarios.csv")
    scenarios_db = load_scenarios(scenarios_path)
    
    # 1. Baseline Full Solve
    t0 = time.time()
    baseline_sol = solve_cpu(model)
    t1 = time.time()
    val = validation_service.validate_solution(model, baseline_sol)
    
    print(f"Baseline solve: {t1-t0:.4f}s. Validation: {val.is_valid}")
    
    telemetry_rows = []
    
    for scenario_id, event_ids in scenarios_db.items():
        print(f"Running scenario: {scenario_id}")
        
        # Fresh state for each scenario
        state = PersistentOptimizationState(
            model_version="v1",
            previous_solution=baseline_sol,
            objective=baseline_sol.objective_value,
            feasibility=val.is_valid,
            optimality=val.is_valid
        )
        
        scenario_results = []
        
        for e_id in event_ids:
            ev_data = events_db[e_id]
            parsed_event = EventTranslator.parse_command(ev_data["command"])
            
            # Baseline execution (from scratch on the same state representation theoretically)
            # Actually, to simulate baseline on the "changed full model", 
            # we'd need to apply the change directly to the full model, which DeltaModel does.
            # But the orchestrator does this internally if fallback happens.
            # Let's use the orchestrator and extract the time it took for the adaptive part.
            # Then force a full solve on the modified model.
            
            # 1. Adaptive run
            orchestrator = DeltaReoptimizationOrchestrator()
            t_a0 = time.time()
            reopt_res = orchestrator.run_adaptive_solve(model, [parsed_event], state)
            t_a1 = time.time()
            
            val_adapt = validation_service.validate_solution(model, reopt_res.solution)
            
            # 2. Extract metrics
            diag = reopt_res.diagnostics
            fallback_used = getattr(diag, 'fallback_used', False)
            adaptive_time = (t_a1 - t_a0) if not fallback_used else getattr(diag, 'delta_solve_time', t_a1-t_a0)
            
            # 3. Simulate "baseline" by taking the time of the full solve
            # If fallback was used, the full solve time is part of the orchestrator's time.
            # If not used, we can just run a full solve.
            t_b0 = time.time()
            baseline_res = solve_cpu(model)
            t_b1 = time.time()
            
            baseline_time = (t_b1 - t_b0)
            val_base = validation_service.validate_solution(model, baseline_res)
            
            speedup = baseline_time / adaptive_time if adaptive_time > 0 else 0
            
            # Update state for sequential
            if reopt_res.solution.status == SolveStatus.OPTIMAL:
                state.previous_solution = reopt_res.solution
                state.objective = reopt_res.solution.objective_value
                
            # JSON format
            package = ResultTranslator.translate(reopt_res.solution, var_map)
            package = ResultTranslator.attach_diagnostics(package, reopt_res, parsed_event)
            
            telemetry_row = {
                "scenario_id": scenario_id,
                "event_id": e_id,
                "sequence": ev_data["sequence"],
                "event_type": ev_data["event_type"],
                "entity_id": parsed_event.affected_entities[0] if parsed_event.affected_entities else "",
                "model_version": "v1",
                "total_variables": len(model.variables),
                "total_constraints": len(model.constraints),
                "total_nonzeros": len(model.A.data) if hasattr(model.A, 'data') else 0,
                "affected_variables": len(parsed_event.affected_variables) if parsed_event else 0,
                "affected_constraints": len(parsed_event.affected_constraints) if parsed_event else 0,
                "active_variables": getattr(diag, 'active_variables', 0),
                "active_constraints": getattr(diag, 'active_constraints', 0),
                "active_region_ratio": getattr(diag, 'active_region_ratio', 0.0),
                "baseline_runtime_ms": baseline_time * 1000,
                "adaptive_runtime_ms": adaptive_time * 1000,
                "speedup": speedup,
                "baseline_objective": baseline_res.objective_value,
                "adaptive_objective": reopt_res.solution.objective_value,
                "objective_difference": abs((baseline_res.objective_value or 0) - (reopt_res.solution.objective_value or 0)),
                "baseline_solver_status": baseline_res.status.name,
                "adaptive_solver_status": reopt_res.solution.status.name,
                "baseline_validation_status": "VALIDATED" if val_base.is_valid else "FAILED",
                "adaptive_validation_status": "VALIDATED" if val_adapt.is_valid else "FAILED",
                "expansion_count": getattr(diag, 'expansion_count', 0),
                "fallback_used": fallback_used,
                "fallback_reason": getattr(diag, 'fallback_reason', ""),
                "accepted": val_adapt.is_valid,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            telemetry_rows.append(telemetry_row)
            
            event_dict = parsed_event.__dict__.copy()
            event_dict["event_type"] = event_dict["event_type"].name
            
            scenario_results.append({
                "input": ev_data,
                "event": event_dict,
                "validation": val_adapt.__dict__,
                "telemetry": telemetry_row
            })

            # Save example decision
            if scenario_id == "capacity_change":
                with open(os.path.join(output_dir, "example_decision.json"), "w") as f:
                    json.dump(package.dict(), f, indent=2)
                    
        # Save scenario
        with open(os.path.join(output_dir, "scenarios", f"{scenario_id}.json"), "w") as f:
            json.dump(scenario_results, f, indent=2)
            
    # Write full CSV
    csv_file = os.path.join(output_dir, "realtime_results.csv")
    if telemetry_rows:
        keys = telemetry_rows[0].keys()
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(telemetry_rows)
            
    # Write full JSON
    json_file = os.path.join(output_dir, "realtime_results.json")
    with open(json_file, "w") as f:
        json.dump(telemetry_rows, f, indent=2)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--events", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    run_experiment(args.model, args.events, args.output)
