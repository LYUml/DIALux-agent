import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import workflow
from regulations import SOURCE_FIELDS


def test_scoped_assessment_never_receives_other_room_measurements(monkeypatch):
    first = {'summary_id':'one','measurements':[{'value':100}]}
    second = {'summary_id':'two','measurements':[{'value':500}]}
    report = {'source':'fixture.pdf','sha256':'fixture','summaries':[first,second]}
    monkeypatch.setattr(workflow, 'read_report_pdf', lambda *a: report)
    context = {'room_evidence':'only second room'}
    def assess(profile, measurements, facts):
        assert measurements is second['measurements']
        assert facts is context
        return {'status':'unverified'}
    monkeypatch.setattr(workflow, 'evaluate_profile', assess)
    result = workflow.check_report_summary('fixture.pdf', 'two', {}, context)
    assert result['summary'] is second
    assert not result['whole_project_assessed']
    with pytest.raises(ValueError, match='not found'):
        workflow.check_report_summary('fixture.pdf', 'missing', {}, context)


@pytest.mark.parametrize('threshold,status', [(5, 'fail'), (10, 'pass')])
def test_report_check_uses_profile_limits_and_retains_evidence(monkeypatch, threshold, status):
    measurement = {'metric': 'lighting_power_density', 'unit': 'W/m2',
                   'calculation_surface': 'space', 'value': 8,
                   'evidence': 'Synthetic report page 2 hash fixture'}
    report = {'measurements': [measurement], 'sha256': 'synthetic'}
    monkeypatch.setattr(workflow, 'read_summary_pdf', lambda path: report)
    profile = {'schema': 'dialux-agent/criteria-profile/v1', 'status': 'verified',
               'criteria': [{'id': 'synthetic-limit', 'metric': measurement['metric'],
                             'unit': 'W/m2', 'calculation_surface': 'space',
                             'operator': '<=', 'threshold': threshold,
                             'source': {k: 'Synthetic fixture' for k in SOURCE_FIELDS}}]}
    result = workflow.check_report('synthetic.pdf', profile)
    assert result['status'] == status
    assert result['report'] is report
    assert result['assessment']['criteria'][0]['evidence'] == measurement['evidence']


@pytest.mark.skipif(not (ROOT/'local/validation-summary-v2.pdf').exists(), reason='Local live artifact not distributed')
def test_real_report_cli_does_not_pass_without_hk_applicability():
    run = subprocess.run([sys.executable, '-m', 'src.dialux_agent', 'report-check',
                          '--path', 'local/validation-summary-v2.pdf',
                          '--profile', 'profiles/hk-bec2024-office-lpd.json'],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 3, run.stderr
    result = json.loads(run.stdout)
    assert result['status'] == 'unverified'
    assert result['report']['measurements'][1]['value'] == .22
    assert all(row['status'] == 'unverified' for row in result['assessment']['criteria'])
