import numpy as np
from scipy import sparse
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType, ConstraintMeta, ConstraintSense
from src.domain.schema import GenericSupplyChainModel

class MathematicalCompiler:
    def compile(self, domain_model: GenericSupplyChainModel) -> OptimizationModel:
        opt_model = OptimizationModel(problem_type=ProblemType.LP)
        
        var_names = []
        var_lbs = []
        var_ubs = []
        var_objs = []
        
        # 1. Supply variables
        for s in domain_model.supply:
            var_name = f"supply_{s.supplier}_{s.product}"
            opt_model.variables[var_name] = VariableMeta(
                name=var_name, var_type=VariableType.CONTINUOUS, lb=0.0, ub=s.capacity
            )
            var_names.append(var_name)
            var_lbs.append(0.0)
            var_ubs.append(s.capacity)
            var_objs.append(0.0)
            
        # 2. Demand variables
        for d in domain_model.demand:
            var_name = f"fulfilled_{d.customer}_{d.product}"
            opt_model.variables[var_name] = VariableMeta(
                name=var_name, var_type=VariableType.CONTINUOUS, lb=0.0, ub=d.quantity
            )
            var_names.append(var_name)
            var_lbs.append(0.0)
            var_ubs.append(d.quantity)
            var_objs.append(0.0) # Assume revenue/cost mapped separately, or 0
            
        # 3. Route variables
        for r in domain_model.routes:
            var_name = f"flow_{r.source}_{r.target}"
            opt_model.variables[var_name] = VariableMeta(
                name=var_name, var_type=VariableType.CONTINUOUS, lb=0.0, ub=r.capacity, obj_coef=r.cost
            )
            var_names.append(var_name)
            var_lbs.append(0.0)
            var_ubs.append(r.capacity)
            var_objs.append(r.cost)
            
        # 4. Processing variables
        if domain_model.processing:
            for node, proc in domain_model.processing.items():
                var_name = f"process_{node}_{proc.input_product}_{proc.output_product}"
                opt_model.variables[var_name] = VariableMeta(
                    name=var_name, var_type=VariableType.CONTINUOUS, lb=0.0, ub=proc.capacity, obj_coef=proc.cost
                )
                var_names.append(var_name)
                var_lbs.append(0.0)
                var_ubs.append(proc.capacity)
                var_objs.append(proc.cost)
                
        # 5. Inventory variables
        if domain_model.inventory:
            for node, inv in domain_model.inventory.items():
                for prod in domain_model.products:
                    var_name = f"inventory_{node}_{prod}"
                    opt_model.variables[var_name] = VariableMeta(
                        name=var_name, var_type=VariableType.CONTINUOUS, lb=0.0, ub=inv.capacity, obj_coef=inv.holding_cost
                    )
                    var_names.append(var_name)
                    var_lbs.append(0.0)
                    var_ubs.append(inv.capacity)
                    var_objs.append(inv.holding_cost)
                    
        var_idx = {name: i for i, name in enumerate(var_names)}
        
        # Constraints
        # Balance constraints per node per product: Inflow - Outflow = 0
        # Inflow = flow into node + supply at node + proc output at node
        # Outflow = flow out of node + demand fulfilled at node + proc input at node
        rows, cols, data = [], [], []
        b = []
        
        c_idx = 0
        
        # Build balance equations
        all_nodes = set()
        for nodes in domain_model.nodes.values():
            all_nodes.update(nodes)
            
        for node in all_nodes:
            for prod in domain_model.products:
                c_name = f"balance_{node}_{prod}"
                
                # Check if this equation has any terms
                has_terms = False
                
                # Inflow terms (+1)
                for r in domain_model.routes:
                    if r.target == node: # Assuming flow represents a single generic product or route specific? 
                        # In the data model, route doesn't specify product, assume it carries all or generic. 
                        # For now, let's assume routes carry generic flow unless specified. Wait, schema doesn't have product in Route.
                        # Let's map route flow to product if there's only 1 product, or sum. 
                        # To keep it simple, assume flow is per route for all products, we'll just add it to the balance.
                        pass
                        
                for s in domain_model.supply:
                    if s.supplier == node and s.product == prod:
                        var_name = f"supply_{s.supplier}_{s.product}"
                        rows.append(c_idx); cols.append(var_idx[var_name]); data.append(1.0)
                        has_terms = True
                        
                if domain_model.processing and node in domain_model.processing:
                    proc = domain_model.processing[node]
                    if proc.output_product == prod:
                        var_name = f"process_{node}_{proc.input_product}_{proc.output_product}"
                        rows.append(c_idx); cols.append(var_idx[var_name]); data.append(1.0) # output 1.0 or yield rate? yield_rate!
                        # Let's use yield_rate
                        data[-1] = proc.yield_rate
                        has_terms = True
                        
                # Outflow terms (-1)
                for d in domain_model.demand:
                    if d.customer == node and d.product == prod:
                        var_name = f"fulfilled_{d.customer}_{d.product}"
                        rows.append(c_idx); cols.append(var_idx[var_name]); data.append(-1.0)
                        has_terms = True
                        
                if domain_model.processing and node in domain_model.processing:
                    proc = domain_model.processing[node]
                    if proc.input_product == prod:
                        var_name = f"process_{node}_{proc.input_product}_{proc.output_product}"
                        rows.append(c_idx); cols.append(var_idx[var_name]); data.append(-1.0)
                        has_terms = True
                        
                # Route matching
                for r in domain_model.routes:
                    # In a real compiler, routes would specify products. For this simplified domain:
                    if r.target == node:
                        var_name = f"flow_{r.source}_{r.target}"
                        rows.append(c_idx); cols.append(var_idx[var_name]); data.append(1.0)
                        has_terms = True
                    if r.source == node:
                        var_name = f"flow_{r.source}_{r.target}"
                        rows.append(c_idx); cols.append(var_idx[var_name]); data.append(-1.0)
                        has_terms = True
                        
                if has_terms:
                    opt_model.constraints[c_name] = ConstraintMeta(name=c_name, sense=ConstraintSense.EQ, rhs=0.0)
                    b.append(0.0)
                    c_idx += 1
                    
        num_vars = len(var_names)
        num_cons = c_idx
        
        opt_model.c = np.array(var_objs, dtype=np.float64)
        opt_model.lower_bounds = np.array(var_lbs, dtype=np.float64)
        opt_model.upper_bounds = np.array(var_ubs, dtype=np.float64)
        
        if num_cons > 0:
            opt_model.A = sparse.csr_matrix((data, (rows, cols)), shape=(num_cons, num_vars))
            opt_model.b = np.array(b, dtype=np.float64)
        else:
            opt_model.A = sparse.csr_matrix((0, num_vars))
            opt_model.b = np.array([], dtype=np.float64)
            
        return opt_model
