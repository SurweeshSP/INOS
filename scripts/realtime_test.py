import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

def wait_for_job(job_id: str, timeout: int = 10) -> dict:
    start_time = time.time()
    while time.time() - start_time < timeout:
        res = requests.get(f"{BASE_URL}/v1/jobs/{job_id}")
        if res.status_code == 200:
            status = res.json().get("status")
            if status == "COMPLETED":
                return requests.get(f"{BASE_URL}/v1/jobs/{job_id}/result").json()
            elif status == "FAILED":
                print(f"Job failed: {res.json()}")
                sys.exit(1)
        time.sleep(0.1)
    print("Timeout waiting for job")
    sys.exit(1)

def run_tests():
    print("=== SupplyChainOptii Real-Time API Test Harness ===")

    # Test 1: Static LP Solve
    print("\n[Test 1] Static LP Solve via JSON")
    lp_payload = {
        "model_type": "LP",
        "objective_sense": "minimize",
        "variables": [
            {"obj_coeff": -3.0},
            {"obj_coeff": -4.0}
        ],
        "constraints": [
            {"rhs": 14.0, "terms": [{"var_index": 0, "coeff": 1.0}, {"var_index": 1, "coeff": 2.0}]},
            {"rhs": 8.0, "terms": [{"var_index": 0, "coeff": 3.0}, {"var_index": 1, "coeff": -1.0}]}
        ],
        "options": {"method": "simplex"}
    }
    res = requests.post(f"{BASE_URL}/v1/solve", json=lp_payload)
    job_id = res.json()["job_id"]
    result = wait_for_job(job_id)
    print(f"Status: {result['solution']['status']}")
    print(f"Validated: {result['validation']['is_valid']}")
    assert result['validation']['is_valid'] == True
    
    model_id_lp = result["model_id"]

    # Test 3: Dynamic change
    print("\n[Test 3] Reoptimization (Parameter Change)")
    reopt_payload = {
        "model_id": model_id_lp,
        "events": [
            {
                "type": "capacity_change",
                "old_value": 14.0,
                "new_value": 15.0
            }
        ]
    }
    res = requests.post(f"{BASE_URL}/v1/reoptimize", json=reopt_payload)
    job_id = res.json()["job_id"]
    result = wait_for_job(job_id)
    print(f"Status: {result['solution']['status']}")
    print(f"Validated: {result['validation']['is_valid']}")
    assert result['validation']['is_valid'] == True

    # Test 6: Invalid solution
    print("\n[Test 6] Invalid solution validation detection")
    val_payload = {
        "model_id": model_id_lp,
        "solution": {
            "status": "OPTIMAL",
            "objective": -999.0,
            "variables": {"v0": 100.0, "v1": 100.0}
        }
    }
    res = requests.post(f"{BASE_URL}/v1/validate", json=val_payload)
    val_result = res.json()
    print(f"Is Valid? {val_result['is_valid']}")
    print(f"Primal Residual: {val_result['telemetry']['primal_residual']}")
    assert val_result['is_valid'] == False

    # Test 2 & 10: MPS Benchmark (flugpl)
    print("\n[Test 2 & 10] MPS Benchmark (flugpl)")
    res = requests.post(f"{BASE_URL}/v1/benchmark", json={"dataset": "netlib", "instance": "flugpl", "mode": "full"})
    if res.status_code == 200:
        bench = res.json()
        print(f"Status: {bench['status']}")
        print(f"Validated: {bench['validated']}")
        print(f"Solve Time: {bench['solve_ms']} ms")
    else:
        print(f"Benchmark failed: {res.text}")

    print("\n=== All Tests Completed Successfully ===")

if __name__ == "__main__":
    run_tests()
