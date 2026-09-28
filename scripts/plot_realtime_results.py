import csv
import sys
import argparse
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot_results(csv_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    with open(csv_path, "r") as f:
        reader = list(csv.DictReader(f))
        
    if not reader:
        print("No telemetry rows found.")
        sys.exit(1)
        
    events = [r["event_id"] for r in reader]
    baseline_times = [float(r["baseline_runtime_ms"]) for r in reader]
    adaptive_times = [float(r["adaptive_runtime_ms"]) for r in reader]
    speedups = [float(r["speedup"]) for r in reader]
    active_ratios = [float(r["active_region_ratio"]) for r in reader]
    fallbacks = [1 if r["fallback_used"] == "True" else 0 for r in reader]
    
    # 1. Runtime comparison
    plt.figure(figsize=(10, 6))
    plt.plot(baseline_times, label="Baseline (ms)", marker="o")
    plt.plot(adaptive_times, label="Adaptive (ms)", marker="x")
    plt.xlabel("Event Execution Sequence")
    plt.ylabel("Runtime (ms)")
    plt.title("Baseline vs Adaptive Runtime Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "realtime_runtime_comparison.png"))
    plt.close()
    
    # 2. Speedup
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(speedups)), speedups, color="green")
    plt.axhline(y=1.0, color='r', linestyle='--')
    plt.xlabel("Event Execution Sequence")
    plt.ylabel("Speedup Factor")
    plt.title("Adaptive Reoptimization Speedup")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "realtime_speedup.png"))
    plt.close()
    
    # 3. Active Region Ratio
    plt.figure(figsize=(10, 6))
    plt.hist(active_ratios, bins=10, color="blue", alpha=0.7)
    plt.xlabel("Active Region Ratio")
    plt.ylabel("Frequency")
    plt.title("Active Region Size Distribution")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "active_region_ratio.png"))
    plt.close()
    
    # 4. Sequential Event Runtime (specifically filtering for sequential_10_events)
    seq_runs = [r for r in reader if r["scenario_id"] == "sequential_10_events"]
    if seq_runs:
        plt.figure(figsize=(10, 6))
        plt.plot([float(r["adaptive_runtime_ms"]) for r in seq_runs], label="Adaptive (ms)", marker="x")
        plt.plot([float(r["baseline_runtime_ms"]) for r in seq_runs], label="Baseline (ms)", marker="o")
        plt.xlabel("Sequence Step")
        plt.ylabel("Runtime (ms)")
        plt.title("Sequential Event Runtime (10 Events)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "sequential_event_runtime.png"))
        plt.close()
    
    # 5. Fallback rate
    plt.figure(figsize=(6, 6))
    fallback_count = sum(fallbacks)
    success_count = len(fallbacks) - fallback_count
    plt.pie([success_count, fallback_count], labels=["Adaptive Success", "Fallback Used"], autopct='%1.1f%%', colors=["lightgreen", "salmon"])
    plt.title("Fallback Rate")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "fallback_rate.png"))
    plt.close()
    
    # 6. Validation Results
    validations = [r["adaptive_validation_status"] for r in reader]
    valid_c = validations.count("VALIDATED")
    invalid_c = len(validations) - valid_c
    plt.figure(figsize=(6, 6))
    plt.bar(["VALIDATED", "FAILED"], [valid_c, invalid_c], color=["green", "red"])
    plt.title("Global Validation Results")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "validation_results.png"))
    plt.close()
    
    # 7. Event Type Runtime
    event_types = list(set([r["event_type"] for r in reader]))
    avg_times = []
    for et in event_types:
        times = [float(r["adaptive_runtime_ms"]) for r in reader if r["event_type"] == et]
        avg_times.append(sum(times) / len(times))
        
    plt.figure(figsize=(10, 6))
    plt.bar(event_types, avg_times, color="purple")
    plt.xlabel("Event Type")
    plt.ylabel("Avg Adaptive Runtime (ms)")
    plt.title("Average Runtime by Event Type")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "event_type_runtime.png"))
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    plot_results(args.input, args.output)
