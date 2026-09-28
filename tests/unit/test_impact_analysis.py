import pytest
from src.impact_analysis import ImpactAnalyzer
from src.data_models import SolutionRecord, SolveStatus

def test_impact_analysis():
    base = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        objective_value=100.0,
        primal_values={'x': 10.0, 'y': 5.0}
    )
    scen = SolutionRecord(
        status=SolveStatus.OPTIMAL,
        objective_value=120.0,
        primal_values={'x': 8.0, 'y': 5.0, 'z': 2.0}
    )
    
    analyzer = ImpactAnalyzer()
    res = analyzer.analyze(base, scen)
    
    assert res['objective_change'] == 20.0
    assert res['variable_differences']['x'] == -2.0
    assert 'y' not in res['variable_differences']
    assert res['variable_differences']['z'] == 2.0
