from src.benchmark.runner import BenchmarkRunner

def main():
    print("Starting Netlib Benchmark Run (Milestone 1)...")
    runner = BenchmarkRunner(output_dir="results/netlib")
    subset = ["AFIRO", "ADLITTLE", "BLEND"]
    runner.run_netlib_subset(subset)
    print("Benchmark completed. Certificates generated in results/netlib/")

if __name__ == "__main__":
    main()
