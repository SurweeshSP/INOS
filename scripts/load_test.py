import asyncio
import time
import argparse
import httpx

API_URL = "http://127.0.0.1:8000"

async def submit_job(client: httpx.AsyncClient, dataset: str, instance: str, job_idx: int):
    payload = {"dataset": dataset, "instance": instance}
    result = {
        "latency": 0.0, "http_status": 0,
        "solver_success": False, "validation_success": False,
        "parser_failure": False, "timeout": False, "error": None
    }
    try:
        t0 = time.time()
        response = await client.post(f"{API_URL}/v1/benchmark", json=payload, timeout=60.0)
        result["latency"] = (time.time() - t0) * 1000.0
        result["http_status"] = response.status_code
        
        data = response.json()
        if response.status_code == 200:
            status = data.get("status")
            if status == "OPTIMAL":
                result["solver_success"] = True
            if data.get("validated") is True:
                result["validation_success"] = True
        elif response.status_code == 422:
            err = data.get("error", {})
            if err.get("stage") == "parser":
                result["parser_failure"] = True
            result["error"] = err.get("message")
            
        return result
    except httpx.TimeoutException:
        result["timeout"] = True
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

async def run_load_test(dataset: str, instance: str, concurrency: int, total_requests: int):
    print(f"==========================================")
    print(f"REAL-TIME LOAD TEST")
    print(f"==========================================")
    print(f"Dataset:      {dataset}")
    print(f"Instance:     {instance}")
    print(f"Concurrency:  {concurrency}")
    print(f"Requests:     {total_requests}")
    print(f"Target API:   {API_URL}")
    print(f"==========================================\n")
    
    sem = asyncio.Semaphore(concurrency)
    
    async def worker(client, idx):
        async with sem:
            return await submit_job(client, dataset, instance, idx)
            
    t0 = time.time()
    async with httpx.AsyncClient() as client:
        tasks = [worker(client, i) for i in range(total_requests)]
        results = await asyncio.gather(*tasks)
        
    total_time = (time.time() - t0) * 1000.0
    
    http_2xx = sum(1 for r in results if 200 <= r["http_status"] < 300)
    http_4xx = sum(1 for r in results if 400 <= r["http_status"] < 500)
    http_5xx = sum(1 for r in results if 500 <= r["http_status"] < 600)
    
    solver_successes = sum(1 for r in results if r["solver_success"])
    validation_successes = sum(1 for r in results if r["validation_success"])
    parser_failures = sum(1 for r in results if r["parser_failure"])
    timeouts = sum(1 for r in results if r["timeout"])
    
    latencies = [r["latency"] for r in results if r["latency"] > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    
    print("\n==========================================")
    print(f"LOAD TEST RESULTS")
    print("==========================================")
    print(f"Total Time:             {total_time:.2f} ms")
    print(f"Total Requests:         {total_requests}")
    print(f"HTTP Successes (2xx):   {http_2xx}")
    print(f"HTTP Client Err (4xx):  {http_4xx}")
    print(f"HTTP Server Err (5xx):  {http_5xx}")
    print(f"Solver Successes:       {solver_successes}")
    print(f"Validation Successes:   {validation_successes}")
    print(f"Parser Failures:        {parser_failures}")
    print(f"Timeouts:               {timeouts}")
    print(f"Avg Latency:            {avg_latency:.2f} ms")
    print(f"Throughput:             {(total_requests / (total_time/1000.0)):.2f} req/s")
    print("==========================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="netlib")
    parser.add_argument("--instance", type=str, required=True)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--requests", type=int, default=20)
    args = parser.parse_args()
    
    asyncio.run(run_load_test(args.dataset, args.instance, args.concurrency, args.requests))
