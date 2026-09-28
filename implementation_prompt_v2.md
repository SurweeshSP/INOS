# Implementation Prompt — Indigenous Adaptive Supply-Chain Optimization System

Implement the complete architecture described in `architecture_supply_chain.md` and the stakeholder workflow described in `user.md`.

## Mission

Build a Python-first sovereign mathematical optimization decision engine around:

```text
User / Stakeholder Input
→ Data Validation
→ Canonical Model
→ Statistics
→ Persistent Optimization State
→ Event Detection
→ Impact Analysis
→ Active Decision Subgraph
→ Delta Model
→ Algorithm Harness
→ CPU/GPU Solver
→ Global Validation
→ Visualization + R Analytics
→ Stakeholder Decision
→ Next Scenario / Optimization Cycle
```

The original PS requires LP, MILP and QP support, sparse numerical methods, CPU/GPU acceleration where beneficial, industrial applications, and benchmark validation. Do not use an existing complete optimization solver as the solver core. Do not introduce C++.

Python is the primary language.

---

# 1. Required implementation structure

```text
src/
├── data_models.py
├── data_loader.py
├── supply_chain.py
├── state.py
├── change_detection.py
├── impact_analysis.py
├── active_graph.py
├── delta_model.py
├── delta_reoptimization.py
├── harness.py
├── validation.py
├── solver/
│   ├── lp.py
│   ├── milp.py
│   ├── qp.py
│   ├── simplex.py
│   ├── interior_point.py
│   ├── branch_bound.py
│   ├── cuts.py
│   ├── heuristics.py
│   ├── sparse.py
│   ├── cpu.py
│   └── gpu.py
├── analytics/
│   ├── statistics.py
│   ├── sensitivity.py
│   ├── scenario_analysis.py
│   ├── telemetry.py
│   └── r_bridge.py
└── visualization/
    ├── plots.py
    ├── supply_chain_plots.py
    ├── solver_plots.py
    └── scenario_plots.py
```

Also create:

```text
user.md
architecture_supply_chain.md
```

---

# 2. Canonical data model

`src/data_models.py` is the single schema source.

Implement dataclasses/enums:

```text
ProblemType
VariableType
ConstraintSense
EventType
NodeType
EdgeType
ConstraintRole
SolveStatus
AlgorithmType

VariableMeta
ConstraintMeta
NodeMeta
EdgeMeta
OptimizationModel
SolutionRecord
SupplyChainState
Event
Scenario
PersistentOptimizationState
ActiveRegion
BoundaryCondition
HarnessFeatures
HarnessDecision
SolverTelemetry
ExperienceRecord
InputRequest
ValidationResult
```

No downloads, optimization calls or graph algorithms inside this file.

---

# 3. Data loader

`src/data_loader.py` must expose:

```python
load_instance(...)
load_dataset(...)
load_scenario(...)
load_timeseries(...)
load_solution(...)
normalize_model(...)
```

Support adapters for:

```text
MIPLIB
Netlib
QPLIB
LogiOR
MIPcc23
ISOMORPH
disruption datasets
```

Requirements:

- preserve sparse matrices;
- never silently densify large models;
- lazy-load/stream ISOMORPH;
- normalize all sources into `OptimizationModel`;
- keep source metadata;
- support MPS, LP, QPLIB, JSON, CSV and Parquet where applicable.

---

# 4. User/stakeholder input layer

Implement an input abstraction that accepts:

```text
objective
horizon
demand
supply
production
inventory
capacity
routes
costs
service targets
business constraints
events
scenario parameters
uncertainty parameters
requested outputs
```

Support three input forms:

```text
business/API input
dataset input
what-if/event input
```

Do not invent missing operational values.

Validate:

```text
missing IDs
unknown entities
invalid bounds
negative capacities
NaN/Inf
duplicate IDs
dimension mismatch
time mismatch
```

---

# 5. Supply-chain model

Represent:

```text
G = (V, E, T)
```

Map:

```text
graph node/edge
↔ optimization variable
↔ optimization constraint
```

Support:

```text
supplier
plant
warehouse
DC
customer
port
market
```

and:

```text
supply
production
transport
shipment
flow
dependency
```

---

# 6. Statistical analytics

Implement `src/analytics/statistics.py`.

Provide:

```text
mean
variance
std
CV
quantiles
rolling statistics
trend
demand risk
capacity utilization
capacity stress
inventory risk
service level
service gap
disruption severity
correlation
```

Prefer empirical risk estimation when sufficient data exists.

Do not let statistical estimates override mathematical feasibility.

---

# 7. R integration

Implement `src/analytics/r_bridge.py`.

R is auxiliary, never the optimization core.

Use R for:

