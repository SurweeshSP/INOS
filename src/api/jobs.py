import uuid
import json
import os
from typing import Dict, Any

# Simple in-memory + file-based job manager for single-node deployment
JOBS_DIR = "data/runtime/jobs"

class JobManager:
    def __init__(self):
        os.makedirs(JOBS_DIR, exist_ok=True)
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "status": "QUEUED",
            "result": None
        }
        self.jobs[job_id] = job_data
        self._save_job(job_id)
        return job_id

    def update_job_status(self, job_id: str, status: str, result: Any = None):
        if job_id not in self.jobs:
            self._load_job(job_id)
            
        if job_id in self.jobs:
            self.jobs[job_id]["status"] = status
            if result is not None:
                self.jobs[job_id]["result"] = result
            self._save_job(job_id)

    def get_job(self, job_id: str) -> Dict[str, Any]:
        if job_id not in self.jobs:
            self._load_job(job_id)
        return self.jobs.get(job_id, {"status": "NOT_FOUND"})

    def _save_job(self, job_id: str):
        path = os.path.join(JOBS_DIR, f"{job_id}.json")
        with open(path, "w") as f:
            json.dump(self.jobs[job_id], f, indent=2)

    def _load_job(self, job_id: str):
        path = os.path.join(JOBS_DIR, f"{job_id}.json")
        if os.path.exists(path):
            with open(path, "r") as f:
                self.jobs[job_id] = json.load(f)

job_manager = JobManager()
