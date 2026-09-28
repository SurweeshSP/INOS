import time
import requests
import sys
import argparse
import os

API_URL = "http://127.0.0.1:8000"

def poll_job(job_id: str, timeout: int = 30):
    start_time = time.time()
    while time.time() - start_time < timeout:
        res = requests.get(f"{API_URL}/v1/jobs/{job_id}")
        res.raise_for_status()
        status = res.json().get("status")
        
        if status == "COMPLETED":
            return requests.get(f"{API_URL}/v1/jobs/{job_id}/result").json()
        elif status == "FAILED":
            print(f"Job failed: {res.json().get('error')}")
            sys.exit(1)
            
        time.sleep(0.5)
        
    print(f"Timeout waiting for job {job_id}")
    sys.exit(1)

def run_smoke_test():
    print("==========================================")
    print("END-TO-END SMOKE TEST")
    print("==========================================")
    
    # Check if server is up
    try:
        requests.get(f"{API_URL}/docs")
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to API at {API_URL}")
        sys.exit(1)
        
    # 1. Upload MPS (we use a simple local MPS file or a basic JSON payload)
    # Actually, let's use the standard JSON solve endpoint for simplicity in the smoke test,
    # to avoid needing a specific .mps file on disk.
    print("1. Submitting baseline LP solve...")
    lp_payload = {
        "model_type": "LP",
        "objective_sense": "minimize",
        "variables": [{"obj_coeff": 1.0}, {"obj_coeff": 2.0}],
        "constraints": [
            {"rhs": 10.0, "terms": [{"var_index": 0, "coeff": 1.0}, {"var_index": 1, "coeff": 1.0}]}
        ],
        "options": {"method": "simplex"}
    }
    
    res = requests.post(f"{API_URL}/v1/solve", json=lp_payload)
    res.raise_for_status()
    job_id = res.json()["job_id"]
    print(f"   Job ID: {job_id}")
    
    result = poll_job(job_id)
    model_id = result["model_id"]
    print(f"   Baseline solved successfully. Model ID: {model_id}")
    print(f"   Status: {result['solution']['status']}, Valid: {result['validation']['is_valid']}")
    
    # 2. Reoptimize Event (Parameter Delta)
    print("2. Submitting adaptive reoptimization event (CAPACITY_CHANGE)...")
    reopt_payload = {
        "model_id": model_id,
        "events": [
            {
                "type": "capacity_change",
                "old_value": 10.0,
                "new_value": 15.0
            }
        ]
    }
    
    res2 = requests.post(f"{API_URL}/v1/reoptimize", json=reopt_payload)
    res2.raise_for_status()
    job_id2 = res2.json()["job_id"]
    print(f"   Job ID: {job_id2}")
    
    result2 = poll_job(job_id2)
    print(f"   Reoptimization solved successfully.")
    print(f"   Strategy used: {result2['execution']['strategy']}")
    print(f"   Status: {result2['solution']['status']}, Valid: {result2['validation']['is_valid']}")
    
    # 3. Structural Reoptimize Event (Route Blocked) -> Fallback
    print("3. Submitting structural reoptimization event (ROUTE_BLOCKED) -> Fallback...")
    reopt_fallback_payload = {
        "model_id": result2["model_id"],
        "events": [
            {
                "type": "route_blocked",
                "old_value": 0.0,
                "new_value": 0.0
            }
        ]
    }
    
    res3 = requests.post(f"{API_URL}/v1/reoptimize", json=reopt_fallback_payload)
    res3.raise_for_status()
    job_id3 = res3.json()["job_id"]
    
    result3 = poll_job(job_id3)
    print(f"   Structural event handled successfully.")
    print(f"   Strategy used: {result3['execution']['strategy']}")
    print(f"   Fallback used: {result3['execution'].get('fallback_used', False)}")
    
    if result3["execution"]["strategy"] != "fallback":
        print("ERROR: Structural event did not trigger fallback.")
        sys.exit(1)
        
    print("==========================================")
    print("SMOKE TEST PASSED SUCCESSFULLY")
    print("==========================================")

if __name__ == "__main__":
    run_smoke_test()
