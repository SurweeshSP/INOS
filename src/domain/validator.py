from src.domain.schema import GenericSupplyChainModel

class DomainValidator:
    def validate(self, model: GenericSupplyChainModel) -> bool:
        # Collect all defined nodes
        all_nodes = set()
        for node_list in model.nodes.values():
            all_nodes.update(node_list)
            
        # Check products
        products = set(model.products)
        
        # Check supply
        for s in model.supply:
            if s.supplier not in all_nodes:
                raise ValueError(f"Supplier {s.supplier} not defined in nodes.")
            if s.product not in products:
                raise ValueError(f"Product {s.product} not defined in products.")
                
        # Check demand
        for d in model.demand:
            if d.customer not in all_nodes:
                raise ValueError(f"Customer {d.customer} not defined in nodes.")
            if d.product not in products:
                raise ValueError(f"Product {d.product} not defined in products.")
                
        # Check routes
        for r in model.routes:
            if r.source not in all_nodes:
                raise ValueError(f"Route source {r.source} not defined in nodes.")
            if r.target not in all_nodes:
                raise ValueError(f"Route target {r.target} not defined in nodes.")
                
        return True
