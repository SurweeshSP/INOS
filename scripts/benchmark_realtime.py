import time
import requests
import argparse
import sys

API_URL = "http://127.0.0.1:8000"

def run_benchmark(dataset: str, instance: str):
    print(f"Benchmarking instance: {instance} from dataset: {dataset}")
    
    payload = {
        "dataset": dataset,
        "instance": instance
    }
    
    t0 = time.time()
    try:
        res = requests.post(f"{API_URL}/v1/benchmark", json=payload)
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {API_URL}. Is the server running?")
        sys.exit(1)
    except Exception as e:
        print(f"Error executing benchmark request: {e}")
        if 'res' in locals():
            print(res.text)
        sys.exit(1)
        
    req_ms = (time.time() - t0) * 1000.0
    data = res.json()
    
    print("\n" + "="*40)
    print(f"BENCHMARK RESULT: {instance} ({dataset})")
    print("="*40)
    print(f"Variables:          {data['variables']} ({data['integer_variables']} integer)")
    print(f"Constraints:        {data['constraints']}")
    print(f"Nonzeros:           {data['nonzeros']}")
    print("-" * 40)
    print(f"Parse Time:         {data['parse_ms']:.2f} ms")
    print(f"Solve Time:         {data['solve_ms']:.2f} ms")
    print(f"Total API Latency:  {req_ms:.2f} ms")
    print(f"Status:             {data['status']}")
    print(f"Validated:          {data['validated']}")
    print("="*40 + "\n")
    
    return data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="netlib")
    parser.add_argument("--instance", type=str, required=True)
    args = parser.parse_args()
    
    run_benchmark(args.dataset, args.instance)
