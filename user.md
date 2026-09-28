# User Guide — Indigenous Adaptive Optimization Decision System

## 1. What this system is

This system is a mathematical optimization decision engine for supply-chain, production, logistics, refinery, power and related industrial planning.

A normal user does not need to understand LP/MILP/QP mathematics.

The user provides:

- what they want to optimize;
- operational data;
- business constraints;
- current conditions;
- future scenarios or disruptions.

The system converts those inputs into a mathematical optimization problem, analyzes the situation, chooses an appropriate optimization strategy, solves it, validates it, and explains the result.

---

# 2. The user journey

```text
USER
  |
  | 1. Define goal
  v
INPUT
  |
  | 2. Provide data/constraints
  v
MODEL
  |
  | 3. Analyze current situation
  v
STATISTICS
  |
  | 4. Optimize
  v
SOLVER
  |
  | 5. Explain result
  v
VISUALIZATION
  |
  | 6. User approves or changes assumption
  v
SCENARIO
  |
  | 7. Detect change
  v
ACTIVE GRAPH
  |
  | 8. Reoptimize affected region
  v
DELTA SOLVER
  |
  | 9. Validate globally
  v
DECISION
  |
  `----> New event / next planning cycle
```

---

# 3. What the user or stakeholder provides

## 3.1 Objective

The first input is the business objective.

Examples:

```text
Minimize total supply-chain cost.
```

```text
Maximize profit while maintaining at least 95% service.
```

```text
Minimize shortage while keeping cost below the approved budget.
```

```text
Minimize transportation cost and emissions.
```

The system must make multi-objective priorities explicit.

Example:

```text
Cost       60%
Service    30%
Emissions  10%
```

---

# 4. Operational inputs

Depending on the application, the user can provide:

## Demand

```text
product
customer
location
period
quantity
priority
```

Example:

```text
Product A
Customer C1
Week 12
Demand = 10,000
```

## Supply

```text
supplier
product
availability
capacity
cost
lead time
```

## Production

```text
plant
product
capacity
production cost
resource requirement
availability
```

## Inventory

```text
location
product
opening inventory
safety stock
maximum inventory
holding cost
```

## Transportation

```text
origin
destination
route
capacity
cost
lead time
availability
```

## Facilities

```text
facility
capacity
fixed cost
availability
operating status
```

## Service

```text
customer
product
service target
priority
```

## Planning horizon

```text
daily
weekly
monthly
```

---

# 5. Business constraints

Users can specify:

```text
minimum service level
maximum budget
minimum inventory
maximum inventory
facility capacity
production capacity
transport capacity
route availability
supplier limit
production limit
storage limit
policy constraints
```

The application translates these into mathematical constraints.

---

# 6. Three ways to provide input

## A. Form/API input

For application users.

Example:

```json
{
  "objective": "minimize_cost",
  "horizon": 12,
  "service_target": 0.95,
  "demand": "...",
  "capacity": "...",
  "routes": "..."
}
```

## B. Dataset input

For planners/engineers:

```text
CSV
Parquet
JSON
Excel
MPS
LP
QPLIB
```

## C. Scenario input

For what-if analysis:

```text
Increase Product A demand by 15%.
```

```text
Plant P2 is unavailable during weeks 8-9.
```

```text
Block route R17.
```

```text
Reduce warehouse capacity by 20%.
```

```text
Increase transportation cost by 10%.
```

---

# 7. What happens after input

The system executes:

```text
1. Input validation
2. Data normalization
3. Model construction
4. Statistical analysis
5. Base optimization
6. Persistent state creation
7. Visualization
```

The user receives:

```text
recommended plan
objective value
cost/profit
service level
inventory
capacity utilization
shortages
bottlenecks
risk
```

---

# 8. Base-plan screen

The first result should answer:

### What should we do?

Example:

```text
Production
P1 → Product A = 8,000
P2 → Product A = 5,000

Shipments
P1 → W1 = 6,000
P2 → W1 = 3,000
W1 → C1 = 9,000

