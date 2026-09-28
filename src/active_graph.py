from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from src.data_models import (
    OptimizationModel, Event, SupplyChainState, PersistentOptimizationState,
    BoundaryCondition, ConstraintMeta, VariableMeta, VariableType, ConstraintSense
)

class RelevanceReason(Enum):
    DIRECT_EVENT = auto()
    DEPENDENCY = auto()
    SHARED_RESOURCE = auto()
    FLOW_PROPAGATION = auto()
    CONSTRAINT_CLOSURE = auto()

@dataclass
class RelevanceScore:
    score: float
    reasons: List[RelevanceReason] = field(default_factory=list)
    
    def add_reason(self, reason: RelevanceReason, added_score: float):
        if reason not in self.reasons:
            self.reasons.append(reason)
        self.score += added_score

@dataclass
class ActiveElement:
    id: str
    relevance: RelevanceScore = field(default_factory=lambda: RelevanceScore(0.0))

@dataclass
class ActiveVariable(ActiveElement):
    pass

@dataclass
class ActiveConstraint(ActiveElement):
    pass

@dataclass
class ActiveNode(ActiveElement):
    pass

@dataclass
class ActiveEdge(ActiveElement):
    pass

@dataclass
class ADSConfig:
    max_depth: int = 5
    min_threshold: float = 0.1
    max_variables: int = 10000
    max_constraints: int = 10000

@dataclass
class ADSDiagnostics:
    seed_count: int = 0
    expansion_depth: int = 0
    selected_count: int = 0
    excluded_count: int = 0
    
    full_variables: int = 0
    active_variables: int = 0
    
    full_constraints: int = 0
    active_constraints: int = 0
    
    full_nodes: int = 0
    active_nodes: int = 0
    
    full_edges: int = 0
    active_edges: int = 0

    @property
    def variable_reduction_ratio(self) -> float:
        return 1.0 - (self.active_variables / self.full_variables) if self.full_variables > 0 else 0.0

    @property
    def constraint_reduction_ratio(self) -> float:
        return 1.0 - (self.active_constraints / self.full_constraints) if self.full_constraints > 0 else 0.0

    @property
    def node_reduction_ratio(self) -> float:
        return 1.0 - (self.active_nodes / self.full_nodes) if self.full_nodes > 0 else 0.0

    @property
    def edge_reduction_ratio(self) -> float:
        return 1.0 - (self.active_edges / self.full_edges) if self.full_edges > 0 else 0.0

class ActiveDecisionSubgraph:
    def __init__(self, full_model_id: str = "base"):
        self.full_model_id = full_model_id
        self.variables: Dict[str, ActiveVariable] = {}
        self.constraints: Dict[str, ActiveConstraint] = {}
        self.nodes: Dict[str, ActiveNode] = {}
        self.edges: Dict[str, ActiveEdge] = {}
        self.boundary_conditions: Dict[str, BoundaryCondition] = {}
        self.diagnostics = ADSDiagnostics()

    def to_active_model(self, full_model: OptimizationModel, state: PersistentOptimizationState) -> OptimizationModel:
        """
        Creates a valid OptimizationModel containing only the active region.
        Variables outside the region that are required for active constraints
        are evaluated using their values from the persistent state.
        """
        active_model = OptimizationModel(problem_type=full_model.problem_type)
        
        # Add active variables
        for v_id in self.variables:
            active_model.variables[v_id] = full_model.variables[v_id]
            
        # Add active constraints, adjusting RHS for boundary conditions
        for c_id in self.constraints:
            base_c = full_model.constraints[c_id]
            # Create a copy since we might modify rhs
            new_c = ConstraintMeta(
                name=base_c.name,
                sense=base_c.sense,
                rhs=base_c.rhs,
                role=base_c.role
            )
            # In a real sparse matrix we'd adjust the RHS vector `b` based on A_boundary * x_boundary
            # Here we just copy the metadata. The actual numerical boundary adjustment 
            # would happen in the sparse matrix builder.
            active_model.constraints[c_id] = new_c
            
        return active_model

