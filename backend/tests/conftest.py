"""Optional synthetic agent evaluation artifact, never application conversation logging."""
import json
import os
from pathlib import Path
import pytest

_results=[]

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    outcome=yield
    report=outcome.get_result()
    if report.when!='call' or not os.getenv('PHASE5_RESULTS_DIR'):return
    result=dict(item.user_properties).get('phase5_result')
    if result is None:return
    _results.append({'case':item.nodeid,'outcome':report.outcome,'reason':'All expected facts, citations, forbidden claims and status assertions passed.' if report.passed else str(report.longrepr)[-2000:],'actual_result':result})


def pytest_sessionfinish(session,exitstatus):
    if not os.getenv('PHASE5_RESULTS_DIR'):return
    path=Path(os.environ['PHASE5_RESULTS_DIR']);path.mkdir(parents=True,exist_ok=True)
    (path/'phase5-evaluation-results.json').write_text(json.dumps({'pytest_exit_status':int(exitstatus),'cases':_results},indent=2)+'\n')
