import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_problem():
    payload = {
        "goal": "Minimize cost",
        "entities": [
            {"entity_type": "supplier", "count": 2},
            {"entity_type": "plant", "count": 3},
            {"entity_type": "warehouse", "count": 2},
            {"entity_type": "customer", "count": 4}
        ],
        "planning_horizon": 2
    }
    response = client.post("/v2/problem", json=payload)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    import time
    for _ in range(10):
        status_resp = client.get(f"/v2/jobs/{job_id}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        if status_data["status"] == "READY":
            summary = status_data["problem_summary"]
            # Call optimize to establish the baseline state
            opt_resp = client.post("/v2/optimize", json={"problem_id": summary["problem_id"]})
            assert opt_resp.status_code == 200
            return summary
        time.sleep(0.5)
        
    pytest.fail("Job did not complete in time")

def test_a_static_business_model(setup_problem):
    data = setup_problem
    assert "problem_id" in data
    assert data["variables"] > 0
    assert data["constraints"] > 0
    assert data["solver_readiness"] == "READY"
    assert "graph_image" in data

def test_b_capacity_change(setup_problem):
    problem_id = setup_problem["problem_id"]
    payload = {
        "problem_id": problem_id,
        "command": "increase W01 capacity by 20%"
    }
    resp = client.post("/v2/reoptimize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["explanation"]["trigger"].startswith("Event CAPACITY_CHANGE")
    assert data["optimization"]["validation_status"] == "VALIDATED"
    # Fallback should be false for a simple capacity change
    assert data["diagnostics"]["fallback_used"] == False

def test_c_demand_change(setup_problem):
    problem_id = setup_problem["problem_id"]
    payload = {
        "problem_id": problem_id,
        "command": "increase C01 demand by 15%"
    }
    resp = client.post("/v2/reoptimize", json=payload)
    assert resp.status_code == 200
    assert resp.json()["optimization"]["validation_status"] == "VALIDATED"

def test_d_plant_outage(setup_problem):
    problem_id = setup_problem["problem_id"]
    payload = {
        "problem_id": problem_id,
        "command": "P02 is unavailable tomorrow"
    }
    resp = client.post("/v2/reoptimize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["explanation"]["trigger"].startswith("Event FACILITY_DOWN")
    assert data["optimization"]["validation_status"] == "VALIDATED"

def test_e_cost_change(setup_problem):
    problem_id = setup_problem["problem_id"]
    payload = {
        "problem_id": problem_id,
        "command": "increase P01->W01 cost by 10%"
    }
    resp = client.post("/v2/reoptimize", json=payload)
    assert resp.status_code == 200
    assert resp.json()["optimization"]["validation_status"] == "VALIDATED"

def test_f_route_failure(setup_problem):
    problem_id = setup_problem["problem_id"]
    payload = {
        "problem_id": problem_id,
        "command": "block route P01->W01"
    }
    resp = client.post("/v2/reoptimize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["explanation"]["trigger"].startswith("Event ROUTE_BLOCKED")
    assert data["optimization"]["validation_status"] == "VALIDATED"
    # Structural failures should trigger fallback
    assert data["diagnostics"]["fallback_used"] == True

def test_g_lead_time_change(setup_problem):
    problem_id = setup_problem["problem_id"]
    payload = {
        "problem_id": problem_id,
        "command": "increase lead time P01->W01 by 2 days"
    }
    resp = client.post("/v2/reoptimize", json=payload)
    assert resp.status_code == 200
    assert resp.json()["optimization"]["validation_status"] == "VALIDATED"

def test_h_sequential_events(setup_problem):
    problem_id = setup_problem["problem_id"]
    
    # 1. demand increase
    client.post("/v2/reoptimize", json={"problem_id": problem_id, "command": "increase C02 demand by 10%"})
    # 2. capacity decrease
    client.post("/v2/reoptimize", json={"problem_id": problem_id, "command": "increase W02 capacity by -10%"})
    # 3. route block
    resp = client.post("/v2/reoptimize", json={"problem_id": problem_id, "command": "block route P02->W02"})
    
    data = resp.json()
    assert data["optimization"]["validation_status"] == "VALIDATED"
    assert data["diagnostics"]["fallback_used"] == True

def test_i_invalid_candidate(setup_problem, monkeypatch):
    problem_id = setup_problem["problem_id"]
    
    # Mock global validator to simulate an invalid candidate rejection
    from src.service.validation_service import ValidationService
    original_validate = ValidationService.validate_solution
    
    def mock_validate(self, model, solution):
        from src.api.schemas import ValidationTelemetrySchema
        return ValidationTelemetrySchema(
            is_valid=False, primal_residual=100.0, bound_violation=0.0, integrality_violation=0.0
        )
        
    monkeypatch.setattr(ValidationService, "validate_solution", mock_validate)
    
    # The DeltaReoptimizationOrchestrator will try to solve, validation will fail, 
    # it will try fallback, and fallback validation will also fail.
    # The output should not say VALIDATED.
    
    payload = {
        "problem_id": problem_id,
        "command": "increase W01 capacity by 20%"
    }
    
    resp = client.post("/v2/reoptimize", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    
    # It must not falsely claim validated if the validator rejected it
    assert data["optimization"]["validation_status"] == "FAILED"
