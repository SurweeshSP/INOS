import os
import json
from datetime import datetime
from src.datasets.qplib import QplibLoader
from src.solver.qp import solve_qp

class QplibRunner:
    def __init__(self, data_dir: str = "data/qplib", results_dir: str = "results/qplib"):
        self.loader = QplibLoader(data_dir=data_dir)
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)

    def run_benchmark(self, instances: list[str]):
        results = {}
        for instance in instances:
            print(f"Loading {instance}...")
            
            # This generates the embedded fallback dataset if network download fails
            self.loader.download_subset([instance])
            
            model = self.loader.load_instance(instance)
            print(f"Solving {instance}...")
            
            try:
                res = solve_qp(model)
                
                # Verify KKT constraints
                # Primal residual = || max(0, Ax - b) || for inequalities, || Ax - b || for equalities
                primal_res = 0.0
                if model.A is not None and len(model.A) > 0:
                    for i in range(len(model.A)):
                        val = sum(model.A[i, j] * res.primal_values[v] for j, v in enumerate(model.variables.keys()))
                        if model.senses[i] == 'E':
                            primal_res += abs(val - model.b[i])
                        elif model.senses[i] == 'L':
                            primal_res += max(0, val - model.b[i])
                        elif model.senses[i] == 'G':
                            primal_res += max(0, model.b[i] - val)
                            
                res.constraint_residual = primal_res
                
                result_dict = {
                    "instance": instance,
                    "status": res.status.name,
                    "objective": res.objective_value,
                    "runtime": res.runtime,
                    "iterations": res.iterations,
                    "constraint_residual": res.constraint_residual
                }
            except Exception as e:
                print(f"Error solving {instance}: {e}")
                result_dict = {
                    "instance": instance,
                    "status": "ERROR",
                    "error_message": str(e)
                }

            results[instance] = result_dict
            
            # Save certificate
            cert_path = os.path.join(self.results_dir, f"{instance}_certificate.json")
            with open(cert_path, 'w') as f:
                json.dump(result_dict, f, indent=4)
                
            print(f"Result for {instance}: {result_dict['status']} obj: {result_dict.get('objective', 'N/A')}")
            
        summary_path = os.path.join(self.results_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=4)
            
        return results
