import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.benchmark.qplib_runner import QplibRunner

def main():
    runner = QplibRunner()
    
    # We will test on a very simple instance. Since download might fail, 
    # QplibLoader will automatically generate a fallback QPS for 'TEST_QP'.
    instances = ["TEST_QP"]
    
    runner.run_benchmark(instances)
    
if __name__ == "__main__":
    main()
