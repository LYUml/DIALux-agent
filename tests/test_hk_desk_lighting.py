import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from regulations import evaluate_profile


def fixtures():
    profile = json.loads((ROOT/'profiles/hk-labour-desk-lighting.json').read_text())
    facts = {'labour_desk_guidance_adopted': True, 'visual_task': 'normal_desk_work',
             'task_surface_mapping_reviewed': True, 'operating_conditions_coverage_reviewed': True}
    context = {k: {'value': v, 'evidence': 'Synthetic test; not an actual project'} for k, v in facts.items()}
    measurement = {'metric': 'minimum_illuminance', 'value': 200, 'unit': 'lx',
                   'calculation_surface': 'normal_desk_work', 'evidence': 'Synthetic minimum'}
    return profile, context, measurement


@pytest.mark.parametrize('value,status', [(199.99, 'fail'), (200, 'pass'), (300, 'pass'), (-1, 'unverified')])
def test_advisory_minimum(value, status):
    profile, context, measurement = fixtures()
    measurement['value'] = value
    result = evaluate_profile(profile, [measurement], context)
    assert result['status'] == status
    assert result['criteria'][0]['source']['authority_type'] == 'advisory_guidance_not_statutory_threshold'


def test_average_or_unmapped_workplane_cannot_substitute_for_task_minimum():
    profile, context, measurement = fixtures()
    measurement['metric'] = 'average_perpendicular_illuminance'
    assert evaluate_profile(profile, [measurement], context)['status'] == 'unverified'
    measurement['metric'] = 'minimum_illuminance'
    measurement['calculation_surface'] = 'WP1'
    assert evaluate_profile(profile, [measurement], context)['status'] == 'unverified'


@pytest.mark.parametrize('fact', ['labour_desk_guidance_adopted', 'visual_task',
                                 'task_surface_mapping_reviewed', 'operating_conditions_coverage_reviewed'])
def test_missing_adoption_or_scope(fact):
    profile, context, measurement = fixtures()
    del context[fact]
    assert evaluate_profile(profile, [measurement], context)['status'] == 'unverified'
