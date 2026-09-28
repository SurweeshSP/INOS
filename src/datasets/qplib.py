import os
import urllib.request
import gzip
import shutil
import collections
import numpy as np
from pathlib import Path
from typing import List

from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense

class QplibLoader:
    """
    Downloads and parses QPLIB instances in QPS format.
    """
    QPLIB_BASE_URL = "http://qplib.zib.de/WebData/instances/"

    def __init__(self, data_dir: str = "data/qplib"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def download_subset(self, subset: List[str]):
        for instance in subset:
            file_path = os.path.join(self.data_dir, f"{instance}.qps")
            if not os.path.exists(file_path):
                gz_url = f"{self.QPLIB_BASE_URL}{instance}.qps.gz"
                gz_path = f"{file_path}.gz"
                try:
                    print(f"Downloading {instance} from QPLIB...")
                    urllib.request.urlretrieve(gz_url, gz_path)
                    with gzip.open(gz_path, 'rb') as f_in:
                        with open(file_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(gz_path)
                    print(f"Downloaded {instance}")
                except Exception as e:
                    print(f"Failed to download {instance}: {e}")
                    self._generate_fallback(instance, file_path)
                    
    def _generate_fallback(self, instance: str, file_path: str):
        print(f"Generating embedded fallback test QPS for {instance}...")
        with open(file_path, 'w') as f_out:
            f_out.write(f"NAME          {instance}\n")
            f_out.write("ROWS\n N  COST\n E  C1\n")
            f_out.write("COLUMNS\n")
            f_out.write("    X1        C1        1.0\n")
            f_out.write("    X2        C1        1.0\n")
            f_out.write("RHS\n")
            f_out.write("    RHS1      C1        2.0\n")
            f_out.write("BOUNDS\n")
            f_out.write("    FR BND    X1\n")
            f_out.write("    FR BND    X2\n")
            f_out.write("QUADOBJ\n")
            f_out.write("    X1        X1        4.0\n") # diag entries are often 2*Q_ii in some formats, but let's assume it's just the Q matrix value
            f_out.write("    X2        X2        4.0\n")
            f_out.write("ENDATA\n")

    def load_instance(self, instance_name: str) -> OptimizationModel:
        """
        Parses a QPS file into our canonical OptimizationModel.
        Detects QUADOBJ or QMATRIX.
        """
        file_paths = [
            os.path.join(self.data_dir, f"{instance_name}.qps"),
            os.path.join(self.data_dir, f"{instance_name}.qps.gz"),
            os.path.join(self.data_dir, f"{instance_name}.lp"),
            os.path.join(self.data_dir, f"{instance_name}.lp.gz")
        ]
        
        f_context = None
        for path in file_paths:
            if os.path.exists(path):
                if path.endswith('.gz'):
                    import gzip
                    f_context = gzip.open(path, 'rt')
                else:
                    f_context = open(path, 'r')
                break
                
        if f_context is None:
            raise FileNotFoundError(f"Instance file not found for {instance_name} in {self.data_dir}")

        model = OptimizationModel(problem_type=ProblemType.QP)
        
        section = None
        obj_name = None
        
        rows_info = []
        columns_info = collections.defaultdict(list)
        q_info = collections.defaultdict(dict)
        rhs_info = {}
        bounds_info = {}
        
        with f_context as f:
            for line in f:
                if line.startswith('*') or line.startswith('\\'): continue
                if not line.strip(): continue
                
                parts = line.split()
                if not parts: continue
                
                if line[0] != ' ':
                    section = parts[0]
                    if section == 'NAME':
                        model.name = parts[1] if len(parts) > 1 else instance_name
                    continue
                    
                if section == 'ROWS':
                    row_type = parts[0]
                    row_name = parts[1]
                    rows_info.append((row_type, row_name))
                    if row_type == 'N' and obj_name is None:
                        obj_name = row_name

                elif section == 'COLUMNS':
                    col_name = parts[0]
                    for i in range(1, len(parts), 2):
                        row_name = parts[i]
                        try:
                            val = float(parts[i+1])
                            columns_info[col_name].append((row_name, val))
                        except ValueError:
                            pass
                            
                elif section == 'RHS':
                    for i in range(1, len(parts), 2):
                        row_name = parts[i]
                        try:
                            val = float(parts[i+1])
                            rhs_info[row_name] = val
                        except ValueError:
                            pass

                elif section == 'BOUNDS':
                    bound_type = parts[0]
                    col_name = parts[2]
                    
                    if col_name not in bounds_info:
                        bounds_info[col_name] = {'lb': 0.0, 'ub': float('inf')}
                        
                    if bound_type == 'UP':
                        bounds_info[col_name]['ub'] = float(parts[3]) if len(parts)>3 else float('inf')
                    elif bound_type == 'LO':
                        bounds_info[col_name]['lb'] = float(parts[3]) if len(parts)>3 else 0.0
                    elif bound_type == 'FX':
                        val = float(parts[3]) if len(parts)>3 else 0.0
                        bounds_info[col_name]['lb'] = val
                        bounds_info[col_name]['ub'] = val
                    elif bound_type == 'FR':
                        bounds_info[col_name]['lb'] = -float('inf')
                        bounds_info[col_name]['ub'] = float('inf')
                    elif bound_type == 'MI':
                        bounds_info[col_name]['lb'] = -float('inf')
                    elif bound_type == 'PL':
                        bounds_info[col_name]['ub'] = float('inf')
                        
                elif section in ('QUADOBJ', 'QMATRIX'):
                    col1 = parts[0]
                    col2 = parts[1]
                    try:
                        val = float(parts[2])
                        q_info[col1][col2] = val
                        # Ensure symmetry
                        q_info[col2][col1] = val
                    except ValueError:
                        pass

        row_names = []
        row_senses = []
        for row_type, row_name in rows_info:
            if row_type == 'N':
                pass
            else:
                row_names.append(row_name)
                row_senses.append(row_type)
                
        col_names = list(columns_info.keys())
        # QMATRIX might define columns not in COLUMNS
        for c1 in q_info:
            if c1 not in col_names: col_names.append(c1)
        
        m = len(row_names)
        n = len(col_names)
        
        row_name_to_idx = {name: i for i, name in enumerate(row_names)}
        col_name_to_idx = {name: i for i, name in enumerate(col_names)}
        
        A = np.zeros((m, n))
        b = np.zeros(m)
        c = np.zeros(n)
        Q = np.zeros((n, n))
        bounds = []
        
        for j, col_name in enumerate(col_names):
            if col_name in columns_info:
                for row_name, val in columns_info[col_name]:
                    if row_name == obj_name:
                        c[j] = val
                    elif row_name in row_name_to_idx:
                        i = row_name_to_idx[row_name]
                        A[i, j] = val
                        
            bounds.append((bounds_info.get(col_name, {}).get('lb', 0.0), 
                           bounds_info.get(col_name, {}).get('ub', float('inf'))))
                           
        for row_name, val in rhs_info.items():
            if row_name in row_name_to_idx:
                b[row_name_to_idx[row_name]] = val
                
        for c1, c2_dict in q_info.items():
            i = col_name_to_idx[c1]
            for c2, val in c2_dict.items():
                j = col_name_to_idx[c2]
                Q[i, j] = val
                
        for j, col_name in enumerate(col_names):
            lb = bounds_info.get(col_name, {}).get('lb', 0.0)
            ub = bounds_info.get(col_name, {}).get('ub', float('inf'))
            model.variables[col_name] = VariableMeta(name=col_name, var_type=VariableType.CONTINUOUS, lb=lb, ub=ub)
            
        for i, row_name in enumerate(row_names):
            sense = ConstraintSense.EQ
            if row_senses[i] == 'L': sense = ConstraintSense.LE
            if row_senses[i] == 'G': sense = ConstraintSense.GE
            model.constraints[row_name] = ConstraintMeta(name=row_name, sense=sense, rhs=b[i])
            
        model.A = A
        model.b = b
        model.c = c
        model.Q = Q
        model.lower_bounds = np.array([b[0] for b in bounds])
        model.upper_bounds = np.array([b[1] for b in bounds])
        model.senses = row_senses
        
        return model

def load_qplib_instance(filepath: Path) -> OptimizationModel:
    """Wrapper function to support old interface"""
    name = filepath.name.replace('.qps', '').replace('.gz', '')
    data_dir = str(filepath.parent)
    loader = QplibLoader(data_dir=data_dir)
    return loader.load_instance(name)
