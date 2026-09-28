from typing import Dict, List, Optional
from src.data_models import (
    NodeType,
    EdgeType,
    NodeMeta,
    EdgeMeta,
    OptimizationModel,
    ProblemType,
    VariableMeta,
    VariableType,
    ConstraintMeta,
    ConstraintSense,
    ConstraintRole
)

class SupplyChainGraph:
    def __init__(self, time_periods: int = 1):
        self.nodes: Dict[str, NodeMeta] = {}
        self.edges: Dict[str, EdgeMeta] = {}
        self.time_periods = time_periods

    def add_node(self, node_id: str, node_type: NodeType, capacity: Optional[float] = None, 
                 inventory: Optional[float] = None, demand: Optional[float] = None):
        self.nodes[node_id] = NodeMeta(
            id=node_id, 
            node_type=node_type, 
            capacity=capacity,
            inventory=inventory,
            demand=demand
        )

    def add_edge(self, source: str, target: str, edge_type: EdgeType, 
                 capacity: Optional[float] = None, cost: Optional[float] = None):
        edge_id = f"{source}_{target}"
        self.edges[edge_id] = EdgeMeta(
            source=source,
            target=target,
            edge_type=edge_type,
            capacity=capacity,
            cost=cost
        )

    def to_optimization_model(self) -> OptimizationModel:
        """
        Converts the supply chain graph into a canonical OptimizationModel mapping:
        - Edges -> Flow variables
        - Nodes -> Inventory variables (where applicable)
        - Capacities -> Upper bounds
        - Costs -> Objective coefficients
        - Flow conservation -> Constraints
        """
        model = OptimizationModel(problem_type=ProblemType.LP)

        # Variables: Flow on edges
        for edge_id, edge in self.edges.items():
            for t in range(self.time_periods):
                var_name = f"flow_{edge_id}_t{t}"
                model.variables[var_name] = VariableMeta(
                    name=var_name,
                    var_type=VariableType.CONTINUOUS,
                    lb=0.0,
                    ub=edge.capacity if edge.capacity is not None else float('inf'),
                    obj_coef=edge.cost if edge.cost is not None else 0.0
                )

        # Variables: Inventory and shortage at nodes
        for node_id, node in self.nodes.items():
            for t in range(self.time_periods):
                # Inventory
                if node.node_type in [NodeType.WAREHOUSE, NodeType.DC, NodeType.PLANT]:
                    inv_name = f"inv_{node_id}_t{t}"
                    model.variables[inv_name] = VariableMeta(
                        name=inv_name,
                        var_type=VariableType.CONTINUOUS,
                        lb=0.0,
                        ub=node.capacity if node.capacity is not None else float('inf'),
                        obj_coef=0.0 # inventory holding cost can be added
                    )
                # Shortage
                if node.node_type == NodeType.CUSTOMER:
                    shortage_name = f"shortage_{node_id}_t{t}"
                    model.variables[shortage_name] = VariableMeta(
                        name=shortage_name,
                        var_type=VariableType.CONTINUOUS,
                        lb=0.0,
                        ub=node.demand if node.demand is not None else float('inf'),
                        obj_coef=1000.0 # high penalty for shortage
                    )

        # Constraints: Flow conservation & demand fulfillment
        for node_id, node in self.nodes.items():
            for t in range(self.time_periods):
                in_edges = [f"flow_{e}_t{t}" for e, ev in self.edges.items() if ev.target == node_id]
                out_edges = [f"flow_{e}_t{t}" for e, ev in self.edges.items() if ev.source == node_id]

                # Flow Balance: In = Out (simplified for time T without inter-period inventory yet)
                if node.node_type in [NodeType.WAREHOUSE, NodeType.DC, NodeType.PLANT]:
                    # Basic balance
                    c_name = f"balance_{node_id}_t{t}"
                    model.constraints[c_name] = ConstraintMeta(
                        name=c_name,
                        sense=ConstraintSense.EQ,
                        rhs=0.0,
                        role=ConstraintRole.FLOW_BALANCE
                    )

                # Demand fulfillment: In + Shortage = Demand
                if node.node_type == NodeType.CUSTOMER:
                    c_name = f"demand_meet_{node_id}_t{t}"
                    model.constraints[c_name] = ConstraintMeta(
                        name=c_name,
                        sense=ConstraintSense.EQ,
                        rhs=node.demand if node.demand is not None else 0.0,
                        role=ConstraintRole.DEMAND_FULFILLMENT
                    )

        import numpy as np
        import scipy.sparse as sp

        # Map variable and constraint names to indices
        var_names = list(model.variables.keys())
        con_names = list(model.constraints.keys())
        n = len(var_names)
        m = len(con_names)

        var_to_idx = {name: i for i, name in enumerate(var_names)}
        con_to_idx = {name: i for i, name in enumerate(con_names)}

        # Build c, lb, ub
        c = np.zeros(n)
        lb = np.zeros(n)
        ub = np.full(n, np.inf)

        for i, name in enumerate(var_names):
            meta = model.variables[name]
            c[i] = meta.obj_coef
            lb[i] = meta.lb
            ub[i] = meta.ub

        # Build b, senses
        b = np.zeros(m)
        senses = []

        for i, name in enumerate(con_names):
            meta = model.constraints[name]
            b[i] = meta.rhs
            senses.append(meta.sense.name[0])  # 'E', 'L', 'G'

        # Build A
        row_indices = []
        col_indices = []
        data = []

        # Populate A based on Flow Balance & Demand Fulfillment
        # We need to reiterate and map to indices
        for node_id, node in self.nodes.items():
            for t in range(self.time_periods):
                in_edges = [f"flow_{e}_t{t}" for e, ev in self.edges.items() if ev.target == node_id]
                out_edges = [f"flow_{e}_t{t}" for e, ev in self.edges.items() if ev.source == node_id]

                if node.node_type in [NodeType.WAREHOUSE, NodeType.DC, NodeType.PLANT]:
                    c_name = f"balance_{node_id}_t{t}"
                    if c_name in con_to_idx:
                        c_idx = con_to_idx[c_name]
                        for edge_var in in_edges:
                            if edge_var in var_to_idx:
                                row_indices.append(c_idx)
                                col_indices.append(var_to_idx[edge_var])
                                data.append(1.0)
                        for edge_var in out_edges:
                            if edge_var in var_to_idx:
                                row_indices.append(c_idx)
                                col_indices.append(var_to_idx[edge_var])
                                data.append(-1.0)
                        inv_name = f"inv_{node_id}_t{t}"
                        if inv_name in var_to_idx:
                            # Current inventory balance logic
                            row_indices.append(c_idx)
                            col_indices.append(var_to_idx[inv_name])
                            data.append(-1.0)

                if node.node_type == NodeType.CUSTOMER:
                    c_name = f"demand_meet_{node_id}_t{t}"
                    if c_name in con_to_idx:
                        c_idx = con_to_idx[c_name]
                        for edge_var in in_edges:
                            if edge_var in var_to_idx:
                                row_indices.append(c_idx)
                                col_indices.append(var_to_idx[edge_var])
                                data.append(1.0)
                        shortage_name = f"shortage_{node_id}_t{t}"
                        if shortage_name in var_to_idx:
                            row_indices.append(c_idx)
                            col_indices.append(var_to_idx[shortage_name])
                            data.append(1.0)

        A = sp.csr_matrix((data, (row_indices, col_indices)), shape=(m, n))

        model.c = c
        model.lower_bounds = lb
        model.upper_bounds = ub
        model.A = A
        model.b = b
        model.senses = senses

        return model
