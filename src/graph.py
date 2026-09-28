from typing import List, Dict, Optional
from src.data_models import OptimizationModel, NodeMeta, EdgeMeta

class SupplyChainGraph:
    """
    Represents G = (V, E, T)
    """
    def __init__(self):
        self.nodes: Dict[str, NodeMeta] = {}
        self.edges: Dict[str, EdgeMeta] = {}
        self.time_periods: List[int] = []
        
        # Mappings to mathematical model
        self.node_to_vars: Dict[str, List[str]] = {}
        self.edge_to_vars: Dict[str, List[str]] = {}
        
        self.node_to_cons: Dict[str, List[str]] = {}
        self.edge_to_cons: Dict[str, List[str]] = {}

    def add_node(self, node: NodeMeta):
        self.nodes[node.id] = node
        self.node_to_vars[node.id] = []
        self.node_to_cons[node.id] = []

    def add_edge(self, edge: EdgeMeta):
        edge_id = f"{edge.source}->{edge.target}"
        self.edges[edge_id] = edge
        self.edge_to_vars[edge_id] = []
        self.edge_to_cons[edge_id] = []

    def map_variable(self, var_name: str, node_id: Optional[str] = None, edge_id: Optional[str] = None):
        if node_id and node_id in self.nodes:
            self.node_to_vars[node_id].append(var_name)
        if edge_id and edge_id in self.edges:
            self.edge_to_vars[edge_id].append(var_name)

    def map_constraint(self, con_name: str, node_id: Optional[str] = None, edge_id: Optional[str] = None):
        if node_id and node_id in self.nodes:
            self.node_to_cons[node_id].append(con_name)
        if edge_id and edge_id in self.edges:
            self.edge_to_cons[edge_id].append(con_name)

    def get_upstream_nodes(self, node_id: str) -> List[str]:
        return [e.source for e in self.edges.values() if e.target == node_id]

    def get_downstream_nodes(self, node_id: str) -> List[str]:
        return [e.target for e in self.edges.values() if e.source == node_id]
