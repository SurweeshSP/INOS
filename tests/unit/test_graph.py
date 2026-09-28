import pytest
from src.graph import SupplyChainGraph
from src.data_models import NodeMeta, NodeType, EdgeMeta, EdgeType

def test_supply_chain_graph_mapping():
    graph = SupplyChainGraph()
    
    n1 = NodeMeta(id="P1", node_type=NodeType.PLANT)
    n2 = NodeMeta(id="W1", node_type=NodeType.WAREHOUSE)
    graph.add_node(n1)
    graph.add_node(n2)
    
    e1 = EdgeMeta(source="P1", target="W1", edge_type=EdgeType.TRANSPORT)
    graph.add_edge(e1)
    
    graph.map_variable("flow_P1_W1", edge_id="P1->W1")
    graph.map_constraint("cap_P1", node_id="P1")
    
    assert "flow_P1_W1" in graph.edge_to_vars["P1->W1"]
    assert "cap_P1" in graph.node_to_cons["P1"]
    
    up = graph.get_upstream_nodes("W1")
    assert "P1" in up
    
    down = graph.get_downstream_nodes("P1")
    assert "W1" in down
