import pytest
from src.api.schemas import SolveOptionsSchema, SolveRequestSchema, ReoptimizeRequestSchema, ValidateRequestSchema, SolveResponseSchema
from src.api.v2_schemas import DiagnosticInfo

def test_pydantic_field_serialization():
    # Test SolveOptionsSchema "validate" mapping
    options = SolveOptionsSchema(validate=True, method="highs")
    assert getattr(options, 'validate_') is True
    # Test JSON dump retains "validate"
    dump = options.model_dump(by_alias=True)
    assert "validate" in dump
    assert dump["validate"] is True
    
    # Test SolveRequestSchema
    req = SolveRequestSchema(
        model_type="MILP",
        objective_sense="maximize",
        variables=[],
        constraints=[],
        options=options
    )
    assert req.model_type == "MILP"
    req_dump = req.model_dump()
    assert "model_type" in req_dump
    
    # Test ReoptimizeRequestSchema
    re_req = ReoptimizeRequestSchema(
        model_id="model-123",
        events=[]
    )
    assert re_req.model_id == "model-123"
    
    # Test DiagnosticInfo
    diag = DiagnosticInfo(model_version="v2")
    assert diag.model_version == "v2"
    diag_dump = diag.model_dump()
    assert "model_version" in diag_dump
