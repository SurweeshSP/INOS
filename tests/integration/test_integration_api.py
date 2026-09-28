import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()

def test_static_lp_solve():
    lp_payload = {
        "model_type": "LP",
        "objective_sense": "minimize",
        "variables": [{"obj_coeff": -3.0}, {"obj_coeff": -4.0}],
        "constraints": [
            {"rhs": 14.0, "terms": [{"var_index": 0, "coeff": 1.0}, {"var_index": 1, "coeff": 2.0}]}
        ],
        "options": {"method": "simplex"}
    }
    
    # Send solve request
    res = client.post("/v1/solve", json=lp_payload)
    assert res.status_code == 200
    data = res.json()
    assert "job_id" in data
    
    # In integration tests using TestClient, BackgroundTasks execute sequentially after the response is sent.
    # Therefore, we can immediately fetch the result.
    res2 = client.get(f"/v1/jobs/{data['job_id']}")
    if res2.json()["status"] != "COMPLETED":
        print(f"Job Status: {res2.json()}")
        
    res2 = client.get(f"/v1/jobs/{data['job_id']}/result")
    assert res2.status_code == 200
    result = res2.json()
    
    assert result["solution"]["status"] == "OPTIMAL"
    assert result["validation"]["is_valid"] == True
