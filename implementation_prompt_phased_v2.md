# Implementation Prompt — Phase-by-Phase Implementation of the Indigenous Adaptive Optimization Solver

## Governing specification

Implement the system **exactly according to `architecture_supply_chain_v2.md`**.

This prompt does NOT replace the architecture. It converts the unphased architecture into an **ordered implementation and testing plan**.

The architecture is the source of truth for:

- terminology;
- system boundaries;
- modules;
- mathematical concepts;
- user/stakeholder workflow;
- CPU/GPU design;
- R interoperability;
- Persistent Optimization State;
- Event Detection;
- Impact Analysis;
- Active Decision Subgraph (ADS);
- Delta Re-optimization;
- Global Validation;
- Algorithm Harness;
- Solver Experience Dataset;
- benchmark methodology.

Do not redesign the architecture while implementing unless a concrete technical conflict is discovered. If a conflict is discovered, document it before changing behavior.

---

# 1. Non-negotiable implementation constraints

1. Python is the primary language.
2. Do not introduce C++.
3. The project must have its own mathematical optimization solver core.
4. Do not wrap CBC, HiGHS, SCIP, Gurobi, CPLEX, Xpress, OR-Tools or another complete optimizer as the production solver core.
5. NumPy and SciPy sparse numerical primitives may be used where appropriate.
6. CUDA, CuPy and Numba CUDA may be used for GPU numerical kernels.
7. R is auxiliary and optional.
8. Matplotlib is the primary scientific visualization system.
9. Sparse representations are mandatory for large models.
10. Never silently densify a large sparse matrix.
11. Full-model state must remain available for global validation.
12. Statistical estimates must never override mathematical feasibility.
13. GPU must not be assumed to be faster than CPU.
14. CPU/GPU selection must be measurable and explainable.
15. The initial Algorithm Harness must be deterministic/rule-based.
16. Do not begin with machine learning.
17. The learned Harness may only be introduced after sufficient Solver Experience Dataset data exists.
18. Every adaptive result must undergo global validation.
19. Failed validation must trigger ADS expansion or full-model fallback.
20. User overrides must become explicit mathematical events, bounds, constraints or objective changes.
21. Missing business data must never be fabricated.
22. Every completed phase must pass its testing gate before the next phase begins.
23. Existing passing tests must remain passing after every phase.
24. Use deterministic seeds for reproducible experiments.

---

# 2. Implementation philosophy

Do NOT:

```text
write every module
        ↓
run the application
        ↓
discover errors at the end
```

Instead:

```text
Architecture requirement
        ↓
Small implementation
        ↓
Unit tests
        ↓
Numerical tests
        ↓
Integration tests
        ↓
Performance tests where applicable
        ↓
Phase report
        ↓
PASS GATE
        ↓
Next phase
```

The repository must remain runnable after every phase.

---

# 3. Target repository

Create/maintain:

