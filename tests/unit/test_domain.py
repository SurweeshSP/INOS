import pytest
from src.domain.schema import GenericSupplyChainModel, Supply, Demand, Route
from src.domain.validator import DomainValidator
from src.domain.compiler import MathematicalCompiler
from src.data_models import OptimizationModel, ProblemType

def test_domain_validator():
    model = GenericSupplyChainModel(
        domain="cotton",
        nodes={"suppliers": ["FARM_A"], "customers": ["CUST_A"]},
        products=["raw_cotton"],
        supply=[Supply("FARM_A", "raw_cotton", 100.0)],
        demand=[Demand("CUST_A", "raw_cotton", 50.0)],
        routes=[Route("FARM_A", "CUST_A", 100.0, 5.0)]
    )
    
    val = DomainValidator()
    assert val.validate(model) == True
    
def test_domain_compiler():
    model = GenericSupplyChainModel(
        domain="cotton",
        nodes={"suppliers": ["FARM_A"], "customers": ["CUST_A"]},
        products=["raw_cotton"],
        supply=[Supply("FARM_A", "raw_cotton", 100.0)],
        demand=[Demand("CUST_A", "raw_cotton", 50.0)],
        routes=[Route("FARM_A", "CUST_A", 100.0, 5.0)]
    )
    
    comp = MathematicalCompiler()
    opt = comp.compile(model)
    
    assert opt.problem_type == ProblemType.LP
    assert "flow_FARM_A_CUST_A" in opt.variables
    assert "supply_FARM_A_raw_cotton" in opt.variables
