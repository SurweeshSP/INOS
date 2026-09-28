# Indigenous Adaptive Optimization Solver — Updated Architecture

## 1. Purpose

This architecture defines the complete Python-first optimization system for the Indigenous Optimization Solver, integrating:

- LP, MILP and QP solver foundations;
- CPU and CUDA GPU optimization execution;
- supply-chain mathematical modeling;
- statistical analysis;
- R-based statistical/analytical interoperability;
- Matplotlib-based visualization;
- Persistent Optimization State;
- Event/Change Detection;
- Active Decision Subgraph (ADS);
- Delta Re-optimization;
- global validation;
- Algorithm Harness;
- Solver Experience Dataset;
- stakeholder/user workflow;
- scenario and what-if analysis.

The original PS requires a sovereign optimization core for LP, MILP and QP, sparse numerical methods, CPU/GPU acceleration where beneficial, industrial-scale optimization and recognized benchmark validation. The current data inventory contains MIPLIB, Netlib, QPLIB, LogiOR, ISOMORPH and dynamic/reoptimization data.

The central research idea is:

> The system converts stakeholder decisions, operational data and scenario changes into mathematical optimization models; detects which part of the decision system is affected; selects an appropriate CPU/GPU optimization strategy; reuses persistent solver state; solves the active region; validates against the complete model; expands when necessary; and presents mathematically grounded results and visualizations for human decision-making.

---

# 2. Design Principle: Human → Analytics → Optimization → Decision

The application must not expose raw mathematical complexity to normal users.

```text
USER / STAKEHOLDER
       |
       | Business inputs
       v
INPUT & SCENARIO LAYER
       |
       v
DATA VALIDATION / NORMALIZATION
       |
       +------------------+
       |                  |
       v                  v
STATISTICAL ANALYSIS     BASE MODEL
Python / R               LP / MILP / QP
       |                  |
       +--------+---------+
                v
        PERSISTENT STATE
                |
                v
         CHANGE DETECTION
                |
                v
        IMPACT / RELEVANCE
                |
                v
   ACTIVE DECISION SUBGRAPH
                |
                v
       ALGORITHM HARNESS
          /           \
       CPU             GPU
                |
                v
          SOLVER CORE
        LP / MILP / QP
                |
                v
        GLOBAL VALIDATION
                |
          +-----+-----+
          |           |
        valid       invalid
          |           |
          v           v
      RESULT      EXPAND ADS
          |           |
          +-----<-----+
                |
                v
       DECISION ANALYTICS
                |
       +--------+---------+
       |                  |
       v                  v
   Matplotlib           R
 visualization      statistical analysis
       |                  |
       +--------+---------+
                v
       STAKEHOLDER DECISION
                |
                v
      APPROVE / MODIFY / REJECT
                |
                v
       NEW SCENARIO / EVENT
```

---

# 3. User and Stakeholder Roles

The system supports multiple roles without requiring each role to understand optimization mathematics.

## 3.1 Executive / decision maker

Provides:

- business objective;
- target service level;
- budget;
- strategic priorities;
- acceptable risk;
- scenario to evaluate.

Receives:

- recommended decision;
- expected cost/profit;
- service level;
- risk;
- capacity utilization;
- scenario comparison;
- major constraints;
- sensitivity/explanation.

## 3.2 Supply-chain planner

Provides:

- demand;
- inventory targets;
- production capacity;
- procurement limits;
- transportation availability;
- lead times;
- warehouse constraints;
- planning horizon;
- product priorities.

Receives:

- production plan;
- procurement plan;
- shipment plan;
- inventory plan;
- facility utilization;
- bottlenecks;
- shortage/backlog;
- alternative scenarios.

## 3.3 Operations / plant manager

Provides:

- equipment/facility availability;
- production capacity;
- maintenance outage;
- operating limits;
- resource availability;
- process constraints.

Receives:

- feasible operating plan;
- resource loading;
- bottlenecks;
- impact of outages;
- recovery alternatives.

## 3.4 Logistics manager

Provides:

- route availability;
- transportation capacity;
- costs;
- lead times;
- fleet/vehicle availability;
- route disruption.

Receives:

- routing/flow decisions;
- shipment allocation;
- affected network region;
- alternative routes;
- service impact.

