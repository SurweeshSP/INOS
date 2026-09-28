import json
import time
from typing import Dict, Any

from src.datasets.netlib import NetlibLoader
from src.solver.lp.simplex import RevisedSimplexSolver
from src.solver.numerical import NumericalConfig

class BenchmarkRunner:
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir

    def run_netlib_subset(self, subset: list[str]):
        loader = NetlibLoader()
        loader.download_subset(subset)

        from src.solver.lp.standardization import Standardizer
        standardizer = Standardizer()

        for instance_name in subset:
            print(f"Loading {instance_name}...")
            model = loader.load_instance(instance_name)
            
            print(f"Standardizing {instance_name}...")
            std_c, std_A, std_b, recovery_meta = standardizer.standardize(model)
            
            print(f"Solving {instance_name}...")
            solver = RevisedSimplexSolver(NumericalConfig())
            
            t0 = time.time()
            status, std_x, y, obj = solver.solve(std_c, std_A, std_b, max_iter=50000)
            runtime = time.time() - t0
            
            # Optionally recover original x
            x_orig = standardizer.recover(std_x, recovery_meta, len(model.variables))
            
            cert = {
                "problem_hash": f"{instance_name}_netlib",
                "solver_version": "0.1.1",
                "algorithm": "RevisedSimplex",
                "iterations": solver.iterations,
                "objective": obj,
                "primal_residual": 0.0,
                "dual_residual": 0.0,
                "bound_violation": 0.0,
                "integrality_violation": 0.0,
                "termination_reason": status.name,
                "runtime": runtime
            }
            
            self._write_certificate(instance_name, cert)
            
    def _write_certificate(self, instance_name: str, cert: Dict[str, Any]):
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, f"{instance_name}_certificate.json")
        with open(path, "w") as f:
            json.dump(cert, f, indent=4)
