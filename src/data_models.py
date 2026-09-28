from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union

# Enums

class ProblemType(Enum):
    LP = auto()
    MILP = auto()
    QP = auto()

class VariableType(Enum):
    CONTINUOUS = auto()
    INTEGER = auto()
    BINARY = auto()

class ConstraintSense(Enum):
    LE = auto()  # <=
    EQ = auto()  # ==
    GE = auto()  # >=

class EventType(Enum):
    DEMAND_CHANGE = auto()
    CAPACITY_CHANGE = auto()
    COST_CHANGE = auto()
    ROUTE_BLOCKED = auto()
    ROUTE_RESTORED = auto()
    FACILITY_DOWN = auto()
    FACILITY_RESTORED = auto()
    NEW_ORDER = auto()
    CANCELLATION = auto()
    SUPPLY_CHANGE = auto()
    SERVICE_CHANGE = auto()
    INVENTORY_SHOCK = auto()
    MULTI_EVENT = auto()

class NodeType(Enum):
    SUPPLIER = auto()
    PLANT = auto()
    WAREHOUSE = auto()
    DC = auto()
    CUSTOMER = auto()
    PORT = auto()
    MARKET = auto()

class EdgeType(Enum):
    SUPPLY = auto()
    PRODUCTION = auto()
    TRANSPORT = auto()
    SHIPMENT = auto()
    FLOW = auto()
    DEPENDENCY = auto()

class ConstraintRole(Enum):
    CAPACITY = auto()
    FLOW_BALANCE = auto()
    INVENTORY_BALANCE = auto()
    DEMAND_FULFILLMENT = auto()
    SERVICE = auto()
    LINKING = auto()
    OTHER = auto()

class SolveStatus(Enum):
    OPTIMAL = auto()
    INFEASIBLE = auto()
    UNBOUNDED = auto()
    SUBOPTIMAL = auto()
    ERROR = auto()
    NOT_SOLVED = auto()

class AlgorithmType(Enum):
    SIMPLEX = auto()
    INTERIOR_POINT = auto()
    BRANCH_AND_BOUND = auto()

# Dataclasses

@dataclass
class VariableMeta:
    name: str
    var_type: VariableType
    lb: float = 0.0
    ub: float = float('inf')
    obj_coef: float = 0.0

@dataclass
class ConstraintMeta:
    name: str
    sense: ConstraintSense
    rhs: float
    role: ConstraintRole = ConstraintRole.OTHER

@dataclass
class NodeMeta:
    id: str
    node_type: NodeType
    capacity: Optional[float] = None
    inventory: Optional[float] = None
    demand: Optional[float] = None

@dataclass
class EdgeMeta:
    source: str
    target: str
    edge_type: EdgeType
    capacity: Optional[float] = None
    cost: Optional[float] = None
    lead_time: Optional[float] = None

@dataclass
class OptimizationModel:
    problem_type: ProblemType
    variables: Dict[str, VariableMeta] = field(default_factory=dict)
    constraints: Dict[str, ConstraintMeta] = field(default_factory=dict)
    # Storing matrix structure abstractly here
    A: Any = None  # Placeholder for sparse matrix (csr_matrix)
    b: Any = None  # Placeholder for 1D array
    c: Any = None  # Placeholder for 1D array
    Q: Any = None  # Placeholder for sparse quadratic objective matrix (csr_matrix)
    lower_bounds: Any = None  # Placeholder for 1D array
    upper_bounds: Any = None  # Placeholder for 1D array
    senses: Any = None  # List or array of senses ('E', 'L', 'G')
    objective_offset: float = 0.0  # Constant shift for the objective value

    @property
    def bounds(self):
        if self.lower_bounds is None or self.upper_bounds is None:
            return None
        import numpy as np
        return list(zip(self.lower_bounds, self.upper_bounds))
        
    @bounds.setter
    def bounds(self, value):
        if value is None:
            self.lower_bounds = None
            self.upper_bounds = None
            return
        import numpy as np
        self.lower_bounds = np.array([v[0] for v in value], dtype=float)
        self.upper_bounds = np.array([v[1] for v in value], dtype=float)

