import copy
from typing import List
from src.data_models import OptimizationModel, Event, EventType

class MutationService:
    @staticmethod
    def apply_events_to_model(model: OptimizationModel, events: List[Event]) -> OptimizationModel:
        """
        Applies a list of business events to the OptimizationModel mathematically.
        Mutates the model's arrays (b, c, upper_bounds, lower_bounds) in-place,
        but we return a copy to be safe in the pipeline.
        """
        # Create a deep copy so we don't mutate the baseline model implicitly
        mutated_model = model
        
        var_names = list(mutated_model.variables.keys())
        con_names = list(mutated_model.constraints.keys())
        
        var_to_idx = {name: i for i, name in enumerate(var_names)}
        con_to_idx = {name: i for i, name in enumerate(con_names)}
        
        for event in events:
            # Clear previous records to strictly track this mutation
            event.affected_variables = []
            event.affected_constraints = []
            
            if event.event_type == EventType.CAPACITY_CHANGE:
                for target in event.affected_entities:
                    # Target could be a node (inv)
                    for var_name, idx in var_to_idx.items():
                        if var_name.startswith(f"inv_{target}_") or var_name.startswith(f"flow_{target}_"):
                            old_val = mutated_model.upper_bounds[idx]
                            if old_val != float('inf'):
                                new_val = old_val * (1.0 + event.magnitude)
                                mutated_model.upper_bounds[idx] = new_val
                                event.affected_variables.append(var_name)
                                event.old_value = old_val
                                event.new_value = new_val

            elif event.event_type == EventType.DEMAND_CHANGE:
                for target in event.affected_entities:
                    for con_name, idx in con_to_idx.items():
                        if con_name.startswith(f"demand_meet_{target}_"):
                            old_val = mutated_model.b[idx]
                            new_val = old_val * (1.0 + event.magnitude)
                            mutated_model.b[idx] = new_val
                            event.affected_constraints.append(con_name)
                            event.old_value = old_val
                            event.new_value = new_val
                            
                    for var_name, idx in var_to_idx.items():
                        if var_name.startswith(f"shortage_{target}_"):
                            old_val = mutated_model.upper_bounds[idx]
                            if old_val != float('inf'):
                                new_val = old_val * (1.0 + event.magnitude)
                                mutated_model.upper_bounds[idx] = new_val
                                event.affected_variables.append(var_name)

            elif event.event_type == EventType.COST_CHANGE:
                for target in event.affected_entities:
                    for var_name, idx in var_to_idx.items():
                        if var_name.startswith(f"flow_{target}_"):
                            old_val = mutated_model.c[idx]
                            new_val = old_val * (1.0 + event.magnitude)
                            mutated_model.c[idx] = new_val
                            event.affected_variables.append(var_name)
                            event.old_value = old_val
                            event.new_value = new_val

            elif event.event_type == EventType.ROUTE_BLOCKED:
                for target in event.affected_entities:
                    for var_name, idx in var_to_idx.items():
                        if var_name.startswith(f"flow_{target}_"):
                            old_val = mutated_model.upper_bounds[idx]
                            mutated_model.upper_bounds[idx] = 0.0
                            event.affected_variables.append(var_name)
                            event.old_value = old_val
                            event.new_value = 0.0
                            
            elif event.event_type == EventType.FACILITY_DOWN:
                for target in event.affected_entities:
                    for var_name, idx in var_to_idx.items():
                        if var_name.startswith(f"inv_{target}_"):
                            old_val = mutated_model.upper_bounds[idx]
                            mutated_model.upper_bounds[idx] = 0.0
                            event.affected_variables.append(var_name)
                            event.old_value = old_val
                            event.new_value = 0.0
                            
            # Update the dataclass meta info as well, just in case
            for var_name in event.affected_variables:
                idx = var_to_idx[var_name]
                mutated_model.variables[var_name].ub = mutated_model.upper_bounds[idx]
                mutated_model.variables[var_name].obj_coef = mutated_model.c[idx]
                
            for con_name in event.affected_constraints:
                idx = con_to_idx[con_name]
                mutated_model.constraints[con_name].rhs = mutated_model.b[idx]
                
        return mutated_model