Service = 97.2%
Total cost = ₹X
```

The exact values come from the model; the UI must never invent values.

---

# 9. Visualization

Matplotlib generates scientific decision views.

Recommended views:

```text
Supply-chain network
Inventory over time
Demand vs supply
Capacity utilization
Route utilization
Service level
Shortage/backlog
Objective
Scenario comparison
```

For adaptive optimization:

```text
Full model size
Active model size
Active-region percentage
ADS expansion
Baseline solve time
Adaptive solve time
CPU vs GPU time
```

---

# 10. What happens when the user changes something?

Suppose the user has accepted a base plan.

They then say:

```text
"Demand for Product A increases by 15%."
```

The system does NOT immediately rebuild and solve the entire world blindly.

It performs:

```text
User change
    ↓
Event
    ↓
Affected demand constraints
    ↓
Impact propagation
    ↓
Active Decision Subgraph
    ↓
Delta model
    ↓
Persistent-state warm start
    ↓
Algorithm Harness
    ↓
CPU/GPU solver
    ↓
Global validation
```

---

# 11. What is the Active Decision Subgraph from the user's perspective?

The user does not need to select the graph manually.

The system determines the likely affected region.

For example:

```text
Demand increase at Customer C7
          |
          v
Distribution center W3
          |
          v
Transport routes
          |
          v
Plants P2/P4
          |
          v
Shared production capacity
```

The system may discover during validation that another shared resource is affected.

Then:

```text
initial ADS
   ↓
validation
   ↓
constraint conflict
   ↓
ADS expansion
   ↓
reoptimization
```

This makes the system adaptive rather than dependent on a fixed manually selected region.

---

# 12. CPU vs GPU from the user's perspective

The user should normally not have to select CPU or GPU.

The Algorithm Harness decides.

```text
Small problem
→ CPU

Small active region
→ CPU

Large sparse numerical workload
→ GPU candidate

Many scenarios
→ GPU candidate / parallel evaluation

Irregular branch-and-bound control
→ CPU candidate
```

The Harness can also learn from previous measured performance.

The UI should show:

```text
Execution:
GPU

Reason:
Large sparse active region
Historical GPU benefit: measured
```

or:

```text
Execution:
CPU

Reason:
Small active region; GPU transfer overhead would dominate
```

The system must not claim GPU acceleration unless it actually improves the measured workload.

---

# 13. R from the user's perspective

R is an analytical/research backend.

It can be used to answer:

```text
How variable is demand?
What is the probability of shortage?
Which factors correlate with service failure?
How sensitive is the system to capacity changes?
What scenario distributions should we test?
```

Example:

```text
Historical demand
        ↓
Python data layer
        ↓
R statistical analysis
        ↓
risk / distribution / inference
        ↓
scenario parameters
        ↓
optimization
```

The core optimization remains Python.

---

# 14. Scenario Analysis

Users should be able to create scenarios without changing the base model permanently.

Example:

```text
BASE
Demand = 100%

Scenario A
Demand = +10%

Scenario B
Demand = +20%

Scenario C
Plant P2 unavailable

Scenario D
Demand +20% + Plant P2 unavailable
```

The system solves and compares them.

Output:

```text
Scenario | Cost | Service | Risk | Solve time
------------------------------------------------
Base     | ...  | ...     | ...  | ...
A        | ...  | ...     | ...  | ...
B        | ...  | ...     | ...  | ...
C        | ...  | ...     | ...  | ...
D        | ...  | ...     | ...  | ...
```

---

# 15. Stakeholder decision cycle

The application is not finished after one optimization.

The real operating cycle is:

```text
PLAN
 ↓
OPTIMIZE
 ↓
VISUALIZE
 ↓
STAKEHOLDER REVIEW
 ↓
APPROVE / MODIFY
 ↓
EXECUTE
 ↓
OBSERVE NEW DATA
 ↓
DETECT CHANGE
 ↓
REOPTIMIZE
 ↓
REVIEW
 ↓
