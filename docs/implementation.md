# SupplyChainOptii: Implementation and Architecture Summary (Phases 1–24)

## Overview
This document summarizes the architecture, completed subsystems, testing infrastructure, and datasets established from Phase 1 through Phase 24. The SupplyChainOptii engine has been systematically built to operate as a state-aware, event-aware, hardware-accelerated, and learning-ready industrial optimization solver.

---

## Architecture & Subsystems

### Foundation (Phases 1–5)
- **Canonical Data Model (`src/data_models.py`):** Defines the core schema, including `OptimizationModel`, `VariableMeta`, and `ConstraintMeta`.
- **Data Loader & Statistics (`src/data_loader.py`, `src/analytics/statistics.py`):** Provides loading from serialized formats and core statistical analytics for model feature extraction.
- **Supply-Chain Mathematics (`src/supply_chain.py`):** Maps logical supply-chain operations into rigorous mathematical matrix representations.
- **Sparse Numerical Layer (`src/solver/sparse.py`):** Preserves structural sparsity throughout linear algebra routines to maintain memory efficiency and execution speed.

### Solver Core (Phases 6–8)
- **Real LP Solver (`src/solver/lp/`):** Implements Revised Simplex methods capable of handling standard equality/inequality bounds.
- **Real MILP Solver (`src/solver/milp/`):** Executes Branch-and-Bound logic for integer feasibility, maintaining bounds and gap tracking.
- **Real QP Solver (`src/solver/qp/`):** Engineered with a strict Primal Active-Set approach. It manages KKT conditions, phase-1 LP initializations for feasibility, and explicit `Q` quadratic objective matrices.

### Hardware & State Persistence (Phases 9–14)
- **Persistent State (`src/state.py`):** Defines `PersistentOptimizationState` and `StateManager` for saving/loading optimizer warm-start history securely.
- **GPU Execution Backend (`src/hardware.py`, `src/solver/execution_backend.py`):** Wraps operations targeting `cupy` for GPU acceleration and automatically falls back to `scipy.sparse` on CPU.
- **Profiling (`src/profiling.py`):** Detects hardware bottlenecks, specifically mitigating overhead on smaller models where a CPU might outperform GPU transfer latency.

### Adaptive Optimization Core (Phases 15–18)
- **Supply-Chain Graph (`src/graph.py`):** Formally represents the network as `G = (V, E, T)`.
- **Active Decision Subgraph (ADS) (`src/active_graph.py`):** Dynamically isolates nodes and edges impacted by a specific event.
- **Delta Boundary Model (`src/delta_model.py`, `src/delta_builder.py`):** Mathematically constructs the localized sparse linear residuals ($b_{active} - A_{active} \cdot x_{base}$) ensuring fixed boundary effects from outside the sub-graph are explicitly preserved.
- **Adaptive Orchestrator (`src/adaptive.py`):** Cycles through the pipeline: ADS ➔ Delta Model ➔ CPU/GPU Solve ➔ Global Validation, with automated fallback logic for validation failures.

### Harness, Telemetry, and End-to-End API (Phases 19–24)
- **Intelligent Harness (`src/harness/`):** Evaluates model sizes, event magnitudes, and state validity to deterministically select the optimization strategy (e.g., ADAPTIVE vs FULL). Protected by `SafetyGate`.
- **Scenario Engine (`src/scenarios/`):** Deterministically generates optimization shocks like Demand/Supply/Network disruptions (S1-S4 classes) using fixed random seeds.
- **Telemetry System (`src/telemetry/`):** `SolverExperienceRecord` captures structural outcomes (runtime, objective delta, variables touched) to a machine-readable JSONL sink for future Machine Learning pipelines.
- **Unified Optimizer API (`src/optimizer.py`):** `SupplyChainOptimizer` encapsulates the complete pipeline, allowing users to issue `.solve()` and `.reoptimize()` commands seamlessly.

---

## Testing Infrastructure

The project includes an extensive test suite verifying exact mathematical and algorithmic invariants.

**Execution:** 
Run via `pytest` (currently achieving 50/50 test passes).

**Key Test Modules:**
- `tests/unit/test_qp.py`: Validates strict active-set KKT convergence over inequality constraints.
- `tests/unit/test_graph.py` & `test_ads.py`: Verifies structural graph closures.
- `tests/unit/test_delta_reoptimization.py`: Proves residual arithmetic.
- `tests/unit/test_api.py`, `test_harness.py`, `test_scenarios.py`: Covers the batch 1 orchestration logic and end-to-end API lifecycle.

---

## Datasets (`data/`)

The repository integrates a comprehensive `data/` directory utilized for benchmarking and validating algorithmic implementations across varying difficulty classes.

- **Netlib (`data/netlib/` or `data/tools/netlib/`):** Standard LP benchmark dataset (MPS formats) used to test standard feasibility and simplex stability.
- **MIPLIB:** Standard Mixed-Integer formulations utilized for testing the Branch-and-Bound efficiency.
- **QPLIB (`data/qplib/`):** Massive repository containing quadratic test instances parsed by our custom `QplibLoader`. Used to rigorously assert the correctness of our Active-Set QP implementation.
- **Supply-Chain Synthetics:** Generated iteratively via the `ScenarioEngine` to mimic localized supply shocks and demand spikes specifically targeted for evaluating ADS compression performance.
