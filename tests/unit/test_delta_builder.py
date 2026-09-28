import pytest
import numpy as np
from src.delta_model import DeltaModelBuilder
from src.active_graph import ActiveDecisionSubgraph, ActiveVariable, ActiveConstraint
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense, SolutionRecord, SolveStatus

def test_delta_builder_math():
    builder = DeltaModelBuilder()
    
    full_model = OptimizationModel(problem_type=ProblemType.LP)
    full_model.variables["x1"] = VariableMeta("x1", VariableType.CONTINUOUS, lb=0, ub=10)
    full_model.variables["x2"] = VariableMeta("x2", VariableType.CONTINUOUS, lb=0, ub=10)
    full_model.constraints["c1"] = ConstraintMeta("c1", ConstraintSense.LE, 15.0)
    
    full_model.A = np.array([[1.0, 2.0]]) # 1*x1 + 2*x2 <= 15
    full_model.b = np.array([15.0])
    full_model.c = np.array([1.0, 1.0])
    full_model.bounds = [(0, 10), (0, 10)]
    full_model.senses = ['L']
    
    base_sol = SolutionRecord(status=SolveStatus.OPTIMAL, primal_values={"x1": 5.0, "x2": 5.0})
    
    # Active Subgraph: only x1 is active
    ads = ActiveDecisionSubgraph()
    ads.variables["x1"] = ActiveVariable("x1")
    ads.constraints["c1"] = ActiveConstraint("c1")
    
    delta = builder.build(full_model, ads, base_sol)
    
    # Check new RHS. Base residual: b - A x_base = 15 - (5 + 10) = 0.
    assert delta.b[0] == 0.0
    
    # A_A should be just [[1.0]]
    assert delta.A.shape == (1, 1)
    assert delta.A[0, 0] == 1.0
    
    # bounds for dx1 = lb - 5, ub - 5 => (-5, 5)
    assert delta.bounds[0] == (-5.0, 5.0)
