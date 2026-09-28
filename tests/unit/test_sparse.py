import numpy as np
from src.solver.sparse import SparseMatrix
import math

def test_sparse_matrix_operations():
    # Dense matrix
    dense_A = np.array([
        [1.0, 0.0, 2.0],
        [0.0, 3.0, 0.0],
        [4.0, 0.0, 5.0]
    ])
    
    A = SparseMatrix(dense_A)
    x = np.array([1.0, 1.0, 1.0])
    
    # Check A * x
    Ax = A.dot(x)
    assert np.allclose(Ax, np.array([3.0, 3.0, 9.0]))
    
    # Check A.T * x
    ATx = A.dot_transpose(x)
    assert np.allclose(ATx, np.array([5.0, 3.0, 7.0]))
    
    # Check row extraction
    row1 = A.get_row(1)
    assert np.allclose(row1, np.array([0.0, 3.0, 0.0]))
    
    # Check col extraction
    col2 = A.get_col(2)
    assert np.allclose(col2, np.array([2.0, 0.0, 5.0]))
    
    # Check submatrix
    sub_A = A.get_submatrix([0, 2], [0, 2])
    assert sub_A.shape == (2, 2)
    assert np.allclose(sub_A.get_row(0), np.array([1.0, 2.0]))
    assert np.allclose(sub_A.get_row(1), np.array([4.0, 5.0]))
    
    # Check residual
    b = np.array([4.0, 4.0, 10.0])
    res = A.residual(b, x)
    assert np.allclose(res, np.array([1.0, 1.0, 1.0]))

def test_sparsity_preservation():
    # Large identity matrix
    dense = np.eye(1000)
    sparse_A = SparseMatrix(dense)
    assert sparse_A.nnz == 1000