class ADSBuilder:
    def __init__(self, config: ADSConfig = None):
        self.config = config or ADSConfig()
        
    def build(self, 
              full_model: OptimizationModel, 
              events: List[Event], 
              state: PersistentOptimizationState,
              dependency_graph: Optional[Dict[str, List[str]]] = None,
              graph: Optional[Any] = None) -> ActiveDecisionSubgraph:
        """
        Builds the ADS from the full model and events.
        """
        ads = ActiveDecisionSubgraph()
        
        # Initialize diagnostics
        ads.diagnostics.full_variables = len(full_model.variables)
        ads.diagnostics.full_constraints = len(full_model.constraints)
        # Note: full_nodes and full_edges would come from SupplyChainGraph if available
        
        if not events:
            # Empty / no event case
            return ads
            
        # 1. Seed formulation
        seeds = set()
        for evt in events:
            for v in evt.affected_variables:
                seeds.add(v)
                if v not in ads.variables:
                    ads.variables[v] = ActiveVariable(v)
                ads.variables[v].relevance.add_reason(RelevanceReason.DIRECT_EVENT, 1.0)
            
            for c in evt.affected_constraints:
                if c not in ads.constraints:
                    ads.constraints[c] = ActiveConstraint(c)
                ads.constraints[c].relevance.add_reason(RelevanceReason.DIRECT_EVENT, 1.0)
                
        ads.diagnostics.seed_count = len(seeds)
        
        # 2. Dependency & Flow Expansion
        # For this phase, we use a simple heuristic mock: if dependency_graph is provided, we traverse it
        current_layer = list(seeds)
        for depth in range(self.config.max_depth):
            next_layer = []
            if not current_layer:
                break
                
            ads.diagnostics.expansion_depth = depth + 1
            
            for item in current_layer:
                if dependency_graph and item in dependency_graph:
                    for dep in dependency_graph[item]:
                        if len(ads.variables) >= self.config.max_variables:
                            break
                        
                        # Apply decay based on depth
                        rel_score = 1.0 / (depth + 2.0)
                        
                        if rel_score < self.config.min_threshold:
                            ads.diagnostics.excluded_count += 1
                            continue
                            
                        if dep not in ads.variables:
                            ads.variables[dep] = ActiveVariable(dep)
                            next_layer.append(dep)
                        ads.variables[dep].relevance.add_reason(RelevanceReason.DEPENDENCY, rel_score)
            
            current_layer = next_layer
            
        # 3. Constraint Closure
        # For every active variable, if it participates in constraints, those constraints must be evaluated.
        # Conversely, if a constraint is active, its participating variables should be considered.
        # Here we mock this structural relationship for the supply chain:
        # A variable like flow_A_B_t0 usually connects to balance_A and balance_B.
        self._apply_constraint_closure(ads, full_model, state, graph)
        
        # Finalize diagnostics
        ads.diagnostics.active_variables = len(ads.variables)
        ads.diagnostics.active_constraints = len(ads.constraints)
        ads.diagnostics.selected_count = ads.diagnostics.active_variables + ads.diagnostics.active_constraints
        
        # Sort deterministic (dictionaries in Python 3.7+ preserve insertion, but we can sort explicitly if needed)
        # We leave them as dictionaries since dict iteration order is stable.
        
        return ads

    def _apply_constraint_closure(self, ads: ActiveDecisionSubgraph, full_model: OptimizationModel, state: PersistentOptimizationState, graph: Optional[Any] = None):
        """
        Ensures that if a variable is in the ADS, the essential constraints it participates in are included,
        and boundary variables for those constraints are marked.
        """
        # General matrix-based closure: Any constraint involving an active variable is active.
        if hasattr(full_model, 'A') and full_model.A is not None:
            A = full_model.A
            import scipy.sparse as sp
            import numpy as np
            var_names = list(full_model.variables.keys())
            con_names = list(full_model.constraints.keys())
            
            var_to_idx = {name: i for i, name in enumerate(var_names)}
            idx_to_con = {i: name for i, name in enumerate(con_names)}
            
            # If CSR, convert to CSC for efficient column slicing
            A_csc = A.tocsc() if sp.issparse(A) else np.array(A)
            
            for v_id in list(ads.variables.keys()):
                if v_id in var_to_idx:
                    col_idx = var_to_idx[v_id]
                    if sp.issparse(A_csc):
                        col = A_csc.getcol(col_idx)
                        row_indices = col.indices
                    else:
                        row_indices = np.where(A_csc[:, col_idx] != 0)[0]
                        
                    for row_idx in row_indices:
                        c_id = idx_to_con[row_idx]
                        if c_id not in ads.constraints:
                            ads.constraints[c_id] = ActiveConstraint(c_id)
                            ads.constraints[c_id].relevance.add_reason(RelevanceReason.CONSTRAINT_CLOSURE, 0.5)

        # Boundary condition identification
        # Boundary variables are those NOT in ADS but participate in an active constraint.
        # We need the A matrix to find this accurately.
        if state.previous_solution and state.previous_solution.primal_values and hasattr(full_model, 'A') and full_model.A is not None:
            A = full_model.A
            import scipy.sparse as sp
            var_names = list(full_model.variables.keys())
            con_names = list(full_model.constraints.keys())
            
            var_to_idx = {name: i for i, name in enumerate(var_names)}
            idx_to_var = {i: name for i, name in enumerate(var_names)}
            
            con_to_idx = {name: i for i, name in enumerate(con_names)}
            
            for c_id in ads.constraints:
                if c_id not in con_to_idx:
                    continue
                row_idx = con_to_idx[c_id]
                if sp.issparse(A):
                    row = A.getrow(row_idx)
                    indices = row.indices
                else:
                    import numpy as np
                    indices = np.where(A[row_idx] != 0)[0]
                    
                for col_idx in indices:
                    v_id = idx_to_var[col_idx]
                    if v_id not in ads.variables:
                        if v_id in state.previous_solution.primal_values:
                            val = state.previous_solution.primal_values[v_id]
                            ads.boundary_conditions[v_id] = BoundaryCondition(v_id, val)
