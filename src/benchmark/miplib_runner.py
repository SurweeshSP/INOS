import json
import time
import os
from typing import Dict, Any

from src.datasets.miplib import MiplibLoader
from src.solver.milp.branch_and_bound import BranchAndBoundSolver
from src.solver.numerical import NumericalConfig

class MiplibRunner:
    def __init__(self, output_dir: str = "results/miplib"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_miplib_subset(self, subset: list[str]):
        loader = MiplibLoader()
        loader.download_subset(subset)

        for instance_name in subset:
            print(f"Loading {instance_name}...")
            model = loader.load_instance(instance_name)
            
            print(f"Solving {instance_name} with Branch-and-Bound...")
            solver = BranchAndBoundSolver(NumericalConfig())
            
            t0 = time.time()
            solution = solver.solve(model, time_limit=3600.0, node_limit=10000)
            runtime = time.time() - t0
            
            int_vars = sum(1 for v in model.variables.values() if v.var_type.name in ('INTEGER', 'BINARY'))
            cont_vars = len(model.variables) - int_vars
            
            cert = {
                "instance": instance_name,
                "variables": len(model.variables),
                "constraints": len(model.constraints),
                "integer_variables": int_vars,
                "continuous_variables": cont_vars,
                "status": solution.status.name,
                "objective": solution.objective_value,
                "nodes_processed": solver.nodes_processed,
                "lp_relaxations": solver.lp_relaxations,
                "nodes_pruned": solver.nodes_pruned,
                "runtime": runtime,
                "solver_version": "0.2.0 (Phase 7)"
            }
            
            self._write_certificate(instance_name, cert)
            print(f"Completed {instance_name}: Status={solution.status.name}, Obj={solution.objective_value}, Nodes={solver.nodes_processed}, Time={runtime:.2f}s")
            
    def _write_certificate(self, instance_name: str, cert: Dict[str, Any]):
        path = os.path.join(self.output_dir, f"{instance_name}_certificate.json")
        with open(path, "w") as f:
            json.dump(cert, f, indent=4)
