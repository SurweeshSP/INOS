import pytest
from src.optimizer import SupplyChainOptimizer
from src.data_models import OptimizationModel, ProblemType, VariableMeta, VariableType

def test_optimizer_initial_solve(tmp_path):
    opt = SupplyChainOptimizer(log_dir=str(tmp_path))
    model = OptimizationModel(problem_type=ProblemType.LP)
    
    res = opt.solve(model, run_id="test_init")
    assert res.status == "OPTIMAL"
    assert res.optimization_mode == "FULL"
    assert res.experience_record_id == "test_init"
    
def test_optimizer_reoptimize(tmp_path):
    opt = SupplyChainOptimizer(log_dir=str(tmp_path))
    model = OptimizationModel(problem_type=ProblemType.LP)
    
    res = opt.reoptimize(model, events=[], strategy="ADAPTIVE", run_id="test_reopt")
    assert res.status == "OPTIMAL"
    assert res.optimization_mode == "ADAPTIVE"
    assert res.experience_record_id == "test_reopt"

def test_optimizer_what_if():
    model = OptimizationModel(problem_type=ProblemType.LP)
    model.variables['x'] = VariableMeta(name='x', var_type=VariableType.CONTINUOUS)
    opt = SupplyChainOptimizer(log_dir='results/test_telemetry')
    baseline = opt.solve(model)
    baseline.objective = 100.0
    scenario = opt.what_if(model, demand_multiplier=1.3)
    scenario['result'].objective = 150.0
    comparison = opt.compare_scenarios(baseline, scenario)
    assert 'demand_multiplier' in scenario['scenario']
    assert comparison['objective_delta'] == 50.0

