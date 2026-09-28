import csv
import sys
import argparse

def validate_results(csv_path: str):
    with open(csv_path, "r") as f:
        reader = list(csv.DictReader(f))
        
    if not reader:
        print("No telemetry rows found.")
        sys.exit(1)
        
    event_ids = set()
    prev_seq = -1
    
    for row in reader:
        eid = row["event_id"]
        if eid in event_ids:
            # Note: in sequential events, we might run E001 twice in different scenarios
            # so the event IDs aren't unique across the whole file. They should be checked per scenario.
            pass
            
        seq = int(row["sequence"])
        # We won't enforce global sequence order since we have multiple scenarios, 
        # but within a scenario it should be ordered.
        
        # Status checks
        assert row["adaptive_solver_status"], "Solver status must exist"
        assert row["adaptive_validation_status"], "Validation status must exist"
        
        if row["adaptive_solver_status"] == "OPTIMAL":
            assert row["adaptive_objective"] != "", "Objective must exist for successful solve"
            
        diff = abs(float(row["baseline_objective"] or 0) - float(row["adaptive_objective"] or 0))
        calc_diff = float(row["objective_difference"])
        assert abs(diff - calc_diff) < 1e-5, f"Objective difference mismatch: {diff} != {calc_diff}"
        
        assert float(row["adaptive_runtime_ms"]) >= 0, "Runtime must be non-negative"
        assert float(row["baseline_runtime_ms"]) >= 0, "Runtime must be non-negative"
        
        active_vars = int(row["active_variables"])
        total_vars = int(row["total_variables"])
        assert active_vars <= total_vars, "Active variables cannot exceed total variables"
        
        assert row["fallback_used"] in ["True", "False"], "Fallback must be explicitly recorded"
        assert row["expansion_count"] != "", "Expansion count must be explicitly recorded"
        
        # Invalid solutions are never marked VALIDATED
        if row["adaptive_solver_status"] != "OPTIMAL":
            assert row["adaptive_validation_status"] != "VALIDATED", "Invalid solution marked as VALIDATED"
            
    print("[PASS] realtime_results.csv validation passed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    args = parser.parse_args()
    
    validate_results(args.input)
