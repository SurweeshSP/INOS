import os
import json
import uuid
import time
from typing import Dict, Any, Optional
from src.data_models import OptimizationModel, ProblemType, VariableType
import numpy as np
import scipy.sparse as sp

MODELS_DIR = "data/runtime/models"

class ModelService:
    def __init__(self):
        os.makedirs(MODELS_DIR, exist_ok=True)

    def generate_model_id(self) -> str:
        return f"model_{uuid.uuid4().hex[:8]}"

    def build_from_json(self, req_data: Dict[str, Any]) -> OptimizationModel:
        model = OptimizationModel(
            problem_type=ProblemType[req_data.get("model_type", "LP").upper()]
        )
        
        n = len(req_data["variables"])
        m = len(req_data["constraints"])
        
        c = np.zeros(n)
        lower_bounds = np.zeros(n)
        upper_bounds = np.full(n, np.inf)
        variable_types = np.full(n, VariableType.CONTINUOUS)
        
        for i, var in enumerate(req_data["variables"]):
            c[i] = var.get("obj_coeff", 0.0)
            if "lower_bound" in var: lower_bounds[i] = var["lower_bound"]
            if "upper_bound" in var: upper_bounds[i] = var["upper_bound"]
            
            vtype = var.get("type", "CONTINUOUS").upper()
            if vtype == "INTEGER":
                variable_types[i] = VariableType.INTEGER
            elif vtype == "BINARY":
                variable_types[i] = VariableType.BINARY
                
        model.c = c
        model.lower_bounds = lower_bounds
        model.upper_bounds = upper_bounds
        model.variable_types = variable_types
        
        b = np.zeros(m)
        rows, cols, data = [], [], []
        
        for j, const in enumerate(req_data["constraints"]):
            b[j] = const.get("rhs", 0.0)
            # Simplification: assume all equality for Phase 1 JSON standard form as per solver
            for term in const.get("terms", []):
                rows.append(j)
                cols.append(term["var_index"])
                data.append(term["coeff"])
                
        if len(data) > 0:
            model.A = sp.csr_matrix((data, (rows, cols)), shape=(m, n))
        else:
            model.A = sp.csr_matrix((m, n))
            
        model.b = b
        return model

    def save_model(self, model_id: str, model: OptimizationModel, state: Any = None):
        path = os.path.join(MODELS_DIR, f"{model_id}.json")
        
        # Serialize metadata (we don't serialize full A/b/c here to save space in this demo,
        # but in production we'd pickle the scipy matrix or write to a binary blob).
        meta = {
            "model_id": model_id,
            "created_at": time.time(),
            "variables": int(len(model.c)) if model.c is not None else 0,
            "constraints": int(len(model.b)) if model.b is not None else 0,
            "nonzeros": int(model.A.nnz) if model.A is not None else 0,
            "integer_variables": int(np.sum(model.variable_types == VariableType.INTEGER)) if hasattr(model, 'variable_types') and model.variable_types is not None else 0,
            "binary_variables": int(np.sum(model.variable_types == VariableType.BINARY)) if hasattr(model, 'variable_types') and model.variable_types is not None else 0,
        }
        with open(path, "w") as f:
            json.dump(meta, f, indent=2)
            
        # We'll just cache it in memory for this fast realtime test
        if not hasattr(self, "_cache"):
            self._cache = {}
        self._cache[model_id] = (model, state)

    def load_model(self, model_id: str) -> Optional[OptimizationModel]:
        if hasattr(self, "_cache") and model_id in self._cache:
            return self._cache[model_id][0]
        return None

    def load_state(self, model_id: str) -> Optional[Any]:
        if hasattr(self, "_cache") and model_id in self._cache:
            return self._cache[model_id][1]
        return None

model_service = ModelService()
