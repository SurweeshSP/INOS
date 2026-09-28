import json
from pathlib import Path
from typing import Dict, List, Any

from src.data_models import (
    OptimizationModel,
    ProblemType,
    VariableMeta,
    VariableType,
    ConstraintMeta,
    ConstraintSense,
    Event,
    EventType,
    Scenario
)

def load_dynamic_scenario(filepath: Path) -> OptimizationModel:
    """Parses a dynamic .txt (JSON format) scenario into an OptimizationModel."""
    model = OptimizationModel(problem_type=ProblemType.LP)
    
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    # Build a basic optimization model based on sets C, I, K etc.
    # In a real implementation this would build the transportation constraints.
    # For Phase 15A we just need it to be a valid OptimizationModel.
    
    customers = data.get('C', [])
    items = data.get('I', [])
    
    # Just create some dummy variables and constraints to represent the scenario structure
    for c in customers:
        for i in items:
            var_name = f"flow_{c}_{i}"
            model.variables[var_name] = VariableMeta(name=var_name, var_type=VariableType.CONTINUOUS, obj_coef=1.0)
            
    # Dummy capacity constraint
    c_name = "capacity_limit"
    model.constraints[c_name] = ConstraintMeta(name=c_name, sense=ConstraintSense.LE, rhs=1000.0)
    
    return model
