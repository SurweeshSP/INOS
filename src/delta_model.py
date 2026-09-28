from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import numpy as np

from src.data_models import (
    OptimizationModel, SolutionRecord, VariableMeta, ConstraintMeta,
    ConstraintSense, ProblemType, SolveStatus
)
from src.active_graph import ActiveDecisionSubgraph
# Assuming sparse abstractions exist in src.solver.sparse
# For this mock/architecture, we'll represent the mathematical transformations structurally.

@dataclass
class DeltaDiagnostics:
    full_variable_count: int = 0
    active_variable_count: int = 0
    delta_variable_count: int = 0

    full_constraint_count: int = 0
    active_constraint_count: int = 0
    delta_constraint_count: int = 0

    base_objective: float = 0.0
    delta_objective: float = 0.0
    predicted_objective: float = 0.0

    boundary_variable_count: int = 0
    changed_bound_count: int = 0
    changed_rhs_count: int = 0
    changed_objective_count: int = 0

    nonzero_count: int = 0

@dataclass
class DeltaModel(OptimizationModel):
    base_solution_primal: Dict[str, float] = field(default_factory=dict)
    diagnostics: DeltaDiagnostics = field(default_factory=DeltaDiagnostics)
    
    # Track the constant offset to recover full objective
    objective_offset: float = 0.0

