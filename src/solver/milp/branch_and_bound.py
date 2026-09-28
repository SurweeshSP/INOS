import time
import math
import numpy as np
from typing import Dict, Optional, Any, Tuple, List

from src.data_models import OptimizationModel, SolutionRecord, SolveStatus, VariableType, VariableMeta
from src.solver.milp.node import BranchAndBoundNode, NodeQueue
from src.solver.milp.managers import IncumbentManager, BoundManager
from src.solver.lp.standardization import Standardizer
from src.solver.lp.simplex import RevisedSimplexSolver
from src.solver.numerical import NumericalConfig

class BranchAndBoundSolver:
    def __init__(self, config: Optional[NumericalConfig] = None):
        self.config = config or NumericalConfig()
        self.node_queue = NodeQueue(strategy="depth_first") # Start with DFS to find incumbent
        self.incumbent_manager = IncumbentManager()
        self.bound_manager = BoundManager()
        
        # Statistics
        self.nodes_created = 0
        self.nodes_processed = 0
        self.nodes_pruned = 0
        self.lp_relaxations = 0
        
    def solve(self, model: OptimizationModel, 
              time_limit: float = 3600.0, 
              node_limit: int = 100000) -> SolutionRecord:
              
        start_time = time.time()
        
        if not model.variables or model.A is None:
            return SolutionRecord(
                status=SolveStatus.NOT_SOLVED,
                runtime=time.time() - start_time
            )
            
        # Extract integer/binary variables
        int_vars = [
            var_name for var_name, var_meta in model.variables.items()
            if var_meta.var_type in (VariableType.INTEGER, VariableType.BINARY)
        ]
        
        if not int_vars:
            # Not a MILP, just run LP
            status, primal, obj, iters = self._solve_lp_relaxation(model, {})
            x_array = np.zeros(len(model.variables))
            for i, name in enumerate(model.variables.keys()):
                x_array[i] = primal.get(name, 0.0)
            if hasattr(model, 'objective_offset'):
                obj -= model.objective_offset
                
            return SolutionRecord(
                status=status,
                objective_value=obj,
                primal_values=primal,
                variables=x_array,
                iterations=iters,
                runtime=time.time() - start_time
            )
            
        # Root node
        root_node = BranchAndBoundNode(
            id=self.nodes_created,
            depth=0,
            parent_id=-1,
            bound_updates={}
        )
        self.nodes_created += 1
        self.node_queue.push(root_node)
        
        termination_status = SolveStatus.NOT_SOLVED
        
        while not self.node_queue.is_empty():
            if time.time() - start_time > time_limit:
                termination_status = SolveStatus.SUBOPTIMAL # Time limit
                break
                
            if self.nodes_processed >= node_limit:
                termination_status = SolveStatus.SUBOPTIMAL # Node limit
                break
                
            node = self.node_queue.pop()
            self.nodes_processed += 1
            
            # Prune by bound (before solving if bound is already known to be worse than incumbent)
            if self.incumbent_manager.has_incumbent() and node.lp_objective >= self.incumbent_manager.best_objective:
                self.nodes_pruned += 1
                continue
                
            # Solve LP relaxation
            lp_status, primal_vals, lp_obj, lp_iters = self._solve_lp_relaxation(model, node.bound_updates)
            self.lp_relaxations += 1
            
            if lp_status != SolveStatus.OPTIMAL:
                # Infeasible or unbounded relaxation -> prune
                self.nodes_pruned += 1
                continue
                
            node.lp_objective = lp_obj
            node.lp_primal_values = primal_vals
            
            # Prune by bound (after solving)
            if self.incumbent_manager.has_incumbent() and lp_obj >= self.incumbent_manager.best_objective - self.config.zero_tol:
                self.nodes_pruned += 1
                continue
                
            # Update global lower bound (only valid if we pop best-bound first, but we track minimum of queue)
            # For now, just a rough bound manager
            
            # Check integrality
            is_integer_feasible, fractional_var, fractional_val = self._check_integrality(primal_vals, int_vars)
            
            if is_integer_feasible:
                # New incumbent found!
                node.is_integer_feasible = True
                updated = self.incumbent_manager.update(lp_obj, primal_vals)
            else:
                # Branch
                if fractional_var is not None:
                    # Floor branch: x <= floor(val)
                    left_bounds = node.bound_updates.copy()
                    left_bounds[fractional_var] = (
                        left_bounds.get(fractional_var, (0.0, float('inf')))[0],
                        math.floor(fractional_val)
                    )
                    left_node = BranchAndBoundNode(
                        id=self.nodes_created,
                        depth=node.depth + 1,
                        parent_id=node.id,
                        bound_updates=left_bounds,
                        lp_objective=lp_obj # Inherit parent bound
                    )
                    self.nodes_created += 1
                    
                    # Ceil branch: x >= ceil(val)
                    right_bounds = node.bound_updates.copy()
                    right_bounds[fractional_var] = (
                        math.ceil(fractional_val),
                        right_bounds.get(fractional_var, (0.0, float('inf')))[1]
                    )
                    right_node = BranchAndBoundNode(
                        id=self.nodes_created,
                        depth=node.depth + 1,
                        parent_id=node.id,
                        bound_updates=right_bounds,
                        lp_objective=lp_obj
                    )
                    self.nodes_created += 1
                    
                    self.node_queue.push(left_node)
                    self.node_queue.push(right_node)
                    
        # Conclude
        if self.incumbent_manager.has_incumbent():
            if termination_status == SolveStatus.NOT_SOLVED:
                termination_status = SolveStatus.OPTIMAL
                
            primal_dict = self.incumbent_manager.best_solution or {}
            
            # Map dict back to numpy array for validation
            col_names = list(model.variables.keys())
            x_array = np.zeros(len(col_names))
            for i, name in enumerate(col_names):
                x_array[i] = primal_dict.get(name, 0.0)
            
            final_obj = self.incumbent_manager.best_objective
            if hasattr(model, 'objective_offset'):
                final_obj -= model.objective_offset
            
            return SolutionRecord(
                status=termination_status,
                objective_value=final_obj,
                primal_values=primal_dict,
                variables=x_array,
                iterations=self.nodes_processed,
                runtime=time.time() - start_time
            )
        else:
            return SolutionRecord(
                status=SolveStatus.INFEASIBLE,
                iterations=self.nodes_processed,
                runtime=time.time() - start_time
            )

    def _solve_lp_relaxation(self, base_model: OptimizationModel, bound_updates: Dict[str, Tuple[float, float]]) -> Tuple[SolveStatus, Dict[str, float], float, int]:
        """
        Solves the LP relaxation for a specific node by applying bound updates.
        """
        # We need to temporarily apply bounds to the model.
        # Since OptimizationModel bounds are stored in a list `model.bounds` corresponding to columns,
        # we need to map names to indices.
        
        # We assume base_model has variables ordered matching columns in A.
        col_names = list(base_model.variables.keys())
        name_to_idx = {name: i for i, name in enumerate(col_names)}
        
        # Copy bounds
        original_lb = base_model.lower_bounds.copy()
        original_ub = base_model.upper_bounds.copy()
        
        for var_name, (new_lb, new_ub) in bound_updates.items():
            idx = name_to_idx[var_name]
            orig_lb = original_lb[idx]
            orig_ub = original_ub[idx]
            # Tighten bounds
            applied_lb = max(orig_lb, new_lb)
            applied_ub = min(orig_ub, new_ub)
            base_model.lower_bounds[idx] = applied_lb
            base_model.upper_bounds[idx] = applied_ub
            
        # Standardize
        standardizer = Standardizer()
        std_lp = standardizer.standardize(base_model)
        std_c, std_A, std_b, recovery_meta = standardizer.to_simplex_standard_form(std_lp)
        
        # Solve
        solver = RevisedSimplexSolver(self.config)
        status, std_x, y, obj = solver.solve(std_c, std_A, std_b, max_iter=10000)
        
        primal_vals = {}
        if status == SolveStatus.OPTIMAL:
            x_orig = standardizer.recover(std_x, recovery_meta, len(base_model.variables))
            for i, name in enumerate(col_names):
                primal_vals[name] = x_orig[i]
            
            # Recompute canonical objective to bypass standardizer shift offsets
            if base_model.c is not None:
                obj = float(base_model.c @ x_orig)
                
        # Restore original bounds
        base_model.lower_bounds = original_lb
        base_model.upper_bounds = original_ub
        
        return status, primal_vals, obj, solver.iterations

    def _check_integrality(self, primal_vals: Dict[str, float], int_vars: List[str]) -> Tuple[bool, Optional[str], float]:
        """
        Checks if integer variables satisfy integrality.
        Returns (is_feasible, most_fractional_var, fractional_val).
        """
        max_fractional_dist = -1.0
        branch_var = None
        branch_val = 0.0
        
        for var_name in int_vars:
            val = primal_vals.get(var_name, 0.0)
            nearest_int = round(val)
            dist = abs(val - nearest_int)
            
            if dist > self.config.integrality_tol:
                # Fractional
                # We branch on the variable with largest fractional distance (closest to 0.5)
                # distance to 0.5 is 0.5 - abs(val - floor(val) - 0.5)
                # Actually, standard most fractional is distance from integer
                if dist > max_fractional_dist:
                    max_fractional_dist = dist
                    branch_var = var_name
                    branch_val = val
                    
        is_integer_feasible = (branch_var is None)
        return is_integer_feasible, branch_var, branch_val
