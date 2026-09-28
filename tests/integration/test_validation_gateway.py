import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_invalid_solution_detection():
    lp_payload = {
        "model_type": "LP",
        "objective_sense": "minimize",
        "variables": [{"obj_coeff": -3.0}, {"obj_coeff": -4.0}],
        "constraints": [
            {"rhs": 14.0, "terms": [{"var_index": 0, "coeff": 1.0}, {"var_index": 1, "coeff": 2.0}]}
        ],
        "options": {"method": "simplex"}
    }
    
    # 1. Initial Solve just to get the model into persistence
    res = client.post("/v1/solve", json=lp_payload)
    data = res.json()
    job_id = data["job_id"]
    result = client.get(f"/v1/jobs/{job_id}/result").json()
    model_id = result["model_id"]
    
    # 2. Forge a fake solution
    val_payload = {
        "model_id": model_id,
        "solution": {
            "status": "OPTIMAL",
            "objective": -999.0,
            "variables": {"v0": 100.0, "v1": 100.0} # This violently violates the Ax = b constraint (rhs=14)
        }
    }
    
    res2 = client.post("/v1/validate", json=val_payload)
    assert res2.status_code == 200
    val_result = res2.json()
    
    assert val_result["is_valid"] == False
    assert val_result["telemetry"]["primal_residual"] > 10.0 # 1*100 + 2*100 = 300 != 14 (residual 286)
