import pytest
import os
from src.datasets.netlib import NetlibLoader
from src.solver.cpu import solve_cpu
from src.service.validation_service import validation_service

def test_objective_reconstruction_with_offset(tmp_path):
    """
    Validates that MPS instances with objective constants (RHS N rows)
    are accurately reconstructed using the independent validation pipeline.
    """
    # Create an MPS file with a COST RHS shift (objective offset)
    mps_content = """NAME          test_offset
ROWS
 N  COST
 E  EQ1
 L  INEQ1
COLUMNS
    X1        COST      -1.0   EQ1       1.0
    X1        INEQ1     1.0
    X2        COST      -2.0   EQ1       1.0
    X2        INEQ1     2.0
RHS
    RHS1      EQ1       10.0   INEQ1     15.0
    RHS1      COST      2.0
BOUNDS
 UP BND1      X1        8.0
 LO BND1      X2        1.0
ENDATA
"""
    
    test_file = tmp_path / "test_offset.mps"
    test_file.write_text(mps_content)
    
    loader = NetlibLoader()
    loader.data_dir = str(tmp_path)
    model = loader.load_instance('test_offset')
    
    # Solve
    solution = solve_cpu(model, options={'time_limit': 10.0})
    assert solution.status.name == "OPTIMAL"
    
    # Test validation
    validation = validation_service.validate_solution(model, solution)
    assert validation.is_valid
    
    # Assert objective reconstruction math
    reconstructed_objective = validation.objective_recomputed
    solver_objective = solution.objective_value
    
    objective_tolerance = 1e-6
    diff = abs(reconstructed_objective - solver_objective)
    
    assert diff <= objective_tolerance, f"Objective reconstruction mismatch: {reconstructed_objective} != {solver_objective}"
    
    # Mathematical check: without shift, z = -15.0. 
    # With shift of +2.0 in RHS COST, objective offset = 2.0.
    # Standard formula: c^T x = z + RHS_COST => z = c^T x - RHS_COST
    # z = -15.0 - 2.0 = -17.0
    assert abs(solver_objective - (-17.0)) <= 1e-6, f"Expected -17.0, got {solver_objective}"
