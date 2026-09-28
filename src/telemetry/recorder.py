import json
import os
from typing import List
from src.telemetry.schema import SolverExperienceRecord

class TelemetryRecorder:
    def __init__(self, log_dir: str = "results/telemetry"):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
            
        self.current_file = os.path.join(self.log_dir, "experience_records.jsonl")

    def record(self, experience: SolverExperienceRecord):
        with open(self.current_file, "a") as f:
            f.write(json.dumps(experience.to_dict()) + "\n")
            
    def load_all(self) -> List[SolverExperienceRecord]:
        records = []
        if os.path.exists(self.current_file):
            with open(self.current_file, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        records.append(SolverExperienceRecord(**data))
        return records
