import numpy as np
import scipy.sparse as sp
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Any
from src.data_models import OptimizationModel, ProblemType, VariableType

@dataclass
class ModelValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dimensions: Tuple[int, int] = (0, 0)
    nonzeros: int = 0
    problem_type: Optional[ProblemType] = None

class ModelValidator:
    """
    Independently validates an OptimizationModel instance for dimension consistency,
    NaNs, and well-formed metadata before it reaches any numerical solver.
    """
    
    @staticmethod
    def validate(model: OptimizationModel) -> ModelValidationResult:
        result = ModelValidationResult(valid=True, problem_type=model.problem_type)
        
        if model.A is None:
            result.valid = False
            result.errors.append("Constraint matrix A is None. Must be a sparse matrix (e.g., shape (0, n)).")
            return result
            
        if not sp.issparse(model.A):
            result.warnings.append("Constraint matrix A is not a scipy sparse matrix.")
            
        m, n = model.A.shape
        result.dimensions = (m, n)
        result.nonzeros = model.A.nnz if hasattr(model.A, 'nnz') else 0
        
        # Validate b
        if model.b is None:
            result.valid = False
            result.errors.append("RHS vector b is None.")
        elif len(model.b) != m:
            result.valid = False
            result.errors.append(f"Dimension mismatch: b has length {len(model.b)}, expected {m}.")
        elif not np.all(np.isfinite(model.b)):
            result.valid = False
            result.errors.append("RHS vector b contains NaN or Inf.")

        # Validate c
        if model.c is None:
            result.valid = False
            result.errors.append("Objective vector c is None.")
        elif len(model.c) != n:
            result.valid = False
            result.errors.append(f"Dimension mismatch: c has length {len(model.c)}, expected {n}.")
        elif not np.all(np.isfinite(model.c)):
            result.valid = False
            result.errors.append("Objective vector c contains NaN or Inf.")

        # Validate lower_bounds and upper_bounds
        if model.lower_bounds is None:
            result.valid = False
            result.errors.append("lower_bounds is None.")
        elif len(model.lower_bounds) != n:
            result.valid = False
            result.errors.append(f"Dimension mismatch: lower_bounds has length {len(model.lower_bounds)}, expected {n}.")
            
        if model.upper_bounds is None:
            result.valid = False
            result.errors.append("upper_bounds is None.")
        elif len(model.upper_bounds) != n:
            result.valid = False
            result.errors.append(f"Dimension mismatch: upper_bounds has length {len(model.upper_bounds)}, expected {n}.")
            
        if model.lower_bounds is not None and model.upper_bounds is not None and len(model.lower_bounds) == n and len(model.upper_bounds) == n:
            if not np.all(model.lower_bounds <= model.upper_bounds):
                result.valid = False
                result.errors.append("Bounds consistency error: lower_bounds > upper_bounds for some variables.")

        # Validate metadata
        if len(model.variables) != n:
            result.warnings.append(f"Variable metadata dictionary length ({len(model.variables)}) does not match n ({n}).")
        
        if len(model.constraints) != m:
            result.warnings.append(f"Constraint metadata dictionary length ({len(model.constraints)}) does not match m ({m}).")
            
        # Validate Q for QP
        if model.problem_type == ProblemType.QP:
            if model.Q is None:
                result.valid = False
                result.errors.append("Problem type is QP, but Q matrix is None.")
            else:
                q_m, q_n = model.Q.shape
                if q_m != n or q_n != n:
                    result.valid = False
                    result.errors.append(f"Q matrix dimensions {model.Q.shape} do not match n x n ({n} x {n}).")
                if not sp.issparse(model.Q):
                    result.warnings.append("Q matrix is not a scipy sparse matrix.")
                if hasattr(model.Q, 'nnz'):
                    result.nonzeros += model.Q.nnz
                    
        return result