```text
statistical inference
time-series analysis
distribution fitting
uncertainty analysis
research diagnostics
```

Prefer a file/API boundary:

```text
Python
→ Parquet/CSV/JSON
→ R
→ result files
→ Python
```

The optimization loop must not depend on R being installed.

If R is unavailable, the Python pipeline must continue with Python-based statistics.

---

# 8. Matplotlib visualization

Implement:

```text
src/visualization/plots.py
src/visualization/supply_chain_plots.py
src/visualization/solver_plots.py
src/visualization/scenario_plots.py
```

Generate:

```text
network topology
flows
inventory
demand vs supply
capacity utilization
route utilization
service
shortage
objective convergence
primal/dual residuals
MIP gap
branch nodes
cuts
solve-time distribution
full vs active model size
ADS expansion
CPU vs GPU runtime
scenario comparison
sensitivity ranking
```

Visualization must never mutate solver state.

---

# 9. Persistent Optimization State

Implement `src/state.py`.

Store optional:

```text
previous solution
objective
feasibility
optimality
warm start
incumbent
basis
LP relaxation state
cut metadata
node statistics
variable activity
constraint activity
sensitivity
event history
solve history
```

State must be versioned.

---

# 10. Event detection

Implement `src/change_detection.py`.

Detect:

```text
DEMAND_CHANGE
CAPACITY_CHANGE
COST_CHANGE
ROUTE_BLOCKED
ROUTE_RESTORED
FACILITY_DOWN
FACILITY_RESTORED
NEW_ORDER
CANCELLATION
SUPPLY_CHANGE
SERVICE_CHANGE
INVENTORY_SHOCK
MULTI_EVENT
```

Compare old/new values with configurable absolute and relative tolerances.

Map every event to:

```text
entities
products
periods
variables
constraints
```

---

# 11. Impact analysis

Implement `src/impact_analysis.py`.

Use a hybrid relevance score:

```text
dependency strength
shared resource
shared constraint
temporal overlap
flow dependency
historical coupling
propagation probability
graph distance
```

Do not use graph distance alone.

Return ranked candidate components with scores and explanations.

---

# 12. Active Decision Subgraph

Implement `src/active_graph.py`.

Algorithm:

```text
event
→ seed changed components
→ dependency expansion
→ shared-resource expansion
→ shared-constraint expansion
→ temporal expansion
→ sensitivity expansion
→ historical expansion
→ thresholding
→ boundary completion
```

ADS must contain:

```text
nodes
edges
variables
constraints
boundary conditions
```

---

# 13. Delta model

Implement `src/delta_model.py`.

Given:

```text
M_t
Delta M
```

represent:

```text
M_(t+1) = M_t + Delta M
```

without unnecessary full-model copying.

Use:

```text
ModelBase
ModelDelta
ActiveIndexMap
BoundaryState
```

---

# 14. Delta reoptimization

Implement `src/delta_reoptimization.py`.

Required flow:

```text
previous state
→ new data
→ event detection
→ ADS
→ reduced model
→ Harness
→ persistent-state warm start
→ CPU/GPU solver
→ global reconstruction
→ global validation
```

If validation fails:

```text
violations
→ variables
→ graph entities
→ expand ADS
→ rebuild
→ reoptimize
```

Fallback to full model.

---

# 15. CPU optimizer

Implement `src/solver/cpu.py`.

Use:

```text
NumPy
SciPy sparse primitives where appropriate
Python numerical kernels
parallel CPU execution where safe
```

CPU should be preferred for:

```text
small models
small ADS
irregular operations
branch-and-bound control
GPU-transfer-dominated workloads
```

Do not wrap CBC, HiGHS, SCIP, Gurobi, CPLEX or another complete optimizer as the solver core.

---

# 16. GPU optimizer

Implement `src/solver/gpu.py`.

Use:

```text
CUDA
CuPy
Numba CUDA
```

GPU candidates:

```text
sparse matrix-vector operations
residual calculations
vector operations
batched scenario calculations
selected sparse linear algebra
large active-region numerical kernels
```

Do not assume GPU is faster.

Estimate suitability from:

```text
n
m
nnz
sparsity
active size
batch size
transfer cost
historical GPU performance
```

Measure actual CPU/GPU runtime.

---

# 17. Algorithm Harness

Implement `src/harness.py`.

The initial Harness must be deterministic/rule-based.

Inputs:

```text
problem type
n
m
nnz
density
integer fraction
binary fraction
coefficient range
event type
event magnitude
active fraction
boundary fraction
integrality gap
degeneracy proxy
sensitivity
warm-start quality
GPU suitability
historical performance
```

Outputs:

