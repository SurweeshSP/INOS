from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class EntitySpec(BaseModel):
    entity_type: str
    count: Optional[int] = None
    ids: Optional[List[str]] = None

class BusinessProblemInput(BaseModel):
    goal: str
    entities: List[EntitySpec] = []
    data_files: List[str] = []
    constraints: List[str] = []
    decisions: List[str] = []
    planning_horizon: int = 14
    time_unit: str = "days"
    scenario: str = "normal"
    description: Optional[str] = None
    execution_mode: Optional[str] = "full"

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None
    progress: Optional[str] = None
    problem_summary: Optional[Dict[str, Any]] = None

class BusinessEventRequest(BaseModel):
    problem_id: str
    command: str

class OptimizationStatus(BaseModel):
    status: str
    objective: Optional[float] = None
    objective_unit: str = "USD"
    runtime_seconds: float = 0.0
    mip_gap: Optional[float] = None
    variables: int = 0
    constraints: int = 0
    violations: List[str] = []
    solver: str = ""
    validation_status: str = "PENDING"

class ExplanationBlock(BaseModel):
    trigger: str = ""
    changed_entities: List[str] = []
    changed_variables: List[str] = []
    changed_constraints: List[str] = []
    active_nodes: List[str] = []
    active_edges: List[str] = []
    active_paths: List[str] = []
    why_chain: List[str] = []

class ScenarioMetrics(BaseModel):
    base_objective: float = 0.0
    scenario_objective: float = 0.0
    objective_delta: float = 0.0
    affected_subgraphs: int = 0
    new_bottlenecks: int = 0
    additional_transport_units: float = 0.0

class VisualizationPackage(BaseModel):
    graph_image: Optional[str] = None
    active_graph_image: Optional[str] = None

class DiagnosticInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_version: str = ""
    event_id: str = ""
    active_region_ratio: float = 0.0
    active_variable_ratio: float = 0.0
    active_constraint_ratio: float = 0.0
    expansion_count: int = 0
    fallback_used: bool = False
    validation_status: str = "PENDING"
    solver_status: str = "UNKNOWN"

class DecisionPackage(BaseModel):
    optimization: OptimizationStatus = OptimizationStatus(status="NOT_SOLVED")
    production_plan: List[Dict[str, Any]] = []
    transportation_plan: List[Dict[str, Any]] = []
    inventory_plan: List[Dict[str, Any]] = []
    bottlenecks: List[Dict[str, Any]] = []
    explanation: ExplanationBlock = ExplanationBlock()
    scenario: ScenarioMetrics = ScenarioMetrics()
    visualization: VisualizationPackage = VisualizationPackage()
    diagnostics: DiagnosticInfo = DiagnosticInfo()