## 3.5 Data / optimization engineer

Provides:

- mathematical model;
- datasets;
- variable/constraint mappings;
- solver configuration;
- numerical tolerances;
- benchmark configuration.

Receives:

- solver telemetry;
- numerical diagnostics;
- sensitivity;
- algorithm choice;
- active-region statistics;
- benchmark results.

## 3.6 Analyst / researcher

Provides:

- historical data;
- scenarios;
- statistical assumptions;
- experiment definitions.

Receives:

- distributions;
- correlations;
- scenario statistics;
- solver performance;
- confidence intervals;
- comparative experiments.

---

# 4. What the User Actually Inputs

The application should support three input modes.

## Mode A — Business / application input

The user should not have to write LP/MILP equations.

Example:

```text
Planning horizon: 12 weeks

Demand:
Product A = 12,000 units/week
Product B = 8,000 units/week

Factory:
F1 capacity = 20,000 units/week
F2 capacity = 15,000 units/week

Warehouse:
W1 capacity = 10,000 units
W2 capacity = 12,000 units

Transport:
Route F1-W1 = available
Route F1-W2 = available
Route F2-W1 = unavailable

Objective:
Minimize total cost

Service requirement:
>= 95%
```

The application converts this into the canonical mathematical model.

## Mode B — Data-driven input

The user provides:

```text
CSV
Parquet
JSON
Excel
MPS
LP
QPLIB
```

or connected operational datasets.

The loader validates and normalizes the data.

## Mode C — Event / what-if input

After a base plan exists, the user can say:

```text
Increase demand for Product A by 15%.
```

or:

```text
Disable Warehouse W2 for week 8.
```

or:

```text
Reduce Plant F1 capacity by 20% for two weeks.
```

or:

```text
Block route F1-W1.
```

or:

```text
Increase transport cost on Route R17 by 10%.
```

The system converts this into an explicit Event.

---

# 5. Input Contract

Every application input should ultimately normalize to:

```text
InputRequest
    request_id
    application
    user_role
    objective
    horizon
    entities
    products
    demand
    capacity
    costs
    routes
    inventory
    service_targets
    constraints
    events
    scenario_parameters
    uncertainty_parameters
    requested_outputs
```

The user may provide only a subset.

The application fills only values that are explicitly configured or available from the connected dataset. It must not silently invent operational values.

---

# 6. Application Workflow

## Step 1 — Define objective

The user selects:

```text
Minimize cost
Maximize profit
Maximize service
Minimize shortage
Minimize emissions
Minimize risk
Multi-objective
```

Multi-objective optimization must expose weights/priorities explicitly.

Example:

```text
70% cost
20% service
10% emissions
```

## Step 2 — Define constraints

User configures:

```text
capacity
inventory
demand fulfillment
service
budget
route availability
facility availability
production limits
resource limits
policy constraints
```

## Step 3 — Load data

The system validates:

```text
missing values
invalid bounds
negative capacities
duplicate IDs
unknown entities
inconsistent time periods
NaN/Inf
dimension mismatch
```

## Step 4 — Build/choose model

The application creates:

```text
SupplyChainGraph
+
OptimizationModel
```

## Step 5 — Analyze current state

Statistics calculate:

```text
demand variability
capacity utilization
inventory risk
service risk
bottleneck indicators
scenario severity
```

## Step 6 — Optimize

The Algorithm Harness chooses:

```text
LP / MILP / QP algorithm
CPU/GPU mode
presolve
warm start
cuts
heuristics
parallelism
```

## Step 7 — Validate

The complete model is checked.

## Step 8 — Explain

The application presents:

```text
recommended plan
objective
cost
service
inventory
capacity
bottlenecks
risk
affected region
scenario differences
```

## Step 9 — Human decision

Stakeholder chooses:

```text
APPROVE
MODIFY
RUN ANOTHER SCENARIO
REJECT
```

The decision becomes part of scenario/experiment history.

---

# 7. CPU and GPU Optimization Architecture

The solver must have two execution backends.

```text
                  Algorithm Harness
                         |
              +----------+----------+
              |                     |
          CPU Backend           GPU Backend
              |                     |
       NumPy / SciPy*         CuPy / Numba CUDA
              |                     |
       Sparse numerical       GPU sparse kernels
       factorization         vector operations
       simplex/IP work        selected linear algebra
              |                     |
              +----------+----------+
                         |
                    Solver Core
```

