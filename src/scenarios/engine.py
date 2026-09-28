import random
from typing import List, Dict, Any, Optional
from src.data_models import OptimizationModel
from src.scenarios.events import ScenarioEvent, DemandShock, SupplyDisruption, NetworkDisruption

class ScenarioEngine:
    """
    Generates reproducible optimization changes (scenarios).
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(self.seed)

    def generate_scenario(self, 
                          family: str, 
                          full_model: OptimizationModel,
                          graph: Any) -> List[ScenarioEvent]:
        """
        S1 = highly local
        S2 = moderately local
        S3 = network-wide
        S4 = sparse random
        """
        events = []
        nodes = list(graph.nodes.keys())
        edges = list(graph.edges.keys())
        
        if not nodes:
            return events

        if family == "S1":
            # Highly local: 1 node demand shock
            node = self.rng.choice(nodes)
            magnitude = self.rng.uniform(10.0, 50.0)
            events.append(DemandShock(node_id=node, magnitude=magnitude, seed=self.seed))
            
        elif family == "S2":
            # Moderately local: 1 node demand shock, 1 nearby supply disruption
            node = self.rng.choice(nodes)
            magnitude = self.rng.uniform(10.0, 50.0)
            events.append(DemandShock(node_id=node, magnitude=magnitude, seed=self.seed))
            
            upstream = graph.get_upstream_nodes(node)
            if upstream:
                supplier = self.rng.choice(upstream)
                reduction = self.rng.uniform(-20.0, -5.0)
                events.append(SupplyDisruption(node_id=supplier, capacity_reduction=reduction, seed=self.seed))
                
        elif family == "S3":
            # Network-wide: 10% of nodes get demand shocks
            num_nodes = max(1, int(len(nodes) * 0.1))
            selected = self.rng.sample(nodes, num_nodes)
            for node in selected:
                magnitude = self.rng.uniform(5.0, 25.0)
                events.append(DemandShock(node_id=node, magnitude=magnitude, seed=self.seed, expected_impact_class="GLOBAL"))
                
        elif family == "S4":
            # Sparse random: random edges fail
            if edges:
                num_edges = max(1, int(len(edges) * 0.05))
                selected = self.rng.sample(edges, num_edges)
                for edge in selected:
                    src, tgt = edge.split("->")
                    events.append(NetworkDisruption(edge_source=src, edge_target=tgt, capacity_reduction=-100.0, seed=self.seed))
                    
        return events
