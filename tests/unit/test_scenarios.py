import pytest
from src.scenarios.engine import ScenarioEngine
from src.graph import SupplyChainGraph
from src.data_models import OptimizationModel, ProblemType, NodeMeta, NodeType, EdgeMeta, EdgeType

def test_scenario_engine_s1():
    engine = ScenarioEngine(seed=42)
    model = OptimizationModel(problem_type=ProblemType.LP)
    graph = SupplyChainGraph()
    
    n1 = NodeMeta("N1", NodeType.PLANT)
    n2 = NodeMeta("N2", NodeType.WAREHOUSE)
    graph.add_node(n1)
    graph.add_node(n2)
    
    events = engine.generate_scenario("S1", model, graph)
    assert len(events) == 1
    assert events[0].event_type.name == "DEMAND_CHANGE"
    
def test_scenario_engine_s2():
    engine = ScenarioEngine(seed=42)
    model = OptimizationModel(problem_type=ProblemType.LP)
    graph = SupplyChainGraph()
    
    n1 = NodeMeta("N1", NodeType.PLANT)
    n2 = NodeMeta("N2", NodeType.WAREHOUSE)
    graph.add_node(n1)
    graph.add_node(n2)
    e1 = EdgeMeta("N1", "N2", EdgeType.TRANSPORT)
    graph.add_edge(e1)
    
    events = engine.generate_scenario("S2", model, graph)
    # One demand shock, one supply disruption since there is an upstream node
    assert len(events) >= 1
    
def test_scenario_engine_reproducibility():
    engine1 = ScenarioEngine(seed=100)
    engine2 = ScenarioEngine(seed=100)
    
    model = OptimizationModel(problem_type=ProblemType.LP)
    graph = SupplyChainGraph()
    
    n1 = NodeMeta("N1", NodeType.PLANT)
    n2 = NodeMeta("N2", NodeType.WAREHOUSE)
    n3 = NodeMeta("N3", NodeType.WAREHOUSE)
    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    
    e1 = engine1.generate_scenario("S1", model, graph)[0]
    e2 = engine2.generate_scenario("S1", model, graph)[0]
    
    assert e1.affected_nodes == e2.affected_nodes
    assert e1.delta_parameters == e2.delta_parameters
