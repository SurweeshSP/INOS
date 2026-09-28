from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from src.data_models import VariableType

class EventSchema(BaseModel):
    type: str
    resource: Optional[str] = None
    old_value: float
    new_value: float

class SolveOptionsSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    method: str = "auto"
    use_adaptive: bool = True
    use_warm_start: bool = True
    validate_: bool = Field(default=True, alias="validate")
    node_limit: Optional[int] = None

class SolveRequestSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_type: str = "LP"
    objective_sense: str = "minimize"
    variables: List[Dict[str, Any]]
    constraints: List[Dict[str, Any]]
    events: List[EventSchema] = []
    options: SolveOptionsSchema = SolveOptionsSchema()

class ReoptimizeRequestSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    events: List[EventSchema]
    options: SolveOptionsSchema = SolveOptionsSchema()

class ValidationTelemetrySchema(BaseModel):
    is_valid: bool
    primal_residual: float = 0.0
    bound_violation: float = 0.0
    integrality_violation: float = 0.0
    objective_recomputed: Optional[float] = None

class ExecutionTelemetrySchema(BaseModel):
    solver: str
    strategy: str
    ads_initial_size: int = 0
    ads_final_size: int = 0
    expansions: int = 0
    fallback_used: bool = False
    runtime_ms: float

class ModelTelemetrySchema(BaseModel):
    variables: int
    constraints: int
    nonzeros: int
    integer_variables: int
    binary_variables: int

class SolutionSchema(BaseModel):
    status: str
    objective: Optional[float] = None
    variables: Optional[Dict[str, float]] = None

class JobResponseSchema(BaseModel):
    job_id: str
    status: str

class ValidateRequestSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str
    solution: SolutionSchema

class ValidateResponseSchema(BaseModel):
    is_valid: bool
    telemetry: ValidationTelemetrySchema

class SolveResponseSchema(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    job_id: str
    model_id: Optional[str] = None
    model: Optional[ModelTelemetrySchema] = None
    execution: Optional[ExecutionTelemetrySchema] = None
    solution: Optional[SolutionSchema] = None
    validation: Optional[ValidationTelemetrySchema] = None

class BenchmarkRequestSchema(BaseModel):
    dataset: Optional[str] = "netlib"
    instance: Optional[str] = None
    mode: str = "full"

class BenchmarkResponseSchema(BaseModel):
    instance: str
    parse_ms: float
    solve_ms: float
    variables: int
    constraints: int
    nonzeros: int
    integer_variables: int
    status: str
    validated: bool