```text
project/
├── src/
│   ├── data_models.py
│   ├── data_loader.py
│   ├── supply_chain.py
│   ├── state.py
│   ├── change_detection.py
│   ├── impact_analysis.py
│   ├── active_graph.py
│   ├── delta_model.py
│   ├── delta_reoptimization.py
│   ├── harness.py
│   ├── validation.py
│   │
│   ├── solver/
│   │   ├── lp.py
│   │   ├── milp.py
│   │   ├── qp.py
│   │   ├── simplex.py
│   │   ├── interior_point.py
│   │   ├── branch_bound.py
│   │   ├── cuts.py
│   │   ├── heuristics.py
│   │   ├── sparse.py
│   │   ├── cpu.py
│   │   └── gpu.py
│   │
│   ├── analytics/
│   │   ├── statistics.py
│   │   ├── sensitivity.py
│   │   ├── scenario_analysis.py
│   │   ├── telemetry.py
│   │   └── r_bridge.py
│   │
│   └── visualization/
│       ├── plots.py
│       ├── supply_chain_plots.py
│       ├── solver_plots.py
│       └── scenario_plots.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── numerical/
│   ├── regression/
│   ├── performance/
│   ├── gpu/
│   └── fixtures/
│
├── datasets/
├── benchmarks/
├── examples/
├── results/
├── scripts/
├── docs/
├── architecture_supply_chain_v2.md
├── user.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

# 4. Testing infrastructure

Before substantive implementation, configure:

```text
pytest
ruff
mypy or pyright
```

where appropriate.

Create configurable numerical tolerances:

```text
absolute tolerance
relative tolerance
primal feasibility tolerance
dual feasibility tolerance
integrality tolerance
```

Create deterministic fixtures.

Every benchmark/experiment should record:

```text
Python version
OS
CPU
GPU
CUDA version
package versions
random seed
dataset version
solver version
git commit
```

---

# PHASE 0 — Repository and Test Infrastructure

## Implement

Create:

```text
src/
tests/
datasets/
benchmarks/
examples/
results/
scripts/
docs/
```

Create project configuration and test discovery.

## Test

Verify:

```text
imports
pytest discovery
fixture discovery
logging
configuration
```

## Acceptance gate

```text
pytest starts successfully
test suite executes
lint executes
type checking executes where configured
```

Do not proceed if infrastructure is unstable.

---

# PHASE 1 — Canonical Data Model

## Implement

Implement `src/data_models.py` as the single schema source.

Required types:

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

Keep this module free of:

```text
file downloads
solver execution
graph algorithms
optimization logic
```

## Tests

Test:

```text
construction
required fields
defaults
enum validation
serialization
deserialization
invalid values
NaN/Inf
invalid bounds
duplicate identifiers
```

Round trip:

```text
object
→ serialize
→ deserialize
→ equivalent object
```

## Acceptance gate

All schema and serialization tests pass.

---

# PHASE 2 — Data Loader

## Implement

Implement:

```python
load_instance(...)
load_dataset(...)
load_scenario(...)
load_timeseries(...)
load_solution(...)
normalize_model(...)
```

Initial formats/datasets:

```text
Netlib
MIPLIB
QPLIB
```

Then adapters:

```text
LogiOR
MIPcc23
ISOMORPH
dynamic/disruption datasets
```

Support where applicable:

```text
MPS
LP
QPLIB
CSV
JSON
Parquet
```

Requirements:

```text
preserve sparse matrices
preserve source metadata
preserve bounds
preserve objective
preserve integrality
support lazy/chunked time-series access
never silently densify large models
```

## Tests

Create small fixtures for:

```text
MPS
LP
QPLIB
CSV
JSON
Parquet
```

Verify:

```text
dimensions
nnz
objective
bounds
constraint senses
variable types
```

## Acceptance gate

At least one real representative instance from:

```text
Netlib
MIPLIB
QPLIB
```

loads successfully into the canonical model.

---

# PHASE 3 — Statistical Analytics

## Implement

`src/analytics/statistics.py`

Provide:

```text
mean
variance
std
CV
quantiles
rolling statistics
trend
correlation
demand risk
capacity utilization
capacity stress
inventory risk
service level
service gap
disruption severity
```

Implement sensitivity primitives needed later by impact analysis.

## Tests

Use synthetic datasets with analytically known results.

Examples:

```text
constant series
known mean/std
known quantiles
known correlation
known utilization
known service level
known demand variation
```

Cross-check selected functions with:

```text
NumPy
pandas
```

If R is available, selected reference calculations may also be compared.

## Acceptance gate

Statistical outputs pass analytical/reference tests.

---

# PHASE 4 — Supply-Chain Mathematical Model

## Implement

`src/supply_chain.py`

Represent:

```text
G = (V,E,T)
```

Support node types:

```text
supplier
plant
warehouse
DC
customer
port
market
```

Support edge types:

```text
supply
production
transport
shipment
flow
dependency
```

Map:

```text
graph components
↔ optimization variables
↔ optimization constraints
```

Build the reference application:

```text
Supplier
    ↓
Plant
    ↓
Warehouse
    ↓