`*` SciPy may be used for numerical primitives/utilities during development, but the optimization solver core itself must remain project-owned and built from mathematical foundations rather than wrapping an existing complete optimization solver.

## CPU

Use:

- NumPy;
- SciPy sparse numerical structures/primitives where appropriate;
- multiprocessing/threading where safe;
- optimized Python numerical kernels;
- sparse data structures.

CPU is preferred when:

- models are small/medium;
- active regions are small;
- GPU transfer cost dominates;
- operations are irregular;
- branch-and-bound control is more efficient on CPU.

## GPU

Use:

- CUDA;
- CuPy;
- Numba CUDA;
- GPU-compatible sparse/vector kernels.

GPU candidates:

- sparse matrix-vector operations;
- batched vector operations;
- residual calculations;
- reduced-cost/slack calculations;
- parallel scenario evaluation;
- selected factorization/linear algebra kernels;
- large active-region numerical operations.

GPU is not automatically selected.

The Harness estimates GPU suitability from:

```text
matrix size
nnz
sparsity
batch size
active-region size
operation intensity
transfer cost
historical GPU speedup
```

Then measures actual performance.

---

# 8. R Integration

R is an auxiliary analytics layer, not the solver core.

Python remains the system orchestration language.

R may be used for:

- statistical inference;
- distribution fitting;
- time-series analysis;
- uncertainty analysis;
- advanced statistical diagnostics;
- research reporting.

Recommended interface:

```text
Python
  |
  +--> parquet/csv/json
  |
  +--> R analysis scripts
  |
  +--> results/metrics
  |
  v
Python visualization/reporting
```

Prefer file/API boundaries over embedding R in the critical optimization loop.

R analysis must never block or modify the mathematical solver state unless explicitly requested.

---

# 9. Matplotlib Visualization

Matplotlib is the primary scientific visualization layer.

Create:

```text
src/visualization/
    plots.py
    supply_chain_plots.py
    solver_plots.py
    scenario_plots.py
```

Required visualizations:

## Supply-chain

- network topology;
- flow;
- inventory;
- capacity utilization;
- bottlenecks;
- service level;
- shortages;
- route utilization.

## Optimization

- objective convergence;
- primal/dual residual;
- MIP gap;
- branch-and-bound nodes;
- cut counts;
- iteration counts;
- solve-time distribution.

## Adaptive solver

- full vs active model size;
- active-region percentage;
- ADS expansion;
- speedup;
- validation failures;
- scenario impact;
- CPU vs GPU runtime.

## Statistical

- demand distributions;
- rolling demand;
- capacity stress;
- inventory risk;
- correlation;
- scenario severity;
- sensitivity ranking.

Visualization must never alter optimization results.

---

# 10. Persistent Optimization State

Maintain:

```text
model_version
previous_solution
objective
feasibility
optimality
warm_start
incumbent
basis (optional)
LP relaxation state (optional)
cut metadata (optional)
node statistics
variable activity
constraint activity
sensitivity
event history
solve history
```

The state allows the next scenario to begin from the previous solution rather than treating it as unrelated.

---

# 11. Event and Change Detection

Every change becomes:

```text
Event
    type
    affected entities
    affected variables
    affected constraints
    affected periods
    old value
    new value
    magnitude
```

Examples:

```text
Demand +15%
Capacity -20%
Facility down
Route blocked
Cost +10%
New order
Inventory shock
```

---

# 12. Statistical Impact Model

For event q and candidate component v:

```text
R(q,v) =
    wd dependency_strength
  + ws shared_resource
  + wc shared_constraint
  + wt temporal_overlap
  + wf flow_dependency
  + wh historical_coupling
  + wp propagation_probability
  + wg distance_score
```

Use graph distance only as one feature.

The relevance model combines:

- physical network structure;
- mathematical coupling;
- statistical sensitivity;
- historical solver experience.

---

# 13. Active Decision Subgraph

