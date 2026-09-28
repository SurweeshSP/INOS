from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.data_models import Event, EventType

@dataclass
class ScenarioEvent(Event):
    event_id: str = ""
    seed: int = 42
    affected_nodes: List[str] = field(default_factory=list)
    affected_edges: List[str] = field(default_factory=list)
    delta_parameters: Dict[str, float] = field(default_factory=dict)
    expected_impact_class: str = "LOCAL"

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"{self.event_type.name}_{self.seed}"

class DemandShock(ScenarioEvent):
    def __init__(self, node_id: str, magnitude: float, time_period: int = 0, **kwargs):
        super().__init__(
            event_type=EventType.DEMAND_CHANGE,
            affected_nodes=[node_id],
            delta_parameters={f"demand_{node_id}_{time_period}": magnitude},
            **kwargs
        )
        self.affected_constraints.append(f"demand_meet_{node_id}_{time_period}")

class SupplyDisruption(ScenarioEvent):
    def __init__(self, node_id: str, capacity_reduction: float, time_period: int = 0, **kwargs):
        super().__init__(
            event_type=EventType.CAPACITY_CHANGE,
            affected_nodes=[node_id],
            delta_parameters={f"capacity_{node_id}_{time_period}": capacity_reduction},
            **kwargs
        )
        self.affected_constraints.append(f"cap_{node_id}_{time_period}")

class NetworkDisruption(ScenarioEvent):
    def __init__(self, edge_source: str, edge_target: str, capacity_reduction: float, time_period: int = 0, **kwargs):
        super().__init__(
            event_type=EventType.CAPACITY_CHANGE, # network capacity
            affected_edges=[f"{edge_source}->{edge_target}"],
            delta_parameters={f"cap_edge_{edge_source}_{edge_target}_{time_period}": capacity_reduction},
            **kwargs
        )
        self.affected_constraints.append(f"edge_cap_{edge_source}_{edge_target}_{time_period}")