Customer
```

Variables:

```text
production
shipment
inventory
shortage
```

Constraints:

```text
capacity
flow balance
inventory balance
demand fulfillment
service
```

## Tests

Test:

```text
flow conservation
capacity
demand balance
variable mapping
constraint mapping
time indexing
```

Create hand-calculated tiny examples.

## Acceptance gate

The tiny supply-chain model has a verified mathematical structure and expected feasibility behavior.

---

# PHASE 5 — Sparse Numerical Layer

## Implement

`src/solver/sparse.py`

Provide project-owned abstractions/utilities for:

```text
sparse matrices
vector operations
row/column access
slicing
submatrices
residual calculations
```

Use NumPy/SciPy sparse primitives where appropriate.

## Tests

Compare sparse operations against dense reference calculations on small matrices.

Test:

```text
A*x
A.T*x
row extraction
column extraction
submatrix extraction
residuals
```

Add a large sparse fixture and verify no unintended dense conversion.

## Acceptance gate

Sparse correctness passes and large sparse fixtures remain sparse.

---

# PHASE 6 — LP Solver Foundation

## Implement

Build the first project-owned CPU LP path.

Modules:

```text
src/solver/lp.py
src/solver/simplex.py
src/solver/interior_point.py
src/solver/cpu.py
```

Implement incrementally:

```text
model standardization
bounds
slack handling
revised simplex
basis representation
presolve hooks
termination
primal residual checks
```

Interior-point implementation can initially be an experimental path.

## Fixtures

Create:

```text
simple LP
degenerate LP
infeasible LP
unbounded LP
ill-conditioned LP
multiple-optimum LP
```

## Tests

Verify:

```text
objective
primal feasibility
bounds
termination status
```

Where applicable also verify:

```text
dual feasibility
reduced costs
```

Do not require exact variable vectors when multiple optima exist.

## External validation

Run a representative Netlib subset.

Compare:

```text
objective
feasibility
status
runtime
iterations
```

against trusted reference values.

## Acceptance gate

Small LP suite passes before large Netlib experiments are used.

---

# PHASE 7 — MILP Solver

## Implement

Modules:

```text
src/solver/milp.py
src/solver/branch_bound.py
src/solver/cuts.py
src/solver/heuristics.py
```

Start with:

```text
LP relaxation
branch-and-bound
incumbent
best bound
integrality checks
node selection
branch-variable selection
pruning
```

Then add:

```text
cut generation
primal heuristics
```

incrementally.

## Fixtures

Create known small:

```text
binary knapsack
integer knapsack
assignment
facility selection
transportation MILP
```

## Tests

Verify:

```text
integer feasibility
objective
incumbent updates
bounds
node processing
pruning
termination
MIP gap
```

## External validation

Run a representative MIPLIB benchmark subset.

Record:

```text
objective
best bound
gap
nodes
runtime
```

## Acceptance gate

All tiny MILP problems solve correctly before MIPLIB scaling.

---

# PHASE 8 — QP Solver

## Implement

`src/solver/qp.py`

Start with convex QP:

```text
quadratic objective
linear constraints
bounds
```

Create known small fixtures:

```text
diagonal convex QP
constrained convex QP
small coupled convex QP
```

Then test representative QPLIB instances.

## Acceptance gate

Known QP objectives and feasibility match reference values within tolerance.

---

# PHASE 9 — Persistent Optimization State

## Implement

`src/state.py`

Implement:

```python
create_state()
update_state()
serialize_state()
restore_state()
validate_state()
```

Persist:

```text
model version
previous solution
objective
feasibility
optimality
warm start
incumbent
basis where available
LP relaxation state where available
cut metadata where available
node statistics
variable activity
constraint activity
sensitivity
event history
solve history
```

State must be versioned.

## Tests

Test:

```text
solve
→ save
→ reload
→ equivalent state
```

Also test incompatible states:

```text
model version mismatch
variable mismatch
constraint mismatch
```

These must fail safely.

## Acceptance gate

State can be persisted/restored without mathematical corruption.

---

# PHASE 10 — Event / Change Detection

## Implement

`src/change_detection.py`

Support:

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

Each event must map to:

```text
entities
products
periods
variables
constraints
old values
new values
magnitude
```

Use configurable absolute and relative thresholds.

## Tests

Test:

```text
no change
below threshold
at threshold
above threshold
route block
facility outage
multi-event
```

## Acceptance gate

Event detection is deterministic and correctly maps events to model/graph components.

---

# PHASE 11 — Impact Analysis

## Implement

`src/impact_analysis.py`

Use the architecture's hybrid relevance model:

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

Implement a transparent relevance score.

For event `q` and component `v`:

```text
R(q,v) =
    wd * dependency_strength
  + ws * shared_resource
  + wc * shared_constraint
  + wt * temporal_overlap
  + wf * flow_dependency
  + wh * historical_coupling
  + wp * propagation_probability
  + wg * distance_score
