import io
import base64
from typing import List, Dict, Any, Optional
import networkx as nx
from src.data_models import OptimizationModel

class GraphVisualizer:
    @staticmethod
    def _create_graph_from_model(model: OptimizationModel) -> nx.DiGraph:
        G = nx.DiGraph()
        for var_name in model.variables:
            if var_name.startswith('flow_'):
                parts = var_name.split('_')
                if len(parts) >= 3:
                    u, v = parts[1], parts[2]
                    G.add_edge(u, v)
        return G

    @staticmethod
    def get_graph_data(model: OptimizationModel, entities: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        G = GraphVisualizer._create_graph_from_model(model)
        
        # Categorize nodes
        layers = {"supplier": [], "plant": [], "warehouse": [], "customer": []}
        
        if entities:
            # Use real entities to get all nodes
            for e in entities:
                ent_type = e.get('entity_type', '').lower()
                ids = e.get('ids')
                count = e.get('count')
                
                node_ids = []
                if ids and len(ids) > 0:
                    node_ids = ids
                elif count:
                    prefix = "S" if ent_type == "supplier" else "P" if ent_type == "plant" else "W" if ent_type == "warehouse" else "C" if ent_type == "customer" else "U"
                    node_ids = [f"{prefix}{str(i+1).zfill(3)}" for i in range(count)]
                    
                for node_id in node_ids:
                    if node_id.startswith("S"): layers["supplier"].append(node_id)
                    elif node_id.startswith("P"): layers["plant"].append(node_id)
                    elif node_id.startswith("W"): layers["warehouse"].append(node_id)
                    elif node_id.startswith("C"): layers["customer"].append(node_id)
        else:
            # Fallback
            for n in G.nodes():
                if n.startswith("S"): layers["supplier"].append(n)
                elif n.startswith("P"): layers["plant"].append(n)
                elif n.startswith("W"): layers["warehouse"].append(n)
                elif n.startswith("C"): layers["customer"].append(n)
            
        for k in layers:
            layers[k].sort()
            
        x_offsets = {"supplier": 100, "plant": 400, "warehouse": 700, "customer": 1000}
        
        nodes = []
        for type_str, node_list in layers.items():
            count = len(node_list)
            y_spacing = 800 / max(count, 1)
            for i, n in enumerate(node_list):
                nodes.append({
                    "id": n,
                    "type": type_str,
                    "position": {"x": x_offsets[type_str], "y": i * y_spacing + 50}
                })
        
        edges = []
        for u, v in G.edges():
            edges.append({"source": u, "target": v, "id": f"{u}_{v}"})
            
        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def generate_full_graph_base64(model: OptimizationModel, active_nodes: Optional[List[str]] = None, active_edges: Optional[List[str]] = None) -> str:
        return ""

    @staticmethod
    def generate_active_graph_base64(model: OptimizationModel, active_nodes: List[str], active_edges: List[str]) -> str:
        return ""
