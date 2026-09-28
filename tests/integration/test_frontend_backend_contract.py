import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_frontend_backend_contract():
    # 1. Test POST /v2/problem
    problem_payload = {
        "goal": "minimize_cost",
        "entities": [
            {"entity_type": "supplier", "count": 2},
            {"entity_type": "plant", "count": 1},
            {"entity_type": "warehouse", "count": 1},
            {"entity_type": "customer", "count": 3}
        ],
        "data_files": ["uploaded_files_mock"],
        "constraints": [],
        "decisions": ["production", "transportation", "inventory"],
        "planning_horizon": 14,
        "time_unit": "days",
        "scenario": "normal"
    }

    response = client.post("/v2/problem", json=problem_payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code} with body: {response.text}"
    
    job_id = response.json()["job_id"]
    import time
    for _ in range(10):
        status_resp = client.get(f"/v2/jobs/{job_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data["status"] == "READY":
            data = status_data["problem_summary"]
            break
        time.sleep(0.5)
    else:
        pytest.fail("Job did not complete in time")
    
    assert "problem_id" in data
    assert "model_version" in data
    assert "variables" in data
    assert "constraints" in data
    
    problem_id = data["problem_id"]

    # 2. Test GET /v2/graph/{problem_id}
    graph_response = client.get(f"/v2/graph/{problem_id}")
    assert graph_response.status_code == 200
    assert "graph_image" in graph_response.json()
    
    # 3. Test GET /v2/state/{problem_id}
    state_response = client.get(f"/v2/state/{problem_id}")
    assert state_response.status_code == 200
    state_data = state_response.json()
    assert "model_version" in state_data
    assert "objective" in state_data
    
    # 3.5. Optimize Baseline
    opt_resp = client.post("/v2/optimize", json={"problem_id": problem_id})
    assert opt_resp.status_code == 200
    
    # 4. Test POST /v2/reoptimize
    reopt_payload = {
        "problem_id": problem_id,
        "command": "Decrease S01 capacity by 20%"
    }
    reopt_response = client.post("/v2/reoptimize", json=reopt_payload)
    assert reopt_response.status_code == 200, f"Expected 200, got {reopt_response.status_code} with body: {reopt_response.text}"
    
    reopt_data = reopt_response.json()
    assert "scenario" in reopt_data
    assert "optimization" in reopt_data
    assert "explanation" in reopt_data
    assert "visualization" in reopt_data
    assert "diagnostics" in reopt_data
    
    print("Contract test passed successfully!")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
