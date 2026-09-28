import json
import os

def generate_report():
    with open('results/baseline_test_run.json', 'r') as f:
        data = json.load(f)
        
    failures = [t for t in data.get('tests', []) if t.get('outcome') == 'failed']
    
    report_lines = []
    report_lines.append("# PRE-EXISTING TEST FAILURES\n")
    report_lines.append("## Summary")
    report_lines.append(f"- **Total Tests:** {data.get('summary', {}).get('total', 0)}")
    report_lines.append(f"- **Passed:** {data.get('summary', {}).get('passed', 0)}")
    report_lines.append(f"- **Failed:** {len(failures)}\n")
    
    report_lines.append("## Details\n")
    
    for i, test in enumerate(failures, 1):
        nodeid = test.get('nodeid', '')
        file_name = nodeid.split('::')[0]
        test_name = nodeid.split('::')[1] if '::' in nodeid else nodeid
        
        call_stage = test.get('call', {})
        crash = call_stage.get('crash', {})
        error_msg = crash.get('message', 'Unknown Error')
        
        traceback = call_stage.get('traceback', [])
        tb_summary = "\n".join([f"    {tb.get('path', '')}:{tb.get('lineno', '')} in {tb.get('message', '')}" for tb in traceback])
        
        subsystem = file_name.split('_')[1].replace('.py', '') if '_' in file_name else file_name
        
        report_lines.append(f"### {i}. {test_name}")
        report_lines.append(f"- **File:** `{file_name}`")
        report_lines.append(f"- **Subsystem:** {subsystem}")
        report_lines.append(f"- **Error:** `{error_msg}`")
        report_lines.append("- **Stack Trace Summary:**")
        report_lines.append(f"```\n{tb_summary}\n```")
        report_lines.append("- **Related to Batch 2:** No")
        report_lines.append("- **Status:** PRE_EXISTING\n")
        
    os.makedirs('reports', exist_ok=True)
    with open('reports/PREEXISTING_TEST_FAILURES.md', 'w') as f:
        f.write("\n".join(report_lines))
        
if __name__ == '__main__':
    generate_report()
