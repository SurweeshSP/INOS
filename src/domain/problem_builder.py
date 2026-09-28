from typing import Tuple, Dict, Any
from src.api.v2_schemas import BusinessProblemInput
from src.data_models import OptimizationModel, NodeType, EdgeType
from src.supply_chain import SupplyChainGraph

class SupplyChainProblemBuilder:
    
    @staticmethod
    def build(problem: BusinessProblemInput) -> Tuple[OptimizationModel, Dict[str, Dict[str, Any]]]:
        """
        Takes a business problem description and returns:
        1. The canonical OptimizationModel ready for the solver.
        2. A decision_variable_map mapping variable names to business concepts.
        """
        import pandas as pd
        import os
        
        sc_graph = SupplyChainGraph(time_periods=problem.planning_horizon)
        
        supplier_ids = []
        plant_ids = []
        warehouse_ids = []
        customer_ids = []
        
        if problem.execution_mode == 'full':
            # Fast Vectorized CSV Ingestion
            network_path = 'applicationtest/SupplyChainOptii_demo_network_large.csv'
            if not os.path.exists(network_path):
                network_path = 'applicationtest/SupplyChainOptii_demo_network.csv'
                
            routes_path = 'applicationtest/SupplyChainOptii_demo_routes_large.csv'
            if not os.path.exists(routes_path):
                routes_path = 'applicationtest/SupplyChainOptii_demo_routes.csv'
            
            if os.path.exists(network_path):
                df_net = pd.read_csv(network_path)
                # Map entity types
                for _, row in df_net.iterrows():
                    eid = str(row['id'])
                    etype = str(row['entity_type']).lower()
                    cap = float(row.get('capacity', 1000.0))
                    dem = float(row.get('demand', 0.0))
                    
                    if 'supplier' in etype:
                        sc_graph.add_node(eid, NodeType.SUPPLIER, capacity=cap)
                        supplier_ids.append(eid)
                    elif 'plant' in etype:
                        sc_graph.add_node(eid, NodeType.PLANT, capacity=cap)
                        plant_ids.append(eid)
                    elif 'warehouse' in etype or 'dc' in etype:
                        sc_graph.add_node(eid, NodeType.WAREHOUSE, capacity=cap)
                        warehouse_ids.append(eid)
                    elif 'customer' in etype or 'market' in etype:
                        sc_graph.add_node(eid, NodeType.CUSTOMER, demand=dem)
                        customer_ids.append(eid)
            
            if os.path.exists(routes_path):
                df_routes = pd.read_csv(routes_path)
                for _, row in df_routes.iterrows():
                    u = str(row['from'])
                    v = str(row['to'])
                    cost = float(row.get('cost', 10.0))
                    cap = float(row.get('capacity', 500.0))
                    
                    # Infer edge type
                    etype = EdgeType.TRANSPORT
                    if u in supplier_ids and v in plant_ids:
                        etype = EdgeType.SUPPLY
                    elif u in warehouse_ids and v in customer_ids:
                        etype = EdgeType.SHIPMENT
                        
                    sc_graph.add_edge(u, v, etype, cost=cost, capacity=cap)
                    
        else:
            # Preview / Mock mode
            for entity in problem.entities:
                e_ids = entity.ids if entity.ids else [f"{entity.entity_type[:1].upper()}{str(i).zfill(2)}" for i in range(1, entity.count + 1 if entity.count else 1)]
                e_type = entity.entity_type.lower()
                for eid in e_ids:
                    if 'supplier' in e_type:
                        sc_graph.add_node(eid, NodeType.SUPPLIER, capacity=1000.0)
                        supplier_ids.append(eid)
                    elif 'plant' in e_type:
                        sc_graph.add_node(eid, NodeType.PLANT, capacity=500.0)
                        plant_ids.append(eid)
                    elif 'warehouse' in e_type or 'dc' in e_type:
                        sc_graph.add_node(eid, NodeType.WAREHOUSE, capacity=2000.0)
                        warehouse_ids.append(eid)
                    elif 'customer' in e_type or 'market' in e_type:
                        sc_graph.add_node(eid, NodeType.CUSTOMER, demand=100.0)
                        customer_ids.append(eid)

            # Add naive edges for preview
            for s in supplier_ids:
                for p in plant_ids:
                    sc_graph.add_edge(s, p, EdgeType.SUPPLY, cost=10.0, capacity=500.0)
            for p in plant_ids:
                for w in warehouse_ids:
                    sc_graph.add_edge(p, w, EdgeType.TRANSPORT, cost=15.0, capacity=300.0)
            for w in warehouse_ids:
                for c in customer_ids:
                    sc_graph.add_edge(w, c, EdgeType.SHIPMENT, cost=20.0, capacity=200.0)

        # Compile the existing model using the supply chain compiler
        model = sc_graph.to_optimization_model()
        
        # Generate the Decision Variable Map
        # The to_optimization_model generates variables like:
        # flow_{source}_{target}_t{t}
        # inv_{node}_t{t}
        # shortage_{node}_t{t}
        decision_map = {}
        for var_name in model.variables.keys():
            if var_name.startswith("flow_"):
                parts = var_name.split("_")
                if len(parts) == 4: # flow, source, target, tX
                    t_str = parts[3].replace("t", "")
                    t = int(t_str) if t_str.isdigit() else 0
                    source = parts[1]
                    target = parts[2]
                    # We classify it as production if source is plant, else transportation
                    if source in plant_ids and target in warehouse_ids:
                        v_type = "production"
                    else:
                        v_type = "transportation"
                        
                    decision_map[var_name] = {
                        "type": v_type,
                        "source": source,
                        "destination": target,
                        "plant": source if v_type == "production" else "",
                        "product": "DefaultProduct", # Simplified
                        "day": t
                    }
            elif var_name.startswith("inv_"):
                parts = var_name.split("_")
                if len(parts) == 3:
                    node = parts[1]
                    t_str = parts[2].replace("t", "")
                    t = int(t_str) if t_str.isdigit() else 0
                    decision_map[var_name] = {
                        "type": "inventory",
                        "location": node,
                        "product": "DefaultProduct",
                        "day": t
                    }

        return model, decision_map
