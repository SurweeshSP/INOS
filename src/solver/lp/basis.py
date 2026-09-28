from typing import List, Tuple
import numpy as np

class BasisManager:
    """
    Manages the basis for the Revised Simplex method.
    Avoids explicit inverse. Uses factorization or sparse solves.
    """
    def __init__(self, m: int):
        # basic variables indices
        self.basic_indices: List[int] = list(range(m))
        self.B_matrix = np.eye(m)
    
    def set_basis(self, basic_indices: List[int], B_matrix: np.ndarray):
        self.basic_indices = basic_indices
        self.B_matrix = B_matrix

    def solve_B_x_equals_b(self, b: np.ndarray) -> np.ndarray:
        """
        Solves Bx = b for x
        """
        return np.linalg.solve(self.B_matrix, b)

    def solve_B_T_y_equals_c(self, c: np.ndarray) -> np.ndarray:
        """
        Solves B^T y = c for y
        """
        return np.linalg.solve(self.B_matrix.T, c)

    def update_basis(self, entering_idx: int, leaving_idx: int, entering_col: np.ndarray):
        """
        Replace leaving_idx in basis with entering_idx
        """
        idx_in_basis = self.basic_indices.index(leaving_idx)
        self.basic_indices[idx_in_basis] = entering_idx
        self.B_matrix[:, idx_in_basis] = entering_col
