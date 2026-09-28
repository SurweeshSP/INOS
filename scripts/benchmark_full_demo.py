import os
import time
from src.api.v2_schemas import BusinessProblemInput
from src.domain.problem_builder import SupplyChainProblemBuilder
from src.execution_backend import execution_backend

def run_benchmark():
    os.makedirs('reports', exist_ok=True)
    report_lines = [
        "# SupplyChainOptii Full Demo Performance Benchmark",
        "",
        "## Configuration",
        "- Execution Mode: FULL",
        "- Hardware: GPU / CPU Fallback",
        "",
        "## Results",
        "| Phase | Time (s) | Entities / Variables |",
        "|-------|----------|----------------------|",
    ]
    
    print("Building model...")
    t0 = time.time()
    problem = BusinessProblemInput(execution_mode="full", planning_horizon=1, goal="Minimize Cost", entities=[])
    model, var_map = SupplyChainProblemBuilder.build(problem)
    t_build = time.time() - t0
    
    nodes = sum(1 for v in model.variables)
    edges = sum(1 for c in model.constraints)
    
    report_lines.append(f"| Model Construction & Ingestion | {t_build:.4f} | {len(model.variables)} vars, {len(model.constraints)} constraints |")
    
    # 2. Execution Backend estimation
    print("Estimating memory...")
    t1 = time.time()
    bytes_req = execution_backend._estimate_memory_required(model)
    mb = bytes_req / (1024 * 1024)
    can_gpu = execution_backend._can_run_on_gpu(bytes_req)
    t_est = time.time() - t1
    
    report_lines.append(f"| Backend Selection & Estimation | {t_est:.4f} | Memory required: {mb:.2f} MB. GPU Executable: {can_gpu} |")
    
    # 3. Solve (Auto)
    print("Solving model...")
    t2 = time.time()
    solution = execution_backend.solve_auto(model)
    t_solve = time.time() - t2
    
    report_lines.append(f"| Solver Execution (AUTO) | {t_solve:.4f} | Status: {solution.status.name} |")
    report_lines.append("")
    report_lines.append(f"**Total End-to-End Time:** {t_build + t_est + t_solve:.4f} seconds")
    report_lines.append("")
    report_lines.append(f"Objective Value: {solution.objective_value}")
    
    with open('reports/FULL_DEMO_MODEL_PERFORMANCE.md', 'w') as f:
        f.write("\n".join(report_lines))
        
    print("Benchmark complete. Wrote to reports/FULL_DEMO_MODEL_PERFORMANCE.md")

if __name__ == "__main__":
    run_benchmark()
