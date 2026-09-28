import pytest
from pathlib import Path
from src.data_loader import load_instance
from src.data_models import ProblemType, VariableType, ConstraintSense

def test_load_json_instance():
    fixture_path = Path("tests/fixtures/dummy.json")
    model = load_instance(fixture_path)
    
    assert model.problem_type == ProblemType.LP
    assert "x1" in model.variables
    assert model.variables["x1"].var_type == VariableType.CONTINUOUS
    assert model.variables["x1"].ub == 10.0
    assert model.variables["x1"].obj_coef == 2.5
    
    assert "c1" in model.constraints
    assert model.constraints["c1"].sense == ConstraintSense.LE
    assert model.constraints["c1"].rhs == 5.0

def test_load_missing_file():
    with pytest.raises(FileNotFoundError):
        load_instance("nonexistent_file.json")
