from typing import Dict, Any, List
from src.data_models import SolutionRecord, OptimizationModel
from src.api.v2_schemas import (
    DecisionPackage, 
    OptimizationStatus, 
    ExplanationBlock, 
    DiagnosticInfo
)

class ResultTranslator:
    
    @staticmethod
    def translate(solution: SolutionRecord, variable_map: Dict[str, Dict[str, Any]], telemetry: Any = None) -> DecisionPackage:
        """
        Translates a raw mathematical SolutionRecord back into business plans
        using the generated decision_variable_map.
        """
        package = DecisionPackage()
        
        # 1. Optimization Status
        opt_status = OptimizationStatus(
            status=solution.status.name,
            objective=solution.objective_value,
            runtime_seconds=solution.runtime,
            variables=len(solution.primal_values) if solution.primal_values else 0
        )
        
        if solution.status.name != "OPTIMAL" or solution.bound_violation > 0 or solution.constraint_residual > 0 or solution.integrality_violation > 0:
            opt_status.validation_status = "FAILED"
            if solution.bound_violation > 0:
                opt_status.violations.append(f"Bound violation: {solution.bound_violation}")
            if solution.constraint_residual > 0:
                opt_status.violations.append(f"Constraint residual: {solution.constraint_residual}")
        else:
            opt_status.validation_status = "VALIDATED"
            
        package.optimization = opt_status
        
        # 2. Decode Variables
        production_plan = []
        transportation_plan = []
        inventory_plan = []
        
        if solution.primal_values:
            for var_name, value in solution.primal_values.items():
                if value <= 1e-6:
                    continue # Skip zero values
                    
                meta = variable_map.get(var_name)
                if not meta:
                    continue
                    
                v_type = meta.get("type")
                if v_type == "production":
                    production_plan.append({
                        "day": meta.get("day", 0),
                        "plant": meta.get("plant", ""),
                        "product": meta.get("product", ""),
                        "quantity": value
                    })
                elif v_type == "transportation":
                    transportation_plan.append({
                        "day": meta.get("day", 0),
                        "source": meta.get("source", ""),
                        "destination": meta.get("destination", ""),
                        "product": meta.get("product", ""),
                        "quantity": value
                    })
                elif v_type == "inventory":
                    inventory_plan.append({
                        "day": meta.get("day", 0),
                        "location": meta.get("location", ""),
                        "product": meta.get("product", ""),
                        "closing": value
                    })
                    
        package.production_plan = production_plan
        package.transportation_plan = transportation_plan
        package.inventory_plan = inventory_plan
        
        # 3. Extract Bottlenecks
        # In a real scenario, this comes from dual variables or slack variables.
        # Here we just look at constraints with high duals if duals are provided.
        bottlenecks = []
        if solution.dual_values:
            sorted_duals = sorted(solution.dual_values.items(), key=lambda x: abs(x[1]), reverse=True)
            for i, (c_name, dual_val) in enumerate(sorted_duals[:5]):
                if abs(dual_val) > 1e-6:
                    bottlenecks.append({
                        "rank": i + 1,
                        "resource": c_name,
                        "shadow_price": dual_val,
                        "explanation": f"Constraint {c_name} is binding with shadow price {dual_val:.2f}"
                    })
        package.bottlenecks = bottlenecks
        
        return package

    @staticmethod
    def attach_diagnostics(package: DecisionPackage, reoptimization_result: Any, event: Any = None) -> DecisionPackage:
        """
        Attaches the explanation and telemetry from a dynamic event response.
        """
        # Safely extract diagnostics if available
        diagnostics = getattr(reoptimization_result, "diagnostics", None)
        
        fallback_used = getattr(diagnostics, "fallback_used", False) if diagnostics is not None else False
        initial_ads_size = getattr(diagnostics, "initial_ADS_size", 0) if diagnostics is not None else 0
        total_vars = getattr(diagnostics, "total_variables", 1) if diagnostics is not None else 1
        active_nodes = getattr(diagnostics, "active_nodes", []) if diagnostics is not None else []
        active_edges = getattr(diagnostics, "active_edges", []) if diagnostics is not None else []
        
        event_type_name = getattr(event, 'event_type', type('obj', (object,), {'name': 'BASELINE' if event is None else 'UNKNOWN'})).name
        
        diag = DiagnosticInfo(
            event_id=event_type_name,
            fallback_used=fallback_used,
            active_region_ratio=initial_ads_size / max(1, total_vars)
        )
        package.diagnostics = diag
        
        expl = ExplanationBlock(
            trigger=f"Event {diag.event_id} processed." if event else "Baseline optimization complete.",
            active_nodes=active_nodes,
            active_edges=active_edges,
        )
        
        if fallback_used:
            expl.why_chain.append("Structural failure or excessive changes necessitated a full scratch solve fallback.")
        elif event is not None:
            expl.why_chain.append("Adaptive reoptimization executed on the bounded active decision subgraph.")
        else:
            expl.why_chain.append("Full scratch baseline optimization executed.")
            
        package.explanation = expl
        
        return package
