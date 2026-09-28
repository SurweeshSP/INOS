import numpy as np
from typing import Dict, Optional, Any, Tuple, List
import time

from src.data_models import OptimizationModel, SolutionRecord, SolveStatus, ProblemType
from src.solver.numerical import NumericalConfig

class ActiveSetQPSolver:
    """
    Primal Active-Set Solver for Convex Quadratic Programming.
    Solves:
        min 1/2 x^T Q x + c^T x
        s.t. A x <= b
             x_lb <= x <= x_ub
             
    Since the equality constraints and inequalities are standardized in our system,
    we handle the equality/inequality bounds appropriately.
    """
    def __init__(self, config: Optional[NumericalConfig] = None):
        self.config = config or NumericalConfig()
        
    def solve(self, model: OptimizationModel, max_iter: int = 1000) -> SolutionRecord:
        start_time = time.time()
        
        if model.c is None or len(model.variables) == 0:
            return SolutionRecord(status=SolveStatus.NOT_SOLVED)
            
        if model.Q is None:
            model.Q = np.zeros((len(model.c), len(model.c)))
            
        n = len(model.c)
        m = 0 if model.A is None else model.A.shape[0]
        
        Q = np.array(model.Q.toarray() if hasattr(model.Q, 'toarray') else model.Q)
        c = np.array(model.c)
        if model.A is not None:
            A = np.array(model.A.toarray() if hasattr(model.A, 'toarray') else model.A)
        else:
            A = np.zeros((0, n))
        b = np.array(model.b) if model.b is not None else np.zeros(0)
        
        senses = model.senses if hasattr(model, 'senses') and model.senses else ['L'] * m
        
        A_ineq = []
        b_ineq = []
        A_eq = []
        b_eq = []
        
        for i in range(m):
            if senses[i] == 'E':
                A_eq.append(A[i])
                b_eq.append(b[i])
            elif senses[i] == 'L':
                A_ineq.append(A[i])
                b_ineq.append(b[i])
            elif senses[i] == 'G':
                A_ineq.append(-A[i])
                b_ineq.append(-b[i])
                
        # We need a feasible point x0
        import scipy.optimize as sopt
        
        bounds_scipy = []
        for j in range(n):
            lb = model.lower_bounds[j] if hasattr(model, 'lower_bounds') and model.lower_bounds is not None else 0.0
            ub = model.upper_bounds[j] if hasattr(model, 'upper_bounds') and model.upper_bounds is not None else float('inf')
            bounds_scipy.append((lb if lb > -float('inf') else None, ub if ub < float('inf') else None))
            
        res_phase1 = sopt.linprog(c=np.zeros(n), A_ub=A_ineq if A_ineq else None, b_ub=b_ineq if b_ineq else None, A_eq=A_eq if A_eq else None, b_eq=b_eq if b_eq else None, bounds=bounds_scipy, method='highs')
        
        if not res_phase1.success:
            return SolutionRecord(status=SolveStatus.INFEASIBLE)
            
        x = res_phase1.x
        
        # Add bounds explicitly to inequality list for active set tracking
        for j in range(n):
            lb = model.lower_bounds[j] if hasattr(model, 'lower_bounds') and model.lower_bounds is not None else 0.0
            ub = model.upper_bounds[j] if hasattr(model, 'upper_bounds') and model.upper_bounds is not None else float('inf')
            if lb > -float('inf'):
                row = np.zeros(n)
                row[j] = -1.0
                A_ineq.append(row)
                b_ineq.append(-lb)
            if ub < float('inf'):
                row = np.zeros(n)
                row[j] = 1.0
                A_ineq.append(row)
                b_ineq.append(ub)
                
        A_ineq = np.array(A_ineq) if A_ineq else np.zeros((0, n))
        b_ineq = np.array(b_ineq) if b_ineq else np.zeros(0)
        A_eq = np.array(A_eq) if A_eq else np.zeros((0, n))
        b_eq = np.array(b_eq) if b_eq else np.zeros(0)
        
        m_eq = A_eq.shape[0]
        m_in = A_ineq.shape[0]
        
        # Determine initial active set (inequalities that are tight)
        active_set = []
        for i in range(m_in):
            if abs(A_ineq[i] @ x - b_ineq[i]) < 1e-7:
                active_set.append(i)
        
        iterations = 0
        status = SolveStatus.NOT_SOLVED
        
        while iterations < max_iter:
            iterations += 1
            
            # Form working set matrix W
            if len(active_set) > 0:
                W = np.vstack([A_eq, A_ineq[active_set]]) if m_eq > 0 else A_ineq[active_set]
            else:
                W = A_eq
                
            m_w = W.shape[0]
            
            # Solve KKT system for step p:
            # [ Q   W^T ] [ p ] = [ -g ]
            # [ W    0  ] [ y ]   [ 0 ]
            # where g = Qx + c
            
            g = Q @ x + c
            
            KKT = np.zeros((n + m_w, n + m_w))
            KKT[:n, :n] = Q
            if m_w > 0:
                KKT[:n, n:] = W.T
                KKT[n:, :n] = W
                
            rhs = np.zeros(n + m_w)
            rhs[:n] = -g
            
            # If KKT is singular (e.g. Q not strictly convex or linearly dependent constraints),
            # we need a regularization or pseudo-inverse
            try:
                sol = np.linalg.solve(KKT, rhs)
            except np.linalg.LinAlgError:
                # Regularize
                KKT[:n, :n] += np.eye(n) * 1e-8
                if m_w > 0:
                    KKT[n:, n:] -= np.eye(m_w) * 1e-8
                try:
                    sol = np.linalg.solve(KKT, rhs)
                except np.linalg.LinAlgError:
                    status = SolveStatus.ERROR
                    break
            
            p = sol[:n]
            y = sol[n:]
            
            if np.linalg.norm(p) < 1e-8:
                # p is zero, we are optimal on the current subspace
                # Check Lagrange multipliers for inequalities
                if len(active_set) == 0:
                    status = SolveStatus.OPTIMAL
                    break
                    
                # y contains multipliers for equalities and inequalities.
                # Inequalities are the last len(active_set) elements.
                y_ineq = y[m_eq:]
                
                if np.all(y_ineq >= -1e-8):
                    # All multipliers non-negative -> Optimal
                    status = SolveStatus.OPTIMAL
                    break
                else:
                    # Drop constraint with most negative multiplier
                    drop_idx = np.argmin(y_ineq)
                    active_set.pop(drop_idx)
                    continue
                    
            # Compute step length alpha
            alpha = 1.0
            blocking_idx = -1
            
            if m_in > 0:
                # Find inactive constraints
                inactive_set = [i for i in range(m_in) if i not in active_set]
                
                for i in inactive_set:
                    denom = A_ineq[i] @ p
                    if denom > 1e-8:
                        # Constraint could be violated
                        dist = (b_ineq[i] - A_ineq[i] @ x) / denom
                        if dist < alpha:
                            alpha = dist
                            blocking_idx = i
                            
            x = x + alpha * p
            
            if alpha < 1.0 and blocking_idx != -1:
                active_set.append(blocking_idx)
                
        if status == SolveStatus.NOT_SOLVED:
            status = SolveStatus.SUBOPTIMAL
            
        obj_val = float(0.5 * x.T @ Q @ x + c.T @ x)
        if hasattr(model, 'objective_offset'):
            obj_val -= model.objective_offset
        
        primal_vals = {}
        col_names = list(model.variables.keys())
        for i, name in enumerate(col_names):
            primal_vals[name] = x[i]
            
        return SolutionRecord(
            status=status,
            objective_value=obj_val,
            primal_values=primal_vals,
            variables=x,
            iterations=iterations,
            runtime=time.time() - start_time
        )