```

The exact weights must be configurable.

Return:

```text
component
score
reason
feature contributions
```

## Tests

Create hand-built graphs demonstrating:

```text
direct dependency
shared resource
shared constraint
temporal overlap
historical coupling
unrelated node
```

Verify graph distance is not the only decision signal.

## Acceptance gate

Expected components receive higher relevance in deterministic test cases.

---

# PHASE 12 — Active Decision Subgraph

## Implement

`src/active_graph.py`

Pipeline:

```text
event
→ changed components
→ seed region
→ dependency expansion
→ shared-resource expansion
→ shared-constraint expansion
→ temporal expansion
→ sensitivity expansion
→ historical expansion
→ thresholding
→ boundary completion
```

Return:

```text
ActiveRegion
```

containing:

```text
nodes
edges
variables
constraints
boundary conditions
```

## Tests

Test:

```text
local demand change
shared capacity
shared constraint
route disruption
temporal dependency
boundary dependency
ADS expansion
invalid reference protection
```

## Critical safety test

A component that is mathematically required through a linking constraint must not be silently omitted.

## Acceptance gate

ADS is deterministic for fixed input and contains complete required boundary information.

---

# PHASE 13 — Delta Model

## Implement

`src/delta_model.py`

Implement:

```text
ModelBase
ModelDelta
ActiveIndexMap
BoundaryState
```

Represent:

```text
M_(t+1) = M_t + Delta M
```

without unnecessary full-model copying.

## Tests

For small models compare:

```text
base model + delta model
```

against:

```text
explicitly rebuilt changed model
```

Compare:

```text
A
b
c
bounds
variable types
constraint senses
```

## Acceptance gate

Delta representation is mathematically equivalent to explicit changed-model reconstruction.

---

# PHASE 14 — Global Validation

## Implement

`src/validation.py`

Check:

```text
constraint feasibility
variable bounds
integrality
linking constraints
service requirements
route constraints
facility constraints
objective consistency
```

Use:

```text
A x <= b
l <= x <= u
```

with configurable tolerances.

## Tests

Create:

```text
valid solution
constraint violation
bound violation
integrality violation
service violation
linking violation
objective inconsistency
```

## Critical test

Create an intentionally incomplete ADS solution that violates a constraint outside the active region.

Expected:

```text
global validation = FAIL
```

## Acceptance gate

No adaptive solution can be accepted without full-model validation.

---

# PHASE 15 — Delta Re-optimization

## Implement

`src/delta_reoptimization.py`

Required runtime:

```text
previous state
→ new data
→ event detection
→ impact analysis
→ ADS
→ delta model
→ persistent-state warm start
→ Harness
→ CPU/GPU solver
→ global reconstruction
→ global validation
```

If validation fails:

```text
violations
→ affected variables
→ affected graph entities
→ ADS expansion
→ rebuild
→ reoptimize
```

If required:

```text
ADS = full model
→ full solve
```

## Tests

Scenario 1:

```text
local demand change
```

Scenario 2:

```text
shared capacity change
```

Scenario 3:

```text
route disruption
```

Scenario 4:

```text
global coupling
```

Scenario 5:

```text
forced validation failure
```

Scenario 6:

```text
full-model fallback
```

## Most important correctness test

For deterministic small problems:

```text
adaptive result
vs
full solve on changed model
```

must agree within configured optimization tolerances.

## Acceptance gate

Adaptive reoptimization is mathematically equivalent to the validated full solve for deterministic fixtures.

---

# PHASE 16 — CPU Optimization Backend

## Implement

`src/solver/cpu.py`

Create a common solver interface:

```python
solve(model, options, state=None)
```

Use:

```text
NumPy
SciPy sparse numerical primitives where appropriate
Python numerical kernels
safe CPU parallelism
```

CPU should be preferred for:

```text
small models
small ADS
irregular workloads
branch-and-bound control
GPU-transfer-dominated workloads
```

## Tests

Compare:

```text
direct CPU
vs
Harness-selected CPU
```

Verify mathematical equivalence.

Measure:

```text
runtime
memory
iterations
nodes
```

## Acceptance gate

CPU backend passes numerical and integration tests.

---

# PHASE 17 — CUDA GPU Backend

## Implement

`src/solver/gpu.py`

Use:

```text
CUDA
CuPy
Numba CUDA
```

Start with GPU-suitable operations:

```text
vector operations
sparse matrix-vector products
residual calculations
batched scenario calculations
selected sparse linear algebra
large active-region numerical kernels
```

Do not move irregular branch-and-bound control to GPU prematurely.

## Tests

When CUDA is available:

```text
same model
→ CPU
→ GPU
```

Compare:

```text
objective
feasibility
residuals
solution where appropriate
```

If CUDA is unavailable:

```text
GPU tests = SKIP
```

not FAIL.

## Performance tests

Measure separately:

```text
host-to-device transfer
kernel execution
device-to-host transfer
total GPU runtime
CPU runtime
```

Calculate:

```text
speedup = CPU_time / total_GPU_time
```

Do not claim GPU acceleration using kernel-only time.

## Acceptance gate

GPU numerical equivalence passes before GPU performance claims are made.

---

# PHASE 18 — Algorithm Harness

## Implement

`src/harness.py`

Initial Harness must be deterministic/rule-based.

Features:

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
branching policy
node selection
parallelism
```