class DeltaModelBuilder:
    """
    Constructs a localized Delta Optimization Problem representing changes 
    from the current base solution using the Active Decision Subgraph.
    """
    def __init__(self):
        pass

    def build(self, 
              full_model: OptimizationModel, 
              ads: ActiveDecisionSubgraph, 
              base_solution: Optional[SolutionRecord]) -> DeltaModel:
              
        if not base_solution or not base_solution.primal_values:
            # If no base solution is available, the delta model is just the active model (Delta = absolute)
            raise ValueError("Base solution is required for Delta Model construction. If unavailable, use full reoptimization or handle fallback.")
            
        delta_model = DeltaModel(
            problem_type=full_model.problem_type,
            base_solution_primal=base_solution.primal_values.copy()
        )
        
        diag = delta_model.diagnostics
        diag.full_variable_count = len(full_model.variables)
        diag.full_constraint_count = len(full_model.constraints)
        diag.active_variable_count = len(ads.variables)
        diag.active_constraint_count = len(ads.constraints)
        
        # 1. Delta Variables
        # Δx = x - x_base
        for v_id in ads.variables:
            base_var = full_model.variables[v_id]
            x_base = base_solution.primal_values.get(v_id, 0.0)
            
            new_lb = None if base_var.lb is None else base_var.lb - x_base
            new_ub = None if base_var.ub is None else base_var.ub - x_base
            
            delta_var = VariableMeta(
                name=base_var.name,
                var_type=base_var.var_type,
                lb=new_lb,
                ub=new_ub,
                obj_coef=base_var.obj_coef
            )
            delta_model.variables[v_id] = delta_var
            
            # Constant offset added to objective: c^T x_base
            if base_var.obj_coef:
                delta_model.objective_offset += base_var.obj_coef * x_base
                
        diag.delta_variable_count = len(delta_model.variables)
        
        # 2. Boundary handling & Constraints
        # A_active * Δx_active = b - A_active * x_base_active - A_boundary * x_base_boundary
        # Assuming we have a way to query constraint coefficients from the full model.
        # Since our OptimizationModel dataclass mock doesn't hold the sparse matrix directly 
        # (usually constructed via the solver layer or graph layer), we will symbolically represent this.
        
        import numpy as np
        import scipy.sparse as sp

        has_matrix = hasattr(full_model, 'A') and full_model.A is not None
        
        if has_matrix:
            A_full = full_model.A
            b_full = full_model.b
            c_full = full_model.c
            bounds_full = full_model.bounds
            
            var_names = list(full_model.variables.keys())
            con_names = list(full_model.constraints.keys())
            
            n_vars = len(full_model.c)
            var_to_idx = {name: i for i, name in enumerate(var_names)}
            con_to_idx = {name: i for i, name in enumerate(con_names)}
            
            # If full_model.variables wasn't populated but we know we have n_vars
            if not var_names:
                var_to_idx = {f"v{i}": i for i in range(n_vars)}
                # Also we must assume ads.variables has elements like "v0", "v1"
            
            # Use active variables from ads, but if ads is using string names, it should match
            active_var_indices = [var_to_idx[v] for v in ads.variables if v in var_to_idx]
            
            # Similarly for constraints
            if not con_names and full_model.b is not None:
                con_to_idx = {f"c{i}": i for i in range(len(full_model.b))}
            active_con_indices = [con_to_idx[c] for c in ads.constraints if c in con_to_idx]
            
            x_base_vec = np.zeros(n_vars)
            if not var_names:
                for i in range(n_vars):
                    x_base_vec[i] = base_solution.primal_values.get(f"v{i}", 0.0)
            else:
                for i, v in enumerate(var_names):
                    x_base_vec[i] = base_solution.primal_values.get(v, 0.0)
                
            if sp.issparse(A_full):
                # A_A is the submatrix of active rows and active columns
                # We need A_active_rows
                A_active_rows = A_full[active_con_indices, :]
                A_A = A_active_rows[:, active_var_indices]
                
                # Boundary effect: A_B * x_B = A_active_rows * x_base - A_A * x_base_active
                # Actually, residual r = b - A*x_base. The new RHS for Delta x is just r!
                # Because A(x_base + dx) = b => A dx = b - A x_base
                # And we only care about active rows.
                # So new_rhs = b_active - A_active_rows * x_base_vec
                
                b_active = b_full[active_con_indices]
                new_rhs_vec = b_active - A_active_rows.dot(x_base_vec)
                
            else:
                A_active_rows = A_full[active_con_indices, :]
                A_A = A_active_rows[:, active_var_indices]
                b_active = b_full[active_con_indices]
                new_rhs_vec = b_active - A_active_rows.dot(x_base_vec)
                
            delta_model.A = A_A
            delta_model.b = new_rhs_vec
            delta_model.c = c_full[active_var_indices]
            
            # bounds for dx = lb - x_base, ub - x_base
            delta_lb = np.zeros(len(active_var_indices))
            delta_ub = np.zeros(len(active_var_indices))
            
            for i, idx in enumerate(active_var_indices):
                lb_val = full_model.lower_bounds[idx]
                ub_val = full_model.upper_bounds[idx]
                x_val = x_base_vec[idx]
                
                delta_lb[i] = lb_val - x_val if lb_val != -np.inf else -np.inf
                delta_ub[i] = ub_val - x_val if ub_val != np.inf else np.inf
                
            delta_model.lower_bounds = delta_lb
            delta_model.upper_bounds = delta_ub
            
            delta_model.senses = [full_model.senses[i] for i in active_con_indices] if hasattr(full_model, 'senses') and full_model.senses else ['E'] * len(active_con_indices)

        for i, c_id in enumerate(ads.constraints):
            base_c = full_model.constraints[c_id]
            new_rhs = float(delta_model.b[i]) if has_matrix else 0.0
            
            delta_model.constraints[c_id] = ConstraintMeta(
                name=base_c.name,
                sense=base_c.sense,
                rhs=new_rhs,
                role=base_c.role
            )
            
        diag.delta_constraint_count = len(delta_model.constraints)
        
        return delta_model

    def reconstruct_full_solution(self, 
                                  full_model: OptimizationModel, 
                                  delta_model: DeltaModel, 
                                  delta_solution_primal: Dict[str, float]) -> SolutionRecord:
        """
        x_full = x_base + Δx (for active)
        x_full = x_base (for inactive)
        """
        reconstructed = delta_model.base_solution_primal.copy()
        
        for v_id, delta_val in delta_solution_primal.items():
            if v_id in reconstructed:
                reconstructed[v_id] += delta_val
            else:
                reconstructed[v_id] = delta_val
                
        # Objective calculation:
        # We can approximate with the delta model's offset if linear, 
        # but Global Validation should calculate the exact full objective.
        # We'll just sum c^T x
        obj = 0.0
        for v_id, val in reconstructed.items():
            if v_id in full_model.variables:
                coef = full_model.variables[v_id].obj_coef or 0.0
                obj += coef * val
                
        # Build numpy array for variables
        has_matrix = hasattr(full_model, 'A') and full_model.A is not None
        vars_array = None
        if has_matrix and full_model.c is not None:
            n = len(full_model.c)
            import numpy as np
            vars_array = np.zeros(n)
            var_names = list(full_model.variables.keys())
            
            if not var_names:
                for i in range(n):
                    vars_array[i] = reconstructed.get(f"v{i}", 0.0)
            else:
                var_to_idx = {name: i for i, name in enumerate(var_names)}
                for v_id, val in reconstructed.items():
                    if v_id in var_to_idx:
                        vars_array[var_to_idx[v_id]] = val
                        
        return SolutionRecord(
            status=SolveStatus.OPTIMAL, # Pending global validation
            primal_values=reconstructed,
            objective_value=obj,
            variables=vars_array
        )
