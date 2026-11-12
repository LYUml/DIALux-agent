"""Exercise actual process exit status so automation cannot mistake unknown for pass."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


@pytest.mark.parametrize('value,evidence,status,code', [
    (10, 'synthetic fixture', 'pass', 0),
    (11, 'synthetic fixture', 'fail', 1),
    (10, '', 'unverified', 3),
])
def test_cli_status(tmp_path, value, evidence, status, code):
    from regulations import SOURCE_FIELDS
    profile = {'schema': 'dialux-agent/criteria-profile/v1', 'status': 'verified',
               'jurisdiction': 'TEST', 'criteria': [{
                   'id': 'synthetic', 'metric': 'test', 'unit': 'test',
                   'calculation_surface': 'test', 'operator': '<=', 'threshold': 10,
                   'source': {k: 'synthetic test source' for k in SOURCE_FIELDS}}]}
    measurements = [{'metric': 'test', 'unit': 'test', 'calculation_surface': 'test',
                     'value': value, 'evidence': evidence}]
    p, m = tmp_path / 'profile.json', tmp_path / 'measurement.json'
    p.write_text(json.dumps(profile))
    m.write_text(json.dumps(measurements))
    result = subprocess.run([sys.executable, str(ROOT / 'src/dialux_agent.py'),
                             'criteria-check', '--profile', str(p), '--measurements', str(m)],
                            cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == code, result.stderr
    assert json.loads(result.stdout)['status'] == status


def test_malformed_measurement_is_json_error(tmp_path):
    p, m = tmp_path / 'profile.json', tmp_path / 'measurement.json'
    p.write_text((ROOT / 'resources/profiles/hk-office.template.json').read_text())
    m.write_text('{}')
    result = subprocess.run([sys.executable, str(ROOT / 'src/dialux_agent.py'),
                             'criteria-check', '--profile', str(p), '--measurements', str(m)],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert json.loads(result.stdout)['ok'] is False