```text
event
 ↓
changed components
 ↓
seed region
 ↓
dependency expansion
 ↓
shared resource/constraint expansion
 ↓
temporal expansion
 ↓
sensitivity expansion
 ↓
historical expansion
 ↓
boundary completion
 ↓
Active Decision Subgraph
```

The ADS contains:

```text
nodes
edges
variables
constraints
boundary conditions
```

---

# 14. Delta Re-optimization

Given:

```text
M_t
Delta M
```

construct:

```text
M_(t+1) = M_t + Delta M
```

without unnecessarily copying the entire model.

Solve the active region using:

```text
previous solution
warm start
incumbent
basis/LP state where available
```

Then reconstruct the global solution.

---

# 15. Global Validation

Always validate against the full changed model.

Check:

```text
A x <= b
l <= x <= u
integrality
service constraints
linking constraints
route/facility rules
objective consistency
```

If validation fails:

```text
violated constraints
→ affected variables
→ affected graph entities
→ ADS expansion
→ reoptimization
```

If necessary:

```text
ADS = full model
```

This is the mathematical safety fallback.

---

# 16. Algorithm Harness

The Harness selects:

```text
solver algorithm
CPU/GPU
presolve
warm-start policy
cut policy
heuristic policy
branching
node selection
parallelism
```

Initial implementation is rule-based.

Later it learns:

```text
P(strategy | model, state, event)
```

from the Solver Experience Dataset.

---

# 17. Solver Experience Dataset

Each solve records:

```text
model signature
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
validation
expansion count
```

This dataset supports future learned solver strategies.

---

# 18. Supply-Chain Application Templates

The same engine should support:

## Production planning

```text
Inputs:
demand
production capacity
labor/resources
inventory
costs
horizon

Outputs:
production quantity
inventory
shortage
resource utilization
cost
```

## Distribution planning

```text
Inputs:
warehouses
customers
demand
routes
transport capacity
cost
lead time

Outputs:
shipments
route utilization
service
transport cost
```

## Network disruption

```text
Inputs:
network
facility availability
route availability
disruption

Outputs:
affected region
alternate flows
service impact
cost impact
recovery plan
```

## Inventory planning

```text
Inputs:
demand distribution
lead time
holding cost
shortage cost
capacity
service target

Outputs:
order quantity
inventory trajectory
risk
service level
```

## Integrated supply chain

Combine:

```text
procurement
production
inventory
transport
distribution
service
```

into one mathematical model.

---

# 19. User Decision Loop

The application must support iterative decision making.

```text
USER
 |
 v
BASE PLAN
 |
 v
RESULT + VISUALIZATION
 |
 v
USER CHANGES ASSUMPTION
 |
 v
EVENT
 |
 v
ADS + DELTA REOPTIMIZATION
 |
 v
NEW RESULT
 |
 v
SCENARIO COMPARISON
 |
 v
USER APPROVES / MODIFIES
 |
 v
OPERATING PLAN
 |
 v
NEW OPERATIONAL DATA
 |
 `----> next optimization cycle
```

This makes the system an operational decision engine rather than a one-shot solver.

---

# 20. Scenario Comparison

Every scenario should be compared against the selected baseline.

Report:

```text
objective delta
cost delta
service delta
inventory delta
capacity delta
shortage delta
risk delta
emissions delta
solve-time delta
active-region size
```

Visualization should make trade-offs clear.

---

# 21. Human Override

The optimizer recommends a mathematically feasible solution.

Authorized users may impose an additional business constraint or modify a parameter.

A manual override must be represented as:

```text
new constraint
new bound
new event
new objective weight
```

and sent back through validation/reoptimization.

Never silently modify solver output outside the mathematical model.

---

# 22. Data Governance

Every scenario must retain:

```text
source
timestamp
user/role
model version
data version
event
random seed
solver version
harness decision
solution
validation result
```

This supports reproducibility and auditability.

---

# 23. Implementation Structure

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

---

# 24. Technology Responsibilities

| Technology | Responsibility |
|---|---|
| Python | Main application, orchestration, data layer, solver, ADS, Harness |
| NumPy | Numerical arrays |
| SciPy sparse | Sparse mathematical structures/primitives |
| CUDA | GPU execution |
| CuPy | GPU array operations |
| Numba CUDA | Custom GPU kernels |
| pandas | tabular analysis |
| Parquet | large datasets/telemetry |
| NetworkX initially | graph prototyping |
| Custom sparse graph structures later | large-scale graph execution |
| R | auxiliary statistical analysis/inference |
| Matplotlib | scientific visualization |
| pytest | testing |
| PyTorch/scikit-learn | future learned Harness only |

---

# 25. First End-to-End Application

Implement one integrated supply-chain example before supporting every application.

Example:

```text
Supplier
   ↓
