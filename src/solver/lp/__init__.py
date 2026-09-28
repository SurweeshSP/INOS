import time
from typing import Any, Dict, Optional
from src.data_models import OptimizationModel, SolutionRecord, SolveStatus, ProblemType
from src.solver.lp.standardization import Standardizer
from src.solver.lp.simplex import RevisedSimplexSolver

def solve_lp(model: OptimizationModel, method: str = 'scipy', options: Optional[Dict[str, Any]] = None, state: Optional[Any] = None) -> SolutionRecord:
    if model.problem_type != ProblemType.LP and model.problem_type != ProblemType.MILP:
        pass # MILP passes LP relaxation here
        
    start_time = time.time()
    
    from src.trust.model_validator import ModelValidator
    val_res = ModelValidator.validate(model)
    if not val_res.valid:
        return SolutionRecord(
            status=SolveStatus.ERROR,
            runtime=time.time() - start_time,
            objective_value=None
        )
    
    if method == 'scipy':
        import scipy.sparse as sp
        from scipy.optimize import linprog
        import numpy as np

        # model.A is csr_matrix, model.b is array, model.senses is list of 'E', 'L', 'G'
        if sp.issparse(model.c):
            c = np.array(model.c.todense()).flatten()
        else:
            c = np.array(model.c).flatten()
            
        if len(c) == 0:
            return SolutionRecord(
                status=SolveStatus.OPTIMAL,
                objective_value=0.0,
                variables=np.array([])
            )
            
        b = model.b
        lb = model.lower_bounds if model.lower_bounds is not None else [0.0] * len(c)
        ub = model.upper_bounds if model.upper_bounds is not None else [np.inf] * len(c)
        
        # Scipy linprog bounds
        bounds = [(l, u if u != np.inf else None) for l, u in zip(lb, ub)]

        A_eq_rows, A_eq_cols, A_eq_data = [], [], []
        b_eq = []
        A_ub_rows, A_ub_cols, A_ub_data = [], [], []
        b_ub = []

        A_csr = model.A.tocsr() if sp.issparse(model.A) else sp.csr_matrix(model.A)

        eq_idx = 0
        ub_idx = 0
        senses = model.senses if model.senses is not None else ['E'] * len(b)
        for i, sense in enumerate(senses):
            row = A_csr.getrow(i)
            if sense == 'E':
                A_eq_rows.extend([eq_idx] * len(row.indices))
                A_eq_cols.extend(row.indices)
                A_eq_data.extend(row.data)
                b_eq.append(b[i])
                eq_idx += 1
            elif sense == 'L':
                A_ub_rows.extend([ub_idx] * len(row.indices))
                A_ub_cols.extend(row.indices)
                A_ub_data.extend(row.data)
                b_ub.append(b[i])
                ub_idx += 1
            elif sense == 'G':
                A_ub_rows.extend([ub_idx] * len(row.indices))
                A_ub_cols.extend(row.indices)
                A_ub_data.extend(-row.data)  # Multiply by -1 for G to L
                b_ub.append(-b[i])
                ub_idx += 1

        A_eq = sp.csr_matrix((A_eq_data, (A_eq_rows, A_eq_cols)), shape=(len(b_eq), len(c))) if b_eq else None
        A_ub = sp.csr_matrix((A_ub_data, (A_ub_rows, A_ub_cols)), shape=(len(b_ub), len(c))) if b_ub else None

        print(f"DEBUG: c type={type(c)}, c ndim={c.ndim}, shape={c.shape}, c={c}")
        res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

        status = SolveStatus.OPTIMAL if res.success else SolveStatus.INFEASIBLE
        
        if res.success:
            orig_x = res.x
            canonical_obj = res.fun
            if hasattr(model, 'objective_offset'):
                canonical_obj -= model.objective_offset
                
            if model.variables:
                primal_vals = {v: orig_x[i] for i, v in enumerate(model.variables.keys())}
            else:
                primal_vals = {f"v{i}": orig_x[i] for i in range(len(orig_x))}
        else:
            orig_x = None
            primal_vals = {}
            canonical_obj = None

        return SolutionRecord(
            status=status,
            objective_value=canonical_obj,
            primal_values=primal_vals,
            variables=orig_x,
            runtime=time.time() - start_time,
            iterations=res.nit
        )
    else:
        standardizer = Standardizer()
        std_lp = standardizer.standardize(model)
        std_c, std_A, std_b, recovery_meta = standardizer.to_simplex_standard_form(std_lp)
        
        solver = RevisedSimplexSolver()
        status, x_final, y, obj_val = solver.solve(std_c, std_A, std_b)
        
        if status == SolveStatus.OPTIMAL or status == SolveStatus.SUBOPTIMAL:
            n_vars = len(model.c) if model.c is not None else len(model.variables)
            orig_x = standardizer.recover(x_final, recovery_meta, n_vars)
            if model.variables:
                primal_vals = {v: orig_x[i] for i, v in enumerate(model.variables.keys())}
            else:
                primal_vals = {f"v{i}": orig_x[i] for i in range(len(orig_x))}
                
            canonical_obj = float(model.c @ orig_x)
            if hasattr(model, 'objective_offset'):
                canonical_obj -= model.objective_offset
        else:
            orig_x = None
            primal_vals = {}
            canonical_obj = None
            
        return SolutionRecord(
            status=status,
            objective_value=canonical_obj,
            primal_values=primal_vals,
            variables=orig_x,
            runtime=time.time() - start_time,
            iterations=solver.iterations
        )
