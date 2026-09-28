import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import load_instance
from src.optimizer import SupplyChainOptimizer
from src.trust.model_validator import ModelValidator, ModelValidationStatus
from src.trust.independent_validator import IndependentValidator
from src.data_models import VariableType

REPRESENTATIVE_FILES = {
    "MIPLIB": [
        "data/miplib/app1-2.mps.gz",
        "data/miplib/50v-10.mps.gz"
    ],
    "NETLIB": [
        "data/netlib/afiro.mps",
        "data/netlib/adlittle.mps"
    ],
    "QPLIB": [
        "data/qplib/TEST_QP.qps",
        "data/qplib/qplib/html/lp/QPLIB_0018.lp"
    ]
}

SUPPLY_CHAIN_FILES = [
    "data/supply_chain/cotton_baseline.yaml",
    "data/supply_chain/coal_supply_chain.yaml"
]

def analyze_model(model):
    num_vars = len(model.variables) if model.variables else 0
    num_cons = len(model.constraints) if model.constraints else 0
    
    int_vars = sum(1 for v in model.variables.values() if v.var_type == VariableType.INTEGER) if model.variables else 0
    bin_vars = sum(1 for v in model.variables.values() if v.var_type == VariableType.BINARY) if model.variables else 0
    
    if model.A is not None:
        nonzeros = model.A.nnz if hasattr(model.A, 'nnz') else np.count_nonzero(model.A)
    else:
        nonzeros = 0
        
    if model.Q is not None:
        quad_terms = model.Q.nnz if hasattr(model.Q, 'nnz') else np.count_nonzero(model.Q)
    else:
        quad_terms = 0
    
    return num_vars, num_cons, nonzeros, int_vars, bin_vars, quad_terms

def run_instance(dataset, filepath, optimizer, indep_val):
    print(f"Testing {dataset} - {filepath}")
    
    start_parse = time.time()
    try:
        if not os.path.exists(filepath):
            return {"dataset": dataset, "instance": Path(filepath).name, "status": "PARSE_FAILURE", "reason": f"File not found: {filepath}"}
            
        if filepath.endswith('.yaml'):
            import yaml
            from src.domain.schema import GenericSupplyChainModel, Supply, Demand, Route, Processing, Inventory
            from src.domain.compiler import MathematicalCompiler
            with open(filepath, 'r') as f:
                data = yaml.safe_load(f)
                
            data['supply'] = [Supply(**s) for s in data.get('supply', [])]
            data['demand'] = [Demand(**d) for d in data.get('demand', [])]
            data['routes'] = [Route(**r) for r in data.get('routes', [])]
            
            if 'processing' in data:
                data['processing'] = {k: Processing(**v) for k, v in data['processing'].items()}
            if 'inventory' in data:
                data['inventory'] = {k: Inventory(**v) for k, v in data['inventory'].items()}
                
            domain_model = GenericSupplyChainModel(**data)
            compiler = MathematicalCompiler()
            model = compiler.compile(domain_model)
        else:
            model = load_instance(filepath)
            
        parse_status = "PARSED"
    except Exception as e:
        return {"dataset": dataset, "instance": Path(filepath).name, "status": "PARSE_FAILURE", "reason": str(e)}
    parse_time = time.time() - start_parse
    
    # Model Validation
    val_status, val_msg = ModelValidator.validate(model)
    if val_status == ModelValidationStatus.INVALID:
        return {"dataset": dataset, "instance": Path(filepath).name, "status": "MODEL_FAILURE", "reason": val_msg}
        
    num_vars, num_cons, nonzeros, int_vars, bin_vars, quad_terms = analyze_model(model)
    
    # Solve
    start_solve = time.time()
    try:
        from src.solver.cpu import solve_cpu
        res = solve_cpu(model, options={'time_limit': 10, 'max_iter': 100})
        solve_time = time.time() - start_solve
        status_str = getattr(res.status, 'name', str(res.status))
    except Exception as e:
        return {"dataset": dataset, "instance": Path(filepath).name, "status": "SOLVER_ERROR", "reason": str(e)}
        
    if status_str not in ["OPTIMAL", "FEASIBLE"]:
        return {"dataset": dataset, "instance": Path(filepath).name, "status": status_str, "reason": "Not solved optimally/feasibly"}
        
    # Independent Validation
    start_val = time.time()
    x = np.array([res.primal_values.get(name, 0.0) for name in model.variables.keys()])
    indep_res = indep_val.validate(model, x)
    val_time = time.time() - start_val
    
    status = "SOLVED_OPTIMAL" if indep_res.is_valid else "VALIDATION_FAILURE"
    
    result = {
        "dataset": dataset,
        "instance": Path(filepath).name,
        "status": status,
        "parse_time": parse_time,
        "solve_time": solve_time,
        "val_time": val_time,
        "num_vars": num_vars,
        "num_cons": num_cons,
        "nonzeros": nonzeros,
        "int_vars": int_vars,
        "bin_vars": bin_vars,
        "quad_terms": quad_terms,
        "obj_recomputed": indep_res.objective_recomputed,
        "obj_solver": res.objective_value,
        "primal_residual": indep_res.primal_residual,
        "bound_violation": indep_res.bound_violation,
        "integrality_violation": indep_res.integrality_violation,
        "kkt_stationarity": indep_res.kkt_stationarity
    }
    
    # Save JSON telemetry
    os.makedirs("results/real/validation", exist_ok=True)
    with open(f"results/real/validation/{Path(filepath).name}_result.json", "w") as f:
        json.dump(result, f, indent=4)
        
    return result

def main():
    import numpy as np # import inside for script independence
    globals()['np'] = np
    
    optimizer = SupplyChainOptimizer()
    indep_val = IndependentValidator()
    
    results = []
    
    for dataset, files in REPRESENTATIVE_FILES.items():
        for file in files:
            res = run_instance(dataset, file, optimizer, indep_val)
            results.append(res)
            
    for file in SUPPLY_CHAIN_FILES:
        res = run_instance("SUPPLY_CHAIN", file, optimizer, indep_val)
        results.append(res)
        
    # Generate Reports
    os.makedirs("reports", exist_ok=True)
    
    with open("reports/REPRESENTATIVE_REAL_DATA_RESULTS.md", "w") as f:
        f.write("# Representative Real Data Results\n\n")
        f.write("| Dataset | Instance | Vars | Cons | Status | Primal Res | Obj (Recomputed) |\n")
        f.write("|---------|----------|------|------|--------|------------|-----------------|\n")
        
        for r in results:
            if "reason" in r:
                f.write(f"| {r['dataset']} | {r['instance']} | - | - | {r['status']} ({r['reason']}) | - | - |\n")
            else:
                p_res = f"{r['primal_residual']:.2e}" if r['primal_residual'] is not None else "N/A"
                obj = f"{r['obj_recomputed']:.4f}" if r['obj_recomputed'] is not None else "N/A"
                f.write(f"| {r['dataset']} | {r['instance']} | {r['num_vars']} | {r['num_cons']} | {r['status']} | {p_res} | {obj} |\n")
                
    print("Representative testing complete. Reports generated.")

if __name__ == "__main__":
    main()
