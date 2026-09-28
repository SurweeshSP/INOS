import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.benchmarks.dataset_inspector import DatasetInspector

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    inspector = DatasetInspector(data_dir=data_dir)
    print("Inspecting internal dataset formats...")
    inspector.scan_all()
    print(f"Inspected {len(inspector.results)} files.")
    
    csv_out = "results/datasets/dataset_inventory_real.csv"
    md_out = "reports/MIPLIB_FORMAT_ANALYSIS.md"
    
    inspector.save_csv(csv_out)
    inspector.generate_miplib_report(md_out)
    
    print(f"Saved: {csv_out}")
    print(f"Saved: {md_out}")
    
if __name__ == "__main__":
    main()