EXECUTE
```

The persistent state connects these cycles.

---

# 16. Human override

A stakeholder may say:

```text
"Do not use Plant P3."
```

or:

```text
"Maintain at least 98% service for Customer C1."
```

or:

```text
"Route R17 must remain unused."
```

This must become an explicit mathematical change:

```text
new bound
new constraint
new route state
new event
```

The system then reoptimizes.

The override must never silently alter a solution outside the mathematical model.

---

# 17. Decision explanation

Every recommendation should answer:

### What changed?

```text
Demand at C7 increased 15%.
```

### What was affected?

```text
W3
P2
P4
Routes R12/R14
```

### What did the optimizer change?

```text
Production P2: +...
Shipment R12: +...
Inventory W3: -...
```

### Why?

```text
W3 became capacity constrained.
P2 had available production capacity.
R14 had lower marginal transport cost.
```

### Was the solution globally feasible?

```text
YES
```

### How much work was avoided?

```text
Full model: ...
Active region: ...
Active fraction: ...
```

The explanation should be based on actual solver/graph statistics, not generated speculation.

---

# 18. Applications

## Supply-chain planning

User:

```text
Demand
inventory
capacity
routes
cost
service
```

System:

```text
procurement
production
inventory
shipment
service plan
```

## Production planning

User:

```text
orders
machines
capacity
labor
materials
```

System:

```text
production schedule
resource allocation
bottlenecks
```

## Logistics

User:

```text
orders
locations
routes
vehicles
capacities
```

System:

```text
shipment/flow plan
route utilization
service
```

## Disruption management

User:

```text
facility outage
route blockage
capacity loss
demand shock
```

System:

```text
impact region
alternate plan
recovery plan
cost/service impact
```

## Inventory planning

User:

```text
historical demand
lead time
holding cost
shortage cost
service target
```

System:

```text
inventory/order plan
risk
service
```

---

# 19. Research/Engineer Mode

Advanced users can bypass the business interface and provide:

```text
MPS
LP
QPLIB
optimization model
variable metadata
constraint metadata
graph mapping
```

They can inspect:

```text
matrix statistics
sparsity
condition proxies
dual values
reduced costs
MIP gap
branch nodes
cuts
ADS
persistent state
CPU/GPU selection
Harness decision
```

---

# 20. What the user should NOT have to do

Normal users should not have to:

- write simplex equations;
- choose branch-and-bound settings;
- manually identify affected nodes;
- manually rebuild models after disruptions;
- decide whether CPU/GPU is mathematically appropriate;
- manually calculate sensitivity;
- inspect sparse matrices;
- understand solver internals.

The system handles these.

Advanced users can override/configure them.

---

# 21. Minimum user workflow

For the first application:

```text
1. Select application:
   Supply Chain

2. Select objective:
   Minimize Cost

3. Enter/upload:
   Demand
   Capacity
   Inventory
   Routes
   Costs
   Service target
   Horizon

4. Click:
   Optimize

5. Review:
   Plan
   Cost
   Service
   Bottlenecks
   Visualization

6. Enter scenario:
   "Increase demand by 15%"

7. Run:
   Reoptimize

8. Review:
   What changed?
   What was affected?
   New cost?
   New service?
   Speedup?
   Active region?

9. Approve or create another scenario.
```

---

# 22. User-facing system promise

The application should communicate:

> Give the system your operational data, objectives and constraints. The optimization engine determines the mathematical plan, identifies the part of the decision network affected by changes, selects an appropriate CPU/GPU strategy, reuses previous optimization state when possible, validates the result globally, and presents the resulting trade-offs for human approval.

It should NOT promise:

> AI automatically makes all decisions.

The stakeholder remains responsible for business decisions; the solver provides mathematically validated decision support.

---

# 23. Audit Trail

Each decision cycle stores:

```text
user role
timestamp
input data version
model version
objective
constraints
event
ADS
Harness decision
CPU/GPU
solution
validation
scenario comparison
approval/override
```

This allows the organization to reproduce why a recommendation was generated.

---

# 24. First application milestone

Build this exact demonstration:

```text
Supply-chain network
      ↓
User inputs demand/capacity/cost/service
      ↓
Base optimization
      ↓
Matplotlib dashboard
      ↓
Persistent state
      ↓
User changes demand/capacity/route
      ↓
Event detection
      ↓
ADS
      ↓
CPU/GPU Harness
      ↓
Delta reoptimization
      ↓
Global validation
      ↓
Scenario comparison
      ↓
Stakeholder approval
```

Once this works, extend the same framework to:

```text
production
logistics
inventory
facility disruption
refinery planning
power dispatch
```

without redesigning the core architecture.