Every decision must include an explanation.

## Tests

Synthetic signatures:

```text
small LP → CPU
small ADS → CPU
large sparse numerical workload → GPU candidate
irregular MILP → CPU candidate
```

Verify deterministic decisions.

## Acceptance gate

Harness produces deterministic, explainable decisions.

---

# PHASE 19 — Scenario Analysis

## Implement

`src/analytics/scenario_analysis.py`

Support:

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

Each scenario stores:

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

## Tests

Use known changes and verify expected metric differences.

## Acceptance gate

Scenario comparisons are reproducible and consistent with the underlying solutions.

---

# PHASE 20 — Matplotlib Visualization

## Implement

```text
src/visualization/plots.py
src/visualization/supply_chain_plots.py
src/visualization/solver_plots.py
src/visualization/scenario_plots.py
```

Required visualizations:

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

## Tests

Use a non-interactive backend.

Verify:

```text
figure creation
axes
expected data series
file export
```

Critical:

```text
visualization must not mutate solver state
```

## Acceptance gate

Visualization tests pass and generated figures contain expected information.

---

# PHASE 21 — R Analytics Bridge

## Implement

`src/analytics/r_bridge.py`

R remains optional.

Support:

```text
R availability detection
data export
R analysis execution
result import
error handling
```

Use R for:

```text
statistical inference
time-series analysis
distribution fitting
uncertainty analysis
research diagnostics
```

Preferred interface:

```text
Python
→ CSV/Parquet/JSON
→ R
→ result files
→ Python
```

The optimization loop must work without R.

## Tests

Without R:

```text
system continues normally
```

With R:

```text
small analysis executes
result schema validates
```

## Acceptance gate

R is optional and cannot become a critical dependency.

---

# PHASE 22 — Solver Telemetry

## Implement

`src/analytics/telemetry.py`

Record:

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

Store:

```text
Parquet
```

## Tests

```text
create telemetry
→ write Parquet
→ read Parquet
→ validate schema
→ compare values
```

## Acceptance gate

Telemetry is reproducible and complete enough to train/evaluate the future Harness.

---

# PHASE 23 — Reference End-to-End Application

Build the first complete application:

```text
Supplier
    ↓
Plant
    ↓
Warehouse
    ↓
Customer
```

User provides:

```text
demand
capacity
inventory
routes
cost
service target
planning horizon
```

Run:

```text
input validation
→ statistics
→ base optimization
→ persistent state
→ Matplotlib visualization
→ user disruption
→ event detection
→ impact analysis
→ ADS
→ Harness
→ CPU/GPU
→ delta model
→ adaptive solve
→ global validation
→ ADS expansion if necessary
→ scenario comparison
→ telemetry
```