Plant
   ↓
Warehouse
   ↓
Customer
```

User enters:

```text
demand
capacity
cost
inventory
routes
service target
planning horizon
```

System:

```text
1. validates data
2. builds model
3. computes statistics
4. solves base model
5. stores persistent state
6. visualizes plan
7. user introduces disruption
8. detects event
9. constructs ADS
10. chooses CPU/GPU strategy
11. delta-reoptimizes
12. globally validates
13. expands if needed
14. compares scenarios
15. visualizes result
16. records telemetry
```

This is the reference application flow.

---

# 26. Benchmark and Research Evaluation

Compare:

```text
Full solve from scratch
vs
Persistent-state reoptimization
vs
ADS + delta reoptimization
vs
ADS + delta + Harness
```

Metrics:

```text
solve time
iterations
branch nodes
memory
objective
MIP gap
active fraction
expansion count
validation time
CPU/GPU time
speedup
```

Statistical reporting:

```text
mean
median
std
IQR
p5
p95
paired comparisons
bootstrap confidence intervals
effect size
```

---

# 27. Research Claims to Test

H1: Localized events can be solved with a smaller active mathematical region.

H2: Decision relevance is more informative than graph distance alone.

H3: Persistent state reduces computational work during sequential optimization.

H4: Global validation plus adaptive expansion preserves correctness.

H5: The Algorithm Harness improves performance over fixed solver policies.

H6: CPU/GPU selection should be adaptive rather than GPU-by-default.

H7: Statistical risk/sensitivity signals improve active-region selection.

H8: Human scenario interaction can be converted into reproducible mathematical events and reoptimization episodes.

---

# 28. Implementation Priority

```text
Phase 1
  data_models
  data_loader
  statistics
  tests

Phase 2
  supply-chain graph
  model mapping
  base LP/MILP/QP integration

Phase 3
  persistent state
  event detection
  impact analysis
  ADS

Phase 4
  delta model
  global validation
  expansion

Phase 5
  CPU/GPU execution
  Algorithm Harness

Phase 6
  Matplotlib visualization
  R statistical bridge

Phase 7
  dynamic scenario benchmark
  telemetry
  Solver Experience Dataset

Phase 8
  learned Harness
  advanced industrial applications
```

Do not begin with the learned Harness.

---

# 29. Final System Definition

The completed system is:

```text
                HUMAN / STAKEHOLDER
                        |
                  Business intent
                        |
                        v
              APPLICATION INPUT
                        |
                        v
             DATA + MODEL LAYER
                        |
          +-------------+-------------+
          |                           |
          v                           v
    STATISTICS / R              OPTIMIZATION MODEL
          |                           |
          +-------------+-------------+
                        |
                PERSISTENT STATE
                        |
                        v
                  EVENT DELTA
                        |
                        v
                IMPACT ANALYSIS
                        |
                        v
             ACTIVE DECISION SUBGRAPH
                        |
                        v
                 DELTA MODEL
                        |
                        v
                ALGORITHM HARNESS
                   /          \
                 CPU          GPU
                   \          /
                    SOLVER CORE
                  LP / MILP / QP
                        |
                        v
                 GLOBAL VALIDATION
                        |
                   +----+----+
                   |         |
                 PASS       FAIL
                   |         |
                   v         v
                RESULT   EXPAND ADS
                   |         |
                   +----<----+
                        |
             +----------+----------+
             |                     |
             v                     v
         Matplotlib               R
       visual analytics     statistical analysis
             |                     |
             +----------+----------+
                        |
                        v
               DECISION SUPPORT
                        |
                        v
              HUMAN DECISION
                        |
                        v
                NEXT SCENARIO
```

The project should therefore be positioned as a **state-aware adaptive mathematical decision engine**, not simply a solver and not simply a supply-chain analytics dashboard.
