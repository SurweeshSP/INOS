from src.benchmark.miplib_runner import MiplibRunner

def main():
    print("Starting MIPLIB Benchmark Run (Phase 7)...")
    runner = MiplibRunner()
    
    # We will use the embedded fallback to test the integration end-to-end
    subset = ["test_mip"]
    runner.run_miplib_subset(subset)
    
    print("Benchmark completed. Certificates generated in results/miplib/")

if __name__ == "__main__":
    main()