```text
algorithm
CPU/GPU
presolve
warm-start policy
cut policy
heuristic policy
branching
node selection
parallelism
```

Later train a learned Harness from telemetry.

The learned policy cannot bypass safety rules.

---

# 18. Global validation

Implement `src/validation.py`.

Check:

```text
constraint feasibility
bounds
integrality
linking
service
route/facility constraints
objective consistency
```

Return a structured `ValidationResult`.

Never accept an ADS result without global validation.

---

# 19. User decision workflow

Implement an application-level flow:

```text
define objective
→ upload/enter data
→ validate
→ build model
→ statistics
→ base solve
→ visualize
→ stakeholder review
→ create scenario
→ event detection
→ ADS
→ delta reoptimization
→ validation
→ scenario comparison
→ approve / modify / reject
→ next cycle
```

User changes must become explicit mathematical events/constraints.

Human overrides must be represented in the model and reoptimized.

---

# 20. Scenario analysis

Implement scenario classes:

```text
demand
capacity
cost
route
facility
supply
inventory
service
multi-event
```

Every scenario stores:

```text
base_instance_id
scenario_id
event
changed parameters
random seed
full-solve result
adaptive result
```

Compare:

```text
objective
cost
service
inventory
risk
capacity
solve time
active fraction
expansion count
CPU/GPU
```

---

# 21. Solver Experience Dataset

Implement telemetry recording:

```text
problem signature
event signature
active fraction
algorithm
CPU/GPU
presolve
warm start
solve time
iterations
nodes
cuts
memory
objective
gap
feasibility
expansion count
validation time
success
```

Store in Parquet.

This becomes the future learned-Harness training data.

---

# 22. Benchmark protocol

Compare:

```text
full solve from scratch
persistent-state solve
ADS + delta solve
ADS + delta + Harness
```

Use:

```text
MIPLIB
Netlib
QPLIB
MIPcc23
LogiOR
ISOMORPH
disruption datasets
```

Report:

```text
mean
median
std
IQR
p5
p95
speedup
active reduction
node reduction
iteration reduction
validation success
timeout rate
bootstrap confidence interval
paired effect
```

Do not report speedup without paired baseline/adaptive runs.

---

# 23. First end-to-end demonstration

Build one supply-chain application:

```text
Supplier → Plant → Warehouse → Customer
```

User provides:

```text
demand
capacity
inventory
routes
cost
service target
horizon
```

System performs:

```text
input validation
→ statistics
→ base optimization
→ persistent state
→ Matplotlib result
→ user disruption
→ event detection
→ ADS
→ CPU/GPU Harness
→ delta solve
→ global validation
→ scenario comparison
→ visualization
→ telemetry
```

This is the reference application.

---

# 24. Implementation order

```text
1 data_models.py
2 data_loader.py
3 analytics/statistics.py
4 tests
5 supply_chain.py
6 state.py
7 change_detection.py
8 impact_analysis.py
9 active_graph.py
10 delta_model.py
11 validation.py
12 CPU/GPU numerical backends
13 harness.py
14 delta_reoptimization.py
15 visualization
16 R bridge
17 telemetry
18 benchmark runner
19 learned Harness
```

Do not begin with ML.

---

# 25. Coding constraints

- Python-first.
- No C++.
- No complete external optimization solver as the solver core.
- Sparse-first.
- No silent dense conversion.
- Lazy/streaming large datasets.
- Deterministic seeds.
- Configurable numerical tolerances.
- Unit tests for mathematical transformations.
- Full model always retained for validation.
- R optional.
- Matplotlib is the primary scientific visualization system.
- CPU/GPU choice must be measured.
- User overrides must become explicit mathematical changes.
- Never fabricate missing business data.
- Never claim optimization correctness without validation.

---

# 26. Acceptance criteria

The implementation is complete only when:

1. A stakeholder can define an objective and upload operational data.
2. The data becomes a canonical optimization model.
3. A base plan can be solved.
4. Persistent state is stored.
5. Results are visualized with Matplotlib.
6. A user can create a what-if event.
7. The event maps to model and graph components.
8. ADS is constructed automatically.
9. Harness selects CPU or GPU using explicit features.
10. Delta reoptimization reuses state.
11. The full changed model validates the result.
12. ADS expands if validation fails.
13. Scenario comparison is generated.
14. R can be used for optional statistical analysis.
15. Solver telemetry is persisted.
16. Full vs adaptive benchmarks can be reproduced.
17. The system safely falls back to a full solve.
18. The user can approve or modify the resulting plan.

The final product should behave as a mathematically validated decision-support system:

```text
Human intent
→ data
→ analysis
→ optimization
→ adaptive reoptimization
→ validation
→ explanation
→ human decision
```
