import copy
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from layout import plan_grid, verify_observed_layout


def fixture_pair():
    spec = json.loads((Path(__file__).resolve().parents[1] / 'examples/synthetic-translated-grid.json').read_text())
    plan = plan_grid(spec)
    observed = {'operation': 'read_group_fixtures', 'observed_count': 4, 'fixtures': [
        {'position_m': list(p), 'rotation_deg': [0, 0, 360]} for p in
        [(4.7, 3.1, 3.035), (1.7, 1.1, 3.035), (4.7, 1.1, 3.035), (1.7, 3.1, 3.035)]]}
    return plan, observed


def test_matching_ignores_order_but_preserves_geometry_and_scope():
    plan, observed = fixture_pair()
    result = verify_observed_layout(plan, observed)
    assert result['matched_count'] == 4
    assert not result['whole_project_verified']
    assert not result['photometry_identity_verified']
    assert len({m['observed_index'] for m in result['matches']}) == 4


@pytest.mark.parametrize('mutation', ['position', 'tilt', 'duplicate', 'nan', 'count', 'id'])
def test_rejects_invalid_or_wrong_native_geometry(mutation):
    plan, observed = fixture_pair()
    if mutation == 'position': observed['fixtures'][0]['position_m'][0] += .01
    if mutation == 'tilt': observed['fixtures'][0]['rotation_deg'][0] = 5
    if mutation == 'duplicate': observed['fixtures'][0] = copy.deepcopy(observed['fixtures'][1])
    if mutation == 'nan': observed['fixtures'][0]['position_m'][0] = float('nan')
    if mutation == 'count': observed['observed_count'] = 3
    if mutation == 'id': plan['fixtures'][0]['id'] = plan['fixtures'][1]['id']
    with pytest.raises(ValueError): verify_observed_layout(plan, observed)
