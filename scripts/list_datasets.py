import os
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1] / "data"
    
    print("="*50)
    print("Available Datasets in data/")
    print("="*50)
    
    for ds in ["miplib", "qplib", "dynamic", "netlib", "isomorph", "logior"]:
        ds_path = root / ds
        if ds_path.exists():
            files = []
            if ds == "miplib":
                files = list(ds_path.glob("*.mps.gz"))
            elif ds == "qplib":
                lp_path = ds_path / "qplib" / "html" / "lp"
                if lp_path.exists():
                    files = list(lp_path.glob("*.lp"))
            elif ds == "dynamic":
                files = list(ds_path.glob("*.txt"))
                
            print(f"- {ds.upper()}: {len(files)} instances found.")
        else:
            print(f"- {ds.upper()}: Directory not found.")

if __name__ == "__main__":
    main()
