import numpy as np
from scipy import sparse
from typing import Union, Tuple, List

class SparseMatrix:
    def __init__(self, data: Union[np.ndarray, sparse.spmatrix]):
        if isinstance(data, np.ndarray):
            self._matrix = sparse.csc_matrix(data)
        elif isinstance(data, sparse.spmatrix):
            self._matrix = data.tocsc()
        else:
            raise ValueError("Data must be a numpy array or scipy sparse matrix")

    @property
    def shape(self) -> Tuple[int, int]:
        return self._matrix.shape

    @property
    def nnz(self) -> int:
        return self._matrix.nnz

    def dot(self, vector: np.ndarray) -> np.ndarray:
        """Matrix-vector product: A * x"""
        return self._matrix.dot(vector)

    def dot_transpose(self, vector: np.ndarray) -> np.ndarray:
        """Transpose matrix-vector product: A.T * x"""
        return self._matrix.T.dot(vector)

    def get_row(self, i: int) -> np.ndarray:
        """Extract a single row as a dense 1D array."""
        return self._matrix[i, :].toarray().flatten()

    def get_col(self, j: int) -> np.ndarray:
        """Extract a single column as a dense 1D array."""
        return self._matrix[:, j].toarray().flatten()

    def get_submatrix(self, row_indices: List[int], col_indices: List[int]) -> 'SparseMatrix':
        """Extract a submatrix based on row and col indices."""
        sub_mat = self._matrix[row_indices, :][:, col_indices]
        return SparseMatrix(sub_mat)

    def residual(self, b: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Calculate the residual: b - A * x"""
        Ax = self.dot(x)
        return b - Ax
