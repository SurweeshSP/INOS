from typing import List, Dict, Tuple, Any

class MPSValidationError(Exception):
    pass

class MPSValidator:
    """
    Validates raw parsed fields from an MPS file to ensure structural and semantic correctness
    before canonical transformation.
    """
    
    @staticmethod
    def validate(name: str, 
                 rows_info: List[Tuple[str, str]], 
                 columns_info: Dict[str, List[Tuple[str, Any]]], 
                 rhs_info: Dict[str, float], 
                 bounds_info: Dict[str, Dict[str, Any]]):
                 
        if not rows_info:
            raise MPSValidationError("MPS file must contain ROWS")
            
        if not columns_info:
            raise MPSValidationError("MPS file must contain COLUMNS")
            
        # Validate objective row
        obj_rows = [name for sense, name in rows_info if sense == 'N']
        if not obj_rows:
            raise MPSValidationError("MPS file must contain at least one objective row (N)")
            
        valid_row_senses = {'N', 'E', 'L', 'G'}
        row_names = set()
        
        for sense, row_name in rows_info:
            if sense not in valid_row_senses:
                raise MPSValidationError(f"Invalid row sense '{sense}' for row {row_name}")
            row_names.add(row_name)
            
        # Validate columns
        in_intorg = False
        for col_name, entries in columns_info.items():
            for row_name, val in entries:
                if row_name == "'MARKER'":
                    continue
                if row_name not in row_names:
                    raise MPSValidationError(f"Column {col_name} references undeclared row {row_name}")
                    
        # Validate RHS
        for row_name in rhs_info:
            if row_name not in row_names:
                raise MPSValidationError(f"RHS references undeclared row {row_name}")
                
        # Validate bounds
        for col_name, b_info in bounds_info.items():
            if col_name not in columns_info:
                raise MPSValidationError(f"Bound references undeclared column {col_name}")
                
            if 'lb' in b_info and 'ub' in b_info:
                if b_info['lb'] > b_info['ub']:
                    raise MPSValidationError(f"Invalid bound for {col_name}: lb ({b_info['lb']}) > ub ({b_info['ub']})")
                    
        return True
