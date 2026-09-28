import pytest
from src.supply_chain import SupplyChainGraph
from src.data_models import NodeType, EdgeType, ConstraintSense

def test_supply_chain_builder():
    graph = SupplyChainGraph(time_periods=1)
    
    # Supplier -> Plant -> Warehouse -> Customer
    graph.add_node("S1", NodeType.SUPPLIER, capacity=1000)
    graph.add_node("P1", NodeType.PLANT, capacity=500)
    graph.add_node("W1", NodeType.WAREHOUSE, capacity=200)
    graph.add_node("C1", NodeType.CUSTOMER, demand=150)
    
    graph.add_edge("S1", "P1", EdgeType.SUPPLY, cost=10.0, capacity=1000)
    graph.add_edge("P1", "W1", EdgeType.TRANSPORT, cost=5.0, capacity=500)
    graph.add_edge("W1", "C1", EdgeType.SHIPMENT, cost=15.0, capacity=200)
    
    model = graph.to_optimization_model()
    
    # Validate variables
    assert "flow_S1_P1_t0" in model.variables
    assert "flow_P1_W1_t0" in model.variables
    assert "flow_W1_C1_t0" in model.variables
    assert "inv_W1_t0" in model.variables
    assert "shortage_C1_t0" in model.variables
    
    # Validate objective coefficients
    assert model.variables["flow_S1_P1_t0"].obj_coef == 10.0
    assert model.variables["shortage_C1_t0"].obj_coef == 1000.0
    
    # Validate constraints
    assert "balance_P1_t0" in model.constraints
    assert "demand_meet_C1_t0" in model.constraints
    assert model.constraints["demand_meet_C1_t0"].rhs == 150.0
    assert model.constraints["demand_meet_C1_t0"].sense == ConstraintSense.EQ
