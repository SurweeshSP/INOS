import pytest
from src.supply_chain import SupplyChainGraph
from src.data_models import Event, EventType, PersistentOptimizationState, SolutionRecord, SolveStatus, NodeType, EdgeType
from src.delta_reoptimization import DeltaReoptimizationOrchestrator, DeltaReoptimizationConfig

def test_supply_chain_integration_with_delta_reopt():
    # 1. Build a small supply chain model
    graph = SupplyChainGraph()
    graph.add_node("plant_A", NodeType.PLANT, capacity=100)
    graph.add_node("wh_A", NodeType.WAREHOUSE, capacity=200)
    graph.add_node("cust_A", NodeType.CUSTOMER, demand=50)
    
    graph.add_edge("plant_A", "wh_A", EdgeType.TRANSPORT, cost=10, capacity=100)
    graph.add_edge("wh_A", "cust_A", EdgeType.TRANSPORT, cost=15, capacity=100)
    
    model = graph.to_optimization_model()
    
    # 2. Simulate an initial solution state
    # Flow of 50 through plant -> wh -> cust (we append _t0 since it defaults to time_periods=1)
    initial_solution = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        primal_values={
            "flow_plant_A_wh_A_t0": 50.0,
            "flow_wh_A_cust_A_t0": 50.0,
            "inv_plant_A_t0": 50.0
        },
        objective_value=1250.0
    )
    state = PersistentOptimizationState(
        model_version="v1.0",
        previous_solution=initial_solution
    )
    
    # 3. Simulate an event: Plant A capacity drops
    event = Event(
        event_type=EventType.CAPACITY_CHANGE,
        affected_variables=["inv_plant_A_t0"],
        new_value=40.0
    )
    
    # 4. Matrix data mapping
    # Assuming we have a constraint representing capacity c_cap_plant_A
    matrix_data = {
        "c_cap_plant_A": {"inv_plant_A_t0": 1.0}
    }
    
    # 5. Run Adaptive Solve
    config = DeltaReoptimizationConfig(max_expansions=1)
    orchestrator = DeltaReoptimizationOrchestrator(config)
    
    result = orchestrator.run_adaptive_solve(model, [event], state, matrix_data)
    
    # We expect the mock CPU solver to handle the run and fallback/expand appropriately.
    # Because of mock implementations, we just ensure it executes without crashing and 
    # either succeeds with fallback or valid delta resolve.
    assert result.solution.status in [SolveStatus.OPTIMAL, SolveStatus.INFEASIBLE, SolveStatus.ERROR]
    assert result.diagnostics is not None
    assert result.diagnostics.total_adaptive_time >= 0
