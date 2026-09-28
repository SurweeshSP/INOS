import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.benchmarks.dataset_inventory import DatasetInventory

def main():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    inventory = DatasetInventory(data_dir=data_dir)
    print("Scanning datasets...")
    records = inventory.scan()
    print(f"Found {len(records)} instance files.")
    
    # Save outputs
    inventory.save_json("results/datasets/dataset_inventory.json")
    inventory.save_csv("results/datasets/dataset_inventory.csv")
    inventory.generate_markdown("reports/DATASET_INVENTORY.md")
    
    print("Saved inventory to results/datasets/ and reports/")
    
if __name__ == "__main__":
    main()
