import numpy as np
import scipy.sparse as sp
from typing import Tuple, List, Dict, Any
from dataclasses import dataclass, field
from src.data_models import OptimizationModel

@dataclass
class StandardizedLP:
    A_eq: np.ndarray
    b_eq: np.ndarray
    A_ub: np.ndarray
    b_ub: np.ndarray
    c: np.ndarray
    lower_bounds: np.ndarray
    upper_bounds: np.ndarray
    variable_mapping: Dict[int, Any] = field(default_factory=dict)
    constraint_mapping: Dict[int, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class Standardizer:
    """
    Converts a general LP model into a standard mathematical form,
    separating equalities and inequalities, and preserving bounds.
    """
    
    def standardize(self, model: OptimizationModel) -> StandardizedLP:
        A = model.A
        if A is None:
            n = len(model.c) if model.c is not None else 0
            A = sp.csr_matrix((0, n))
            
        if sp.issparse(A):
            A = A.toarray()
            
        m, n = A.shape
        b = model.b if model.b is not None else np.zeros(m)
        c = model.c if model.c is not None else np.zeros(n)
        
        senses = model.senses if getattr(model, 'senses', None) is not None else ['E'] * m
        
        eq_rows, ub_rows = [], []
        eq_rhs, ub_rhs = [], []
        constraint_mapping = {}
        
        eq_idx = 0
        ub_idx = 0
        for i in range(m):
            sense = senses[i]
            if sense == 'E':
                eq_rows.append(A[i])
                eq_rhs.append(b[i])
                constraint_mapping[i] = ('E', eq_idx)
                eq_idx += 1
            elif sense == 'L':
                ub_rows.append(A[i])
                ub_rhs.append(b[i])
                constraint_mapping[i] = ('L', ub_idx)
                ub_idx += 1
            elif sense == 'G':
                ub_rows.append(-A[i])
                ub_rhs.append(-b[i])
                constraint_mapping[i] = ('G', ub_idx)
                ub_idx += 1
                
        A_eq = np.vstack(eq_rows) if eq_rows else np.empty((0, n))
        b_eq = np.array(eq_rhs) if eq_rhs else np.empty(0)
        A_ub = np.vstack(ub_rows) if ub_rows else np.empty((0, n))
        b_ub = np.array(ub_rhs) if ub_rhs else np.empty(0)
        
        lb = model.lower_bounds if model.lower_bounds is not None else np.zeros(n)
        ub = model.upper_bounds if model.upper_bounds is not None else np.full(n, np.inf)
        
        var_mapping = {j: j for j in range(n)}
        
        return StandardizedLP(
            A_eq=A_eq, b_eq=b_eq,
            A_ub=A_ub, b_ub=b_ub,
            c=c.copy(),
            lower_bounds=lb.copy(),
            upper_bounds=ub.copy(),
            variable_mapping=var_mapping,
            constraint_mapping=constraint_mapping,
            metadata={}
        )
        
    def to_simplex_standard_form(self, std_lp: StandardizedLP) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict]:
        """
        Converts StandardizedLP into pure Ax=b, x>=0 form for the Revised Simplex Solver.
        """
        n_orig = len(std_lp.c)
        m_eq = len(std_lp.b_eq)
        m_ub = len(std_lp.b_ub)
        
        new_A_cols = []
        new_c_list = []
        recovery_meta = {'var_mapping': {}, 'shifts': {}}
        current_std_idx = 0
        
        # 1. Variables: Free, Bounds, Shifts
        b_shift_eq = np.zeros(m_eq)
        b_shift_ub = np.zeros(m_ub)
        
        for j in range(n_orig):
            lb = std_lp.lower_bounds[j]
            ub = std_lp.upper_bounds[j]
            
            col_eq = std_lp.A_eq[:, j] if m_eq > 0 else np.zeros(0)
            col_ub = std_lp.A_ub[:, j] if m_ub > 0 else np.zeros(0)
            obj_val = std_lp.c[j]
            
            if lb == -np.inf and ub == np.inf: # FR
                new_A_cols.append((col_eq, col_ub))
                new_A_cols.append((-col_eq, -col_ub))
                new_c_list.extend([obj_val, -obj_val])
                recovery_meta['var_mapping'][j] = ('split', current_std_idx, current_std_idx + 1)
                current_std_idx += 2
            else:
                shift = 0.0
                if lb != -np.inf and lb != 0.0:
                    shift = lb
                    if m_eq > 0: b_shift_eq += col_eq * shift
                    if m_ub > 0: b_shift_ub += col_ub * shift
                    
                new_A_cols.append((col_eq, col_ub))
                new_c_list.append(obj_val)
                recovery_meta['var_mapping'][j] = ('std', current_std_idx)
                recovery_meta['shifts'][j] = shift
                current_std_idx += 1
                
        # 2. Build shifted A and b
        if new_A_cols:
            A_eq_shifted = np.column_stack([c[0] for c in new_A_cols]) if m_eq > 0 else np.empty((0, current_std_idx))
            A_ub_shifted = np.column_stack([c[1] for c in new_A_cols]) if m_ub > 0 else np.empty((0, current_std_idx))
        else:
            A_eq_shifted = np.empty((m_eq, 0))
            A_ub_shifted = np.empty((m_ub, 0))
            
        std_c = np.array(new_c_list)
        std_b_eq = std_lp.b_eq - b_shift_eq
        std_b_ub = std_lp.b_ub - b_shift_ub
        
        # 3. Add slacks for inequalities
        if m_ub > 0:
            slack_eq = np.zeros((m_eq, m_ub))
            slack_ub = np.eye(m_ub)
            
            A_eq_full = np.hstack([A_eq_shifted, slack_eq]) if m_eq > 0 else np.empty((0, current_std_idx + m_ub))
            A_ub_full = np.hstack([A_ub_shifted, slack_ub])
            std_c = np.concatenate([std_c, np.zeros(m_ub)])
        else:
            A_eq_full = A_eq_shifted
            A_ub_full = np.empty((0, current_std_idx))
            
        # Combine EQ and UB into one system
        std_A = np.vstack([A_eq_full, A_ub_full]) if m_ub > 0 or m_eq > 0 else np.empty((0, len(std_c)))
        std_b = np.concatenate([std_b_eq, std_b_ub]) if m_ub > 0 or m_eq > 0 else np.empty(0)
        
        # Handle upper bounds as constraints
        ub_rows = []
        ub_rhs = []
        n_current = std_A.shape[1]
        
        for j in range(n_orig):
            lb = std_lp.lower_bounds[j]
            ub = std_lp.upper_bounds[j]
            
            if ub != np.inf:
                shift = recovery_meta['shifts'].get(j, 0.0)
                eff_ub = ub - shift
                if eff_ub <= 0:
                    eff_ub = 0 # if lb == ub
                row = np.zeros(n_current)
                map_type = recovery_meta['var_mapping'][j][0]
                if map_type == 'std':
                    row[recovery_meta['var_mapping'][j][1]] = 1.0
                elif map_type == 'split':
                    row[recovery_meta['var_mapping'][j][1]] = 1.0
                    row[recovery_meta['var_mapping'][j][2]] = -1.0
                    
                ub_rows.append(row)
                ub_rhs.append(eff_ub)
                
        if ub_rows:
            num_ub = len(ub_rows)
            ub_A = np.vstack(ub_rows)
            std_A = np.vstack([std_A, ub_A])
            std_b = np.concatenate([std_b, np.array(ub_rhs)])
            
            new_slacks = np.zeros((std_A.shape[0], num_ub))
            new_slacks[-num_ub:, :] = np.eye(num_ub)
            
            std_A = np.hstack([std_A, new_slacks])
            std_c = np.concatenate([std_c, np.zeros(num_ub)])

        # Ensure RHS >= 0
        for i in range(len(std_b)):
            if std_b[i] < 0:
                std_A[i, :] = -std_A[i, :]
                std_b[i] = -std_b[i]

        return std_c, std_A, std_b, recovery_meta

    def recover(self, std_x: np.ndarray, recovery_meta: Dict, n_original: int) -> np.ndarray:
        orig_x = np.zeros(n_original)
        var_mapping = recovery_meta['var_mapping']
        shifts = recovery_meta.get('shifts', {})
        
        for j in range(n_original):
            map_info = var_mapping[j]
            shift = shifts.get(j, 0.0)
            
            if map_info[0] == 'std':
                orig_x[j] = std_x[map_info[1]] + shift
            elif map_info[0] == 'split':
                orig_x[j] = std_x[map_info[1]] - std_x[map_info[2]] + shift
                
        return orig_x