## End-to-end test

One reproducible command should execute the entire flow.

## Acceptance gate

Complete reference application passes from user input to validated adaptive scenario result.

---

# PHASE 24 — Real Dataset Validation

Validate real datasets progressively.

## Netlib

Use a representative subset first.

Record:

```text
load status
n
m
nnz
solve status
objective
runtime
memory
numerical diagnostics
```

## MIPLIB

Start with benchmark subset.

Record:

```text
objective
best bound
MIP gap
nodes
runtime
status
```

## QPLIB

Start with smaller/appropriate convex instances.

## LogiOR

Use application-oriented mathematical examples.

## MIPcc23 / dynamic MIP data

Use for dynamic and reoptimization experiments.

## ISOMORPH

Do not load the complete large release into memory.

Use:

```text
selected rollouts
streaming
chunked processing
```

## Acceptance gate

Produce a dataset validation report without crashing or silently corrupting data.

---

# PHASE 25 — Adaptive Optimization Research Benchmark

For every dynamic base/scenario pair compare:

```text
A — Full solve from scratch

B — Persistent-state full solve

C — ADS + delta reoptimization

D — ADS + delta + Algorithm Harness
```

Measure:

```text
solve time
objective
gap
iterations
branch nodes
memory
active fraction
expansion count
validation time
CPU/GPU
```

Report:

```text
mean
median
std
IQR
p5
p95
paired speedup
bootstrap confidence interval
effect size
```

Safety metrics:

```text
validation success
fallback frequency
```

Do not report a speedup from unpaired runs.

## Acceptance gate

A reproducible benchmark report exists comparing all four approaches.

---

# PHASE 26 — Regression and Reliability Freeze

Create permanent regression tests for every discovered issue:

```text
data loader
model mapping
numerical solver
state
event detection
impact analysis
ADS
delta model
validation
Harness
CPU/GPU
visualization
R bridge
telemetry
```

Every future change must pass:

```text
unit
integration
numerical
regression
```

before performance conclusions are updated.

## Acceptance gate

Regression suite is stable and reproducible.

---

# PHASE 27 — Learned Algorithm Harness

Only start this phase after:

```text
solver core works
ADS works
delta reoptimization works
CPU/GPU backends work
Harness works
telemetry works
sufficient experience records exist
```

Pipeline:

```text
Solver Experience Dataset
→ feature cleaning
→ train/validation/test split
→ learned strategy model
→ offline evaluation
→ shadow mode
→ safety filter
→ controlled deployment
```

The learned policy estimates something such as:

```text
P(strategy | model, state, event)
```

It must never bypass:

```text
numerical safeguards
global validation
hard safety rules
full-solve fallback
```

If uncertain:

```text
deterministic Harness wins
```

## Acceptance gate

The learned Harness must demonstrate improvement against the deterministic Harness on held-out data without reducing correctness.

---

# 5. Required test architecture

Maintain:

```text
tests/
├── unit/
├── integration/
├── numerical/
├── regression/
├── performance/
├── gpu/
└── fixtures/
```

## Unit tests

One module/function at a time.

## Integration tests

Examples:

```text
loader → model
model → graph
event → impact → ADS
ADS → delta
delta → solver
solver → validation
solver → telemetry
```

## Numerical tests

Use known small mathematical problems.

## Regression tests

Every fixed defect becomes a permanent test.

## Performance tests

Separate from correctness.

## GPU tests

Skip cleanly when CUDA is unavailable.

## E2E tests

Exercise the complete user workflow.

---

# 6. Mandatory mathematical invariants

These must remain true throughout the project.

## Invariant 1 — Model equivalence

The delta model must represent the same changed model as explicit reconstruction.

## Invariant 2 — Feasibility

Accepted solutions satisfy all required constraints.

## Invariant 3 — Integrality

Integer/binary variables satisfy integrality tolerance.

## Invariant 4 — State compatibility

Warm starts are used only with compatible model/state versions.

## Invariant 5 — ADS boundary completeness

Required external dependencies cannot be silently dropped.

## Invariant 6 — Global validation

