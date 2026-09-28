import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_parameter_change_reoptimization():
    lp_payload = {
        "model_type": "LP",
        "objective_sense": "minimize",
        "variables": [{"obj_coeff": -3.0}, {"obj_coeff": -4.0}],
        "constraints": [
            {"rhs": 14.0, "terms": [{"var_index": 0, "coeff": 1.0}, {"var_index": 1, "coeff": 2.0}]}
        ],
        "options": {"method": "simplex"}
    }
    
    # 1. Initial Solve
    res = client.post("/v1/solve", json=lp_payload)
    data = res.json()
    job_id = data["job_id"]
    
    import time
    for _ in range(10):
        status_resp = client.get(f"/v1/jobs/{job_id}")
        if status_resp.json()["status"] == "COMPLETED":
            result = status_resp.json()["result"]
            break
        time.sleep(0.5)
    else:
        pytest.fail("Solve job did not complete")
    
    model_id = result["model_id"]
    
    # 2. Reoptimize
    reopt_payload = {
        "model_id": model_id,
        "events": [
            {
                "type": "capacity_change",
                "old_value": 14.0,
                "new_value": 15.0
            }
        ]
    }
    
    res2 = client.post("/v1/reoptimize", json=reopt_payload)
    data2 = res2.json()
    job_id2 = data2["job_id"]
    
    for _ in range(10):
        status_resp2 = client.get(f"/v1/jobs/{job_id2}")
        if status_resp2.json()["status"] == "COMPLETED":
            result2 = status_resp2.json()["result"]
            break
        time.sleep(0.5)
    else:
        pytest.fail("Reoptimize job did not complete")
    
    assert result2["solution"]["status"] == "OPTIMAL"
    assert result2["validation"]["is_valid"] == True
    # The ADS and fallback telemetry must be present
    assert result2["execution"]["strategy"] in ["adaptive_delta", "fallback"]

def test_structural_fallback_reoptimization():
    # Test that a structural event (e.g. ROUTE_BLOCKED) forces a fallback safely
    lp_payload = {
        "model_type": "LP",
        "objective_sense": "minimize",
        "variables": [{"obj_coeff": 1.0}, {"obj_coeff": 1.0}],
        "constraints": [
            {"rhs": 10.0, "terms": [{"var_index": 0, "coeff": 1.0}, {"var_index": 1, "coeff": 1.0}]}
        ],
        "options": {"method": "simplex"}
    }
    
    # 1. Initial Solve
    res = client.post("/v1/solve", json=lp_payload)
    job_id = res.json()["job_id"]
    
    import time
    for _ in range(10):
        status_resp = client.get(f"/v1/jobs/{job_id}")
        if status_resp.json()["status"] == "COMPLETED":
            result = status_resp.json()["result"]
            break
        time.sleep(0.5)
    else:
        pytest.fail("Solve job did not complete")
        
    model_id = result["model_id"]
    
    # 2. Reoptimize with structural change
    reopt_payload = {
        "model_id": model_id,
        "events": [
            {
                "type": "route_blocked",
                "old_value": 0.0,
                "new_value": 0.0
            }
        ]
    }
    
    res2 = client.post("/v1/reoptimize", json=reopt_payload)
    job_id2 = res2.json()["job_id"]
    
    for _ in range(10):
        status_resp2 = client.get(f"/v1/jobs/{job_id2}")
        print("Status resp2:", status_resp2.json())
        if status_resp2.json()["status"] == "COMPLETED":
            result2 = status_resp2.json()["result"]
            break
        time.sleep(0.5)
    else:
        pytest.fail("Reoptimize job did not complete")
    
    assert result2["solution"]["status"] == "OPTIMAL"
    assert result2["validation"]["is_valid"] == True
    
    # Assert fallback was triggered because of the structural event (unsupported by simple param delta)
    # Right now fallback_used should be True, or strategy should be fallback
    assert result2["execution"]["strategy"] == "fallback"
    assert result2["execution"]["fallback_used"] == True
