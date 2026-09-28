from typing import Optional, List, Any
from src.data_models import PersistentOptimizationState, SolutionRecord, Event

class StateManager:
    def __init__(self, model_version: str = "v1"):
        self.state = PersistentOptimizationState(model_version=model_version)

    def update_solution(self, solution: SolutionRecord):
        self.state.previous_solution = solution
        self.state.solve_history.append(solution)
        if solution.objective_value is not None:
            self.state.objective = solution.objective_value
        self.state.feasibility = (solution.status.name == "OPTIMAL")

    def record_event(self, event: Event):
        self.state.event_history.append(event)

    def save_state(self, filepath: str):
        """
        Serializes the entire state object to disk securely via pickle.
        """
        import pickle
        import os
        
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(filepath, 'wb') as f:
            pickle.dump(self.state, f)

    def load_state(self, filepath: str):
        """
        Deserializes state from disk and strictly checks version compatibility.
        """
        import pickle
        import os
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"State file not found: {filepath}")
            
        with open(filepath, 'rb') as f:
            loaded_state = pickle.load(f)
            
        if not isinstance(loaded_state, PersistentOptimizationState):
            raise TypeError("Loaded object is not a PersistentOptimizationState instance.")
            
        if loaded_state.model_version != self.state.model_version:
            raise ValueError(f"State version mismatch. Expected {self.state.model_version}, got {loaded_state.model_version}")
            
        self.state = loaded_state
