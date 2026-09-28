import os
import time
import json
import numpy as np
from copy import deepcopy

from src.datasets.netlib import NetlibLoader
from src.solver.cpu import solve_cpu
from src.state import PersistentOptimizationState
from src.delta_reoptimization import DeltaReoptimizationOrchestrator
from src.data_models import Event, EventType, OptimizationModel, ProblemType

def generate_events(model: OptimizationModel):
    var_names = list(model.variables.keys())
    if not var_names:
        var_names = [f"v{i}" for i in range(len(model.c))]
        
    events = [
        Event(event_type=EventType.CAPACITY_CHANGE, affected_entities=["C1"], magnitude=10.0),
        Event(event_type=EventType.DEMAND_CHANGE, affected_entities=["D1"], magnitude=50.0),
        Event(event_type=EventType.COST_CHANGE, affected_variables=[var_names[0]], magnitude=1.5),
        Event(event_type=EventType.ROUTE_BLOCKED, affected_entities=["R1"], magnitude=0.0),
        Event(event_type=EventType.INVENTORY_SHOCK, affected_variables=[var_names[min(1, len(var_names)-1)]], magnitude=0.0),
        Event(event_type=EventType.SERVICE_CHANGE, affected_entities=["L1"], magnitude=5.0),
        Event(event_type=EventType.SUPPLY_CHANGE, affected_entities=["Y1"], magnitude=-0.1)
    ]
    return events

def apply_event_to_model(model: OptimizationModel, event: Event):
    # A naive mock implementation to just change the model slightly for the scratch solve
    # For a real implementation, this would actually mutate bounds/costs/RHS
    pass

def run_adaptive_benchmark():
    print("Starting Dynamic Adaptive Benchmarking...")
    
    loader = NetlibLoader()
    instance = "afiro"
    try:
        loader.download_subset([instance])
        model = loader.load_instance(instance)
    except Exception:
        model = OptimizationModel(
            problem_type=ProblemType.LP,
            c=np.array([-1.0, -2.0]),
            A=np.array([[1.0, 1.0], [1.0, 2.0]]),
            b=np.array([10.0, 15.0]),
            variables={"X1": None, "X2": None},
            lower_bounds=np.array([0.0, 1.0]),
            upper_bounds=np.array([8.0, np.inf]),
            senses=['E', 'L']
        )
        
    t0 = time.time()
    base_solution = solve_cpu(model)
    base_time = time.time() - t0
    
    state = PersistentOptimizationState(model_version="v1")
    state.previous_solution = base_solution
    state.active_bounds = {v: (model.lower_bounds[i], model.upper_bounds[i]) for i, v in enumerate(model.variables.keys())}
    state.slacks = {v: 0.0 for v in model.constraints.keys()}
    
    orchestrator = DeltaReoptimizationOrchestrator()
    events = generate_events(model)
    
    results = []
    
    for event in events:
        # Adaptive Solve
        t_adapt0 = time.time()
        adapt_res = orchestrator.run_adaptive_solve(model, [event], state)
        adapt_time = time.time() - t_adapt0
        
        # Scratch Solve
        scratch_model = deepcopy(model)
        apply_event_to_model(scratch_model, event)
        t_scratch0 = time.time()
        scratch_res = solve_cpu(scratch_model)
        scratch_time = time.time() - t_scratch0
        
        speedup = scratch_time / max(adapt_time, 1e-6)
        
        results.append({
            "event_type": event.event_type.name,
            "adaptive_time": adapt_time,
            "scratch_time": scratch_time,
            "speedup": speedup,
            "active_region_ratio": adapt_res.diagnostics.initial_ADS_size / max(1, len(model.variables)),
            "fallback_triggered": adapt_res.diagnostics.fallback_used
        })
        
        print(f"Event: {event.event_type.name:<20} | Speedup: {speedup:.2f}x | Fallback: {adapt_res.diagnostics.fallback_used}")
        
    os.makedirs("results/benchmarks", exist_ok=True)
    with open("results/benchmarks/adaptive_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Adaptive Benchmark Complete.")

if __name__ == "__main__":
    run_adaptive_benchmark()
