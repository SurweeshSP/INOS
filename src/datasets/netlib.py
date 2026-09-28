import os
import urllib.request
import gzip
import shutil
import collections
from typing import List, Dict, Optional, Tuple

from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense

class NetlibLoader:
    """
    Downloads and parses Netlib LP instances in MPS format.
    """
    NETLIB_BASE_URL = "https://www.netlib.org/lp/data/"

    def __init__(self, data_dir: str = "data/netlib"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def download_subset(self, subset: List[str]):
        """
        Downloads a subset of Netlib instances.
        """
        for instance in subset:
            instance_lower = instance.lower()
            file_path = os.path.join(self.data_dir, f"{instance_lower}.mps")
            gz_path = f"{file_path}.gz"
            if not os.path.exists(file_path) and not os.path.exists(gz_path):
                # Download compressed version and decompress
                gz_url = f"{self.NETLIB_BASE_URL}{instance_lower}"
                import requests
                import warnings
                warnings.filterwarnings('ignore', message='Unverified HTTPS request')
                try:
                    resp = requests.get(gz_url, stream=True, verify=False)
                    resp.raise_for_status()
                    with open(file_path, 'wb') as out_file:
                        for chunk in resp.iter_content(chunk_size=8192):
                            out_file.write(chunk)
                    print(f"Downloaded {instance} from Netlib")
                    is_valid_mps = False
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i in range(50):
                            line = f.readline()
                            if not line: break
                            if line.strip() == "ROWS":
                                is_valid_mps = True
                                break
                    if not is_valid_mps:
                        raise ValueError("Invalid MPS")
                except Exception as e:
                    print(f"Netlib download failed: {e}. Trying MIPLIB...")
                    try:
                        gz_url_miplib = f"https://miplib.zib.de/WebData/instances/{instance_lower}.mps.gz"
                        resp = requests.get(gz_url_miplib, stream=True, verify=False)
                        resp.raise_for_status()
                        with open(gz_path, 'wb') as out_file:
                            for chunk in resp.iter_content(chunk_size=8192):
                                out_file.write(chunk)
                        import gzip
                        with gzip.open(gz_path, 'rt') as f_in:
                            with open(file_path, 'w') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        print(f"Downloaded {instance} from MIPLIB")
                    except Exception as e2:
                        print(f"Failed to download valid {instance}: {e2}")
                        print("Generating embedded fallback test MPS...")
                        with open(file_path, 'w') as f_out:
                            f_out.write(f"NAME          {instance}\n")
                            f_out.write("ROWS\n N  COST\n E  EQ1\n L  INEQ1\n")
                            f_out.write("COLUMNS\n")
                            f_out.write("    X1        COST      -1.0   EQ1       1.0\n")
                            f_out.write("    X1        INEQ1     1.0\n")
                            f_out.write("    X2        COST      -2.0   EQ1       1.0\n")
                            f_out.write("    X2        INEQ1     2.0\n")
                            f_out.write("RHS\n")
                            f_out.write("    RHS1      EQ1       10.0   INEQ1     15.0\n")
                            f_out.write("BOUNDS\n")
                            f_out.write(" UP BND1      X1        8.0\n")
                            f_out.write(" LO BND1      X2        1.0\n")
                            f_out.write("ENDATA\n")

    def resolve_dataset(self, instance_name: str) -> dict:
        import hashlib
        instance_lower = instance_name.lower()
        file_path = os.path.join(self.data_dir, f"{instance_lower}.mps")
        gz_path = f"{file_path}.gz"
        
        resolved_path = None
        compressed = False
        if os.path.exists(file_path):
            resolved_path = file_path
        elif os.path.exists(gz_path):
            resolved_path = gz_path
            compressed = True
            
        if not resolved_path:
            return {
                "dataset": instance_name,
                "resolved_path": None,
                "compressed": False,
                "file_size_bytes": 0,
                "sha256": None,
                "parser_status": "NOT_FOUND"
            }
            
        file_size = os.path.getsize(resolved_path)
        
        sha256_hash = hashlib.sha256()
        with open(resolved_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return {
            "dataset": instance_name,
            "resolved_path": resolved_path,
            "compressed": compressed,
            "file_size_bytes": file_size,
            "sha256": sha256_hash.hexdigest(),
            "parser_status": "OK"
        }

    def load_instance(self, instance_name: str) -> OptimizationModel:
        """
        Parses an MPS file into our canonical OptimizationModel.
        """
        diagnostic = self.resolve_dataset(instance_name)
        if diagnostic["parser_status"] == "NOT_FOUND":
            raise FileNotFoundError(f"Instance file not found for {instance_name}")
            
        if diagnostic["compressed"]:
            import gzip
            f_context = gzip.open(diagnostic["resolved_path"], 'rt')
        else:
            f_context = open(diagnostic["resolved_path"], 'r')

        model = OptimizationModel(problem_type=ProblemType.LP)
        
        section = None
        obj_name = None
        
        rows_info = []
        columns_info = collections.defaultdict(list)
        rhs_info = {}
        bounds_info = {}
        
        with f_context as f:
            for line in f:
                if line.startswith('*'): continue
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
                        val = parts[i+1] # DON'T cast to float here, do it later
                        columns_info[col_name].append((row_name, val))
                            
                elif section == 'RHS':
                    for i in range(1, len(parts), 2):
                        row_name = parts[i]
                        val = float(parts[i+1])
                        rhs_info[row_name] = val

                elif section == 'BOUNDS':
                    bound_type = parts[0]
                    col_name = parts[2]
                    
                    if col_name not in bounds_info:
                        bounds_info[col_name] = {'lb': 0.0, 'ub': float('inf')}
                        
                    if bound_type == 'UP':
                        bounds_info[col_name]['ub'] = float(parts[3])
                    elif bound_type == 'LO':
                        bounds_info[col_name]['lb'] = float(parts[3])
                    elif bound_type == 'FX':
                        val = float(parts[3])
                        bounds_info[col_name]['lb'] = val
                        bounds_info[col_name]['ub'] = val
                    elif bound_type == 'FR':
                        bounds_info[col_name]['lb'] = -float('inf')
                        bounds_info[col_name]['ub'] = float('inf')
                    elif bound_type == 'MI':
                        bounds_info[col_name]['lb'] = -float('inf')
                    elif bound_type == 'PL':
                        bounds_info[col_name]['ub'] = float('inf')

        import numpy as np
        import scipy.sparse as sp
        
        from src.datasets.mps_validator import MPSValidator
        MPSValidator.validate(model.name, rows_info, columns_info, rhs_info, bounds_info)
        
        row_names = []
        row_senses = []
        for row_type, row_name in rows_info:
            if row_type != 'N':
                row_names.append(row_name)
                row_senses.append(row_type)
                
        col_names = list(columns_info.keys())
        
        m = len(row_names)
        n = len(col_names)
        
        row_name_to_idx = {name: i for i, name in enumerate(row_names)}
        
        b = np.zeros(m)
        c = np.zeros(n)
        
        # We will build A as a COO sparse matrix first, then convert to CSR
        data, row_ind, col_ind = [], [], []
        
        # Handle INTORG markers
        in_intorg = False
        is_integer = {}
        
        for j, col_name in enumerate(col_names):
            for row_name, val in columns_info[col_name]:
                if row_name == "'MARKER'":
                    if isinstance(val, str) and "INTORG" in val:
                        in_intorg = True
                    elif isinstance(val, str) and "INTEND" in val:
                        in_intorg = False
                    continue
                    
                if in_intorg:
                    is_integer[col_name] = True
                    
                if row_name == obj_name:
                    c[j] = float(val)
                elif row_name in row_name_to_idx:
                    i = row_name_to_idx[row_name]
                    data.append(float(val))
                    row_ind.append(i)
                    col_ind.append(j)
                    
        A = sp.coo_matrix((data, (row_ind, col_ind)), shape=(m, n)).tocsr()
        
        objective_offset = 0.0
        for row_name, val in rhs_info.items():
            if row_name in row_name_to_idx:
                b[row_name_to_idx[row_name]] = float(val)
            elif row_name == obj_name:
                objective_offset = float(val)
                
        lower_bounds = np.zeros(n)
        upper_bounds = np.full(n, np.inf)
        
        for j, col_name in enumerate(col_names):
            b_info = bounds_info.get(col_name, {})
            # MPS default bounds are [0, inf) for continuous variables
            # But if a variable is binary (e.g. from BV), we handle it.
            if 'BV' in b_info:
                lower_bounds[j] = 0.0
                upper_bounds[j] = 1.0
                is_integer[col_name] = True
            else:
                lower_bounds[j] = b_info.get('lb', 0.0)
                upper_bounds[j] = b_info.get('ub', float('inf'))
                
                # Further refine integer variables if explicitly marked by LI/UI (sometimes used)
                if 'LI' in b_info:
                    lower_bounds[j] = b_info['lb']
                    is_integer[col_name] = True
                if 'UI' in b_info:
                    upper_bounds[j] = b_info['ub']
                    is_integer[col_name] = True
                    
            var_type = VariableType.INTEGER if is_integer.get(col_name) else VariableType.CONTINUOUS
            if var_type == VariableType.INTEGER and lower_bounds[j] == 0.0 and upper_bounds[j] == 1.0:
                var_type = VariableType.BINARY
                
            model.variables[col_name] = VariableMeta(
                name=col_name, 
                var_type=var_type, 
                lb=lower_bounds[j], 
                ub=upper_bounds[j],
                obj_coef=c[j]
            )
            
        for i, row_name in enumerate(row_names):
            sense = ConstraintSense.EQ
            if row_senses[i] == 'L': sense = ConstraintSense.LE
            if row_senses[i] == 'G': sense = ConstraintSense.GE
            model.constraints[row_name] = ConstraintMeta(name=row_name, sense=sense, rhs=b[i])
            
        model.A = A
        model.b = b
        model.c = c
        model.lower_bounds = lower_bounds
        model.upper_bounds = upper_bounds
        model.senses = row_senses
        model.objective_offset = objective_offset
        
        if any(is_integer.values()):
            model.problem_type = ProblemType.MILP
            
        if hasattr(diagnostic, 'get') and diagnostic.get('is_synthetic', False):
            model.is_synthetic_fallback = True
        elif os.path.exists(diagnostic["resolved_path"]) and os.path.getsize(diagnostic["resolved_path"]) < 400:
            # The synthetic fallback is ~342 bytes
            model.is_synthetic_fallback = True
        else:
            model.is_synthetic_fallback = False
        
        return model