No adaptive solution is accepted without full-model validation.

## Invariant 7 — CPU/GPU equivalence

Equivalent CPU/GPU computations produce mathematically consistent results within tolerance.

## Invariant 8 — Human override traceability

Every human override becomes an explicit mathematical modification.

## Invariant 9 — Statistics cannot override feasibility

Statistical recommendations cannot make an infeasible solution acceptable.

---

# 7. Phase completion report

After every phase create:

```text
results/phases/phase_XX_report.md
```

Use:

```text
PHASE:
DATE:
GIT COMMIT:

OBJECTIVE:
...

IMPLEMENTED:
...

TESTS EXECUTED:
...

TESTS PASSED:
...

TESTS FAILED:
...

NUMERICAL VALIDATION:
...

PERFORMANCE:
...

DATASETS:
...

KNOWN LIMITATIONS:
...

REGRESSIONS:
...

NEXT PHASE:
...

STATUS:
PASS / FAIL
```

A phase marked FAIL must not be treated as complete.

---

# 8. Development order summary

The implementation order is:

```text
Phase 0
Repository + testing infrastructure

Phase 1
Canonical schemas

Phase 2
Data loader

Phase 3
Statistics

Phase 4
Supply-chain model

Phase 5
Sparse numerical layer

Phase 6
LP

Phase 7
MILP

Phase 8
QP

Phase 9
Persistent state

Phase 10
Event detection

Phase 11
Impact analysis

Phase 12
ADS

Phase 13
Delta model

Phase 14
Global validation

Phase 15
Delta reoptimization

Phase 16
CPU backend

Phase 17
GPU backend

Phase 18
Algorithm Harness

Phase 19
Scenario analysis

Phase 20
Matplotlib

Phase 21
R bridge

Phase 22
Telemetry

Phase 23
End-to-end application

Phase 24
Real datasets

Phase 25
Research benchmark

Phase 26
Regression freeze

Phase 27
Learned Harness
```

---

# 9. Critical rule for the coding agent

At the start of each phase:

1. Read the corresponding architecture sections.
2. Inspect existing implementation.
3. Inspect existing tests.
4. Implement only the current phase and necessary dependencies.
5. Add tests immediately.
6. Run the relevant test suite.
7. Fix failures.
8. Run regression tests.
9. Generate the phase report.
10. Only then proceed.

Do not create placeholder implementations that pretend a solver is complete.

Do not mark functionality as implemented merely because a function exists.

For example:

```text
def solve(...):
    pass
```

is not an implementation.

Similarly, do not use:

```text
random solution
fake objective
hard-coded benchmark result
mocked solver result
```

to claim optimization correctness.

Mocks may be used only for testing interfaces where mathematically valid behavior is not the subject of the test.

---

# 10. Final system acceptance test

The complete system must eventually pass:

```text
Stakeholder objective
        ↓
Operational data
        ↓
Validation
        ↓
Canonical model
        ↓
Statistics
        ↓
Base LP/MILP/QP solve
        ↓
Persistent state
        ↓
Matplotlib visualization
        ↓
Stakeholder creates what-if scenario
        ↓
Event detection
        ↓
Impact analysis
        ↓
Active Decision Subgraph
        ↓
Delta model
        ↓
Algorithm Harness
        ↓
CPU/GPU solver
        ↓
Global validation
        ↓
      PASS?
       /   \
     YES    NO
      |      |
      |    ADS expansion
      |      ↓
      |    reoptimization
      |      ↓
      +------+
        ↓
Scenario comparison
        ↓
Telemetry
        ↓
Human approval / modification / rejection
        ↓
Next optimization cycle
```

The central research experiment is:

```text
FULL REOPTIMIZATION
        VS
PERSISTENT-STATE REOPTIMIZATION
        VS
ADS + DELTA REOPTIMIZATION
        VS
ADS + DELTA + ALGORITHM HARNESS
```

The research claim is valid only when:

```text
mathematical correctness
+
global validation
+
reproducibility
+
paired benchmark evaluation
+
statistical evidence
```

are all demonstrated.

The final product is a **state-aware adaptive mathematical optimization decision engine**, not merely a solver, dashboard, or machine-learning system.
