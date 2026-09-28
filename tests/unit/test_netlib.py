import os
from src.datasets.netlib import NetlibLoader
from src.data_models import ProblemType

def test_mps_parser_simple(tmp_path):
    # Create a simple mock MPS file
    mps_content = """NAME          TEST
ROWS
 N  OBJ
 E  C1
 L  C2
COLUMNS
    X1        OBJ       1.0   C1        2.0
    X1        C2        1.0
    X2        OBJ       2.0   C1        1.0
RHS
    RHS1      C1        4.0   C2        3.0
BOUNDS
 UP BND1      X1        5.0
 LO BND1      X2        1.0
ENDATA
"""
    data_dir = tmp_path / "netlib"
    data_dir.mkdir()
    file_path = data_dir / "test.mps"
    file_path.write_text(mps_content)
    
    loader = NetlibLoader(data_dir=str(data_dir))
    model = loader.load_instance("TEST")
    
    assert model.name == "TEST"
    assert model.problem_type == ProblemType.LP
    
    assert "X1" in model.variables
    assert "X2" in model.variables
    
    assert model.variables["X1"].ub == 5.0
    assert model.variables["X2"].lb == 1.0
    
    assert "C1" in model.constraints
    assert "C2" in model.constraints
    
    from src.data_models import ConstraintSense
    import numpy as np
    
    assert model.constraints["C1"].sense == ConstraintSense.EQ
    assert model.constraints["C2"].sense == ConstraintSense.LE
    
    # Check bounds array
    assert model.bounds[0] == (0.0, 5.0) # X1
    assert model.bounds[1] == (1.0, float('inf')) # X2
    
    # Check b array
    assert np.allclose(model.b, [4.0, 3.0])
    
    # Check c array
    assert np.allclose(model.c, [1.0, 2.0])
    
    # Check A matrix
    # X1 col = [2.0, 1.0]
    # X2 col = [1.0, 0.0]
    expected_A = np.array([
        [2.0, 1.0],
        [1.0, 0.0]
    ])
    A_dense = model.A.toarray() if hasattr(model.A, "toarray") else model.A
    assert np.allclose(A_dense, expected_A)