@dataclass
class SolutionRecord:
    status: SolveStatus
    objective_value: Optional[float] = None
    primal_values: Dict[str, float] = field(default_factory=dict)
    dual_values: Dict[str, float] = field(default_factory=dict)
    variables: Any = None
    
    # Phase 16 execution and warm-start metrics
    warm_start_requested: bool = False
    warm_start_used: bool = False
    warm_start_valid: bool = False
    warm_start_rejected: bool = False
    warm_start_reason: str = ""
    
    iterations: int = 0
    runtime: float = 0.0
    constraint_residual: float = 0.0
    bound_violation: float = 0.0
    integrality_violation: float = 0.0

@dataclass
class SupplyChainState:
    nodes: Dict[str, NodeMeta] = field(default_factory=dict)
    edges: Dict[str, EdgeMeta] = field(default_factory=dict)

@dataclass
class Event:
    event_type: EventType
    affected_entities: List[str] = field(default_factory=list)
    affected_variables: List[str] = field(default_factory=list)
    affected_constraints: List[str] = field(default_factory=list)
    affected_periods: List[int] = field(default_factory=list)
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    magnitude: float = 0.0

@dataclass
class Scenario:
    base_instance_id: str
    scenario_id: str
    event: Event
    changed_parameters: Dict[str, Any] = field(default_factory=dict)
    random_seed: int = 42
    full_solve_result: Optional[SolutionRecord] = None
    adaptive_result: Optional[SolutionRecord] = None

@dataclass
class PersistentOptimizationState:
    model_version: str
    entities: List[Dict[str, Any]] = field(default_factory=list)
    previous_solution: Optional[SolutionRecord] = None
    objective: Optional[float] = None
    feasibility: bool = False
    optimality: bool = False
    warm_start: Any = None
    incumbent: Any = None
    basis: Any = None
    lp_relaxation_state: Any = None
    cut_metadata: Any = None
    node_statistics: Any = None
    variable_activity: Any = None
    constraint_activity: Any = None
    sensitivity: Any = None
    event_history: List[Event] = field(default_factory=list)
    solve_history: List[SolutionRecord] = field(default_factory=list)

@dataclass
class BoundaryCondition:
    variable_name: str
    fixed_value: float

@dataclass
class ActiveRegion:
    nodes: List[str] = field(default_factory=list)
    edges: List[str] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    boundary_conditions: List[BoundaryCondition] = field(default_factory=list)

@dataclass
class HarnessFeatures:
    problem_type: ProblemType
    n: int
    m: int
    nnz: int
    density: float
    integer_fraction: float
    binary_fraction: float
    active_fraction: float

@dataclass
class HarnessDecision:
    algorithm: AlgorithmType
    cpu_gpu: str
    presolve: bool
    warm_start_policy: str
    explanation: str

@dataclass
class SolverTelemetry:
    solve_time: float
    iterations: int
    nodes: int
    mip_gap: Optional[float]

@dataclass
class ExperienceRecord:
    features: HarnessFeatures
    decision: HarnessDecision
    telemetry: SolverTelemetry

@dataclass
class InputRequest:
    request_id: str
    application: str
    user_role: str
    objective: str
    horizon: int
    entities: List[str] = field(default_factory=list)
    products: List[str] = field(default_factory=list)
    demand: Dict[str, Any] = field(default_factory=dict)
    capacity: Dict[str, Any] = field(default_factory=dict)
    costs: Dict[str, Any] = field(default_factory=dict)
    routes: Dict[str, Any] = field(default_factory=dict)
    inventory: Dict[str, Any] = field(default_factory=dict)
    service_targets: Dict[str, Any] = field(default_factory=dict)
    constraints: Dict[str, Any] = field(default_factory=dict)
    events: List[Event] = field(default_factory=list)
    scenario_parameters: Dict[str, Any] = field(default_factory=dict)
    uncertainty_parameters: Dict[str, Any] = field(default_factory=dict)
    requested_outputs: List[str] = field(default_factory=list)

@dataclass
class ValidationResult:
    is_valid: bool
    violations: List[str] = field(default_factory=list)
