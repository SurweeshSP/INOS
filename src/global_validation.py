from typing import Dict, List, Set, Any
from dataclasses import dataclass, field
from src.data_models import (
    OptimizationModel, SolutionRecord, VariableType, ConstraintSense
)

@dataclass
class ValidationDiagnostics:
    max_violation: float = 0.0
    mean_violation: float = 0.0
    number_of_violated_constraints: int = 0
    total_violation: float = 0.0
    
    number_of_bound_violations: int = 0
    number_of_integrality_violations: int = 0
    
    objective_difference: float = 0.0

@dataclass
class GlobalValidationResult:
    is_valid: bool = True
    violated_constraints: List[str] = field(default_factory=list)
    violating_variables: List[str] = field(default_factory=list)
    expansion_seeds: List[str] = field(default_factory=list)
    diagnostics: ValidationDiagnostics = field(default_factory=ValidationDiagnostics)

class GlobalValidator:
    """
    Validates a candidate solution against the FULL optimization model.
    The model is immutable during this process.
    """
    def __init__(self, feasibility_tol: float = 1e-6, integrality_tol: float = 1e-5):
        self.feasibility_tol = feasibility_tol
        self.integrality_tol = integrality_tol

    def validate(self, full_model: OptimizationModel, candidate: SolutionRecord, matrix_A_data: Dict[str, Dict[str, float]] = None) -> GlobalValidationResult:
        """
        Validates the candidate solution.
        Since we mock the dense/sparse matrix in the python classes, we accept an optional
        `matrix_A_data` dictionary: matrix_A_data[c_id][v_id] = coefficient.
        If not provided, we mock perfect constraint satisfaction unless explicitly flagged in tests.
        """
        result = GlobalValidationResult()
        diag = result.diagnostics
        
        primal = candidate.primal_values or {}
        
        # 1. Variable Validation (Bounds & Integrality)
        for v_id, meta in full_model.variables.items():
            val = primal.get(v_id, 0.0)
            
            # Lower bound
            if meta.lb is not None and val < meta.lb - self.feasibility_tol:
                result.is_valid = False
                result.violating_variables.append(v_id)
                result.expansion_seeds.append(v_id)
                diag.number_of_bound_violations += 1
                
            # Upper bound
            if meta.ub is not None and val > meta.ub + self.feasibility_tol:
                result.is_valid = False
                if v_id not in result.violating_variables:
                    result.violating_variables.append(v_id)
                if v_id not in result.expansion_seeds:
                    result.expansion_seeds.append(v_id)
                diag.number_of_bound_violations += 1
                
            # Integrality
            if meta.var_type in (VariableType.INTEGER, VariableType.BINARY):
                rounded = round(val)
                if abs(val - rounded) > self.integrality_tol:
                    result.is_valid = False
                    if v_id not in result.violating_variables:
                        result.violating_variables.append(v_id)
                    if v_id not in result.expansion_seeds:
                        result.expansion_seeds.append(v_id)
                    diag.number_of_integrality_violations += 1
                    
        # 2. Constraint Feasibility
        if matrix_A_data:
            for c_id, meta in full_model.constraints.items():
                row_coeffs = matrix_A_data.get(c_id, {})
                ax = sum(coeff * primal.get(v, 0.0) for v, coeff in row_coeffs.items())
                
                violation = 0.0
                if meta.sense == ConstraintSense.EQ:
                    violation = abs(ax - meta.rhs)
                elif meta.sense == ConstraintSense.LE:
                    violation = max(0.0, ax - meta.rhs)
                elif meta.sense == ConstraintSense.GE:
                    violation = max(0.0, meta.rhs - ax)
                    
                if violation > self.feasibility_tol:
                    result.is_valid = False
                    result.violated_constraints.append(c_id)
                    diag.number_of_violated_constraints += 1
                    diag.total_violation += violation
                    diag.max_violation = max(diag.max_violation, violation)
                    
                    for v in row_coeffs.keys():
                        if v not in result.expansion_seeds:
                            result.expansion_seeds.append(v)
        else:
            if hasattr(full_model, 'A') and full_model.A is not None and candidate.variables is not None:
                try:
                    import numpy as np
                    Ax = full_model.A @ candidate.variables
                    senses = full_model.senses if hasattr(full_model, 'senses') and full_model.senses is not None else []
                    b = full_model.b
                    c_keys = list(full_model.constraints.keys())
                    v_keys = list(full_model.variables.keys())
                    
                    for i in range(len(b)):
                        c_id = c_keys[i] if i < len(c_keys) else f"c{i}"
                        meta = full_model.constraints.get(c_id)
                        
                        val = Ax[i] - b[i]
                        sense = senses[i] if i < len(senses) else ('E' if not meta else meta.sense)
                        if isinstance(sense, str):
                            if sense == 'E':
                                viol = abs(val)
                            elif sense == 'L':
                                viol = max(0, val)
                            elif sense == 'G':
                                viol = max(0, -val)
                            else:
                                viol = abs(val)
                        else:
                            if sense == ConstraintSense.EQ:
                                viol = abs(val)
                            elif sense == ConstraintSense.LE:
                                viol = max(0.0, val)
                            elif sense == ConstraintSense.GE:
                                viol = max(0.0, -val)
                                
                        if viol > self.feasibility_tol:
                            result.is_valid = False
                            if c_id not in result.violated_constraints:
                                result.violated_constraints.append(c_id)
                            diag.number_of_violated_constraints += 1
                            diag.total_violation += viol
                            diag.max_violation = max(diag.max_violation, viol)
                            
                            # Approximation of participating variables for expansion (add all or those with large primal?)
                            # Actually, getting row non-zeros from A
                            if hasattr(full_model.A, 'getrow'):
                                row = full_model.A.getrow(i)
                                for j in row.indices:
                                    v_id = v_keys[j] if j < len(v_keys) else f"v{j}"
                                    if v_id not in result.expansion_seeds:
                                        result.expansion_seeds.append(v_id)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    result.is_valid = False

        if diag.number_of_violated_constraints > 0:
            diag.mean_violation = diag.total_violation / diag.number_of_violated_constraints

        # 3. Objective Calculation
        calculated_obj = sum(
            meta.obj_coef * primal.get(v_id, 0.0) 
            for v_id, meta in full_model.variables.items() 
            if meta.obj_coef
        )
        
        reported_obj = candidate.objective_value or 0.0
        diag.objective_difference = abs(calculated_obj - reported_obj)
        
        # Scale-aware objective tolerance
        obj_tol = self.feasibility_tol + 1e-4 * max(1.0, abs(calculated_obj), abs(reported_obj))
        
        if diag.objective_difference > obj_tol:
            result.is_valid = False
            # Signal objective mismatch in the diagnostics and violated constraints list
            result.violated_constraints.append("OBJECTIVE_MISMATCH")
        
        # Deduplicate sets
        result.violating_variables = list(set(result.violating_variables))
        result.expansion_seeds = list(set(result.expansion_seeds))

        return result
