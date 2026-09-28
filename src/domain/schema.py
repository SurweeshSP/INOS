from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Supply:
    supplier: str
    product: str
    capacity: float

@dataclass
class Demand:
    customer: str
    product: str
    quantity: float

@dataclass
class Route:
    source: str
    target: str
    capacity: float
    cost: float

@dataclass
class Processing:
    input_product: str
    output_product: str
    capacity: float
    yield_rate: float
    cost: float

@dataclass
class Inventory:
    capacity: float
    holding_cost: float

@dataclass
class ObjectiveConfig:
    minimize: List[str] = field(default_factory=lambda: ["transportation_cost", "processing_cost", "inventory_cost", "shortage_cost"])

@dataclass
class GenericSupplyChainModel:
    domain: str
    nodes: Dict[str, List[str]] # e.g. {"suppliers": ["FARM_A", "FARM_B"], ...}
    products: List[str]
    supply: List[Supply]
    demand: List[Demand]
    routes: List[Route]
    processing: Optional[Dict[str, Processing]] = None  # keyed by node
    inventory: Optional[Dict[str, Inventory]] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    objective: ObjectiveConfig = field(default_factory=ObjectiveConfig)
