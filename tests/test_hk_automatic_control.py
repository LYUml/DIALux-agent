import json
from pathlib import Path

import pytest
from src.regulations import evaluate_profile

PROFILE = json.loads((Path(__file__).resolve().parents[1]/'resources/profiles/hk-bec2024-office-automatic-control.json').read_text())


def inputs():
    facts = {'design_code':'BEC 2024','bec_section5_scope_confirmed':True,'space_use':'office',
             'automatic_control_required_reviewed':True,'occupied_24_hours_7_days':False,
             'control_zone_mapping_reviewed':True,'control_zone_nonempty_reviewed':True,
             'occupant_sensors_deployed':True,'manual_override_installed':True}
    context = {key:{'value':value,'evidence':'Synthetic control-zone scope evidence'} for key,value in facts.items()}
    context['complete_fixed_lighting_power'] = {'value':151,'unit':'W','evidence':'Synthetic complete fixed-load schedule'}
    measurements = [{'metric':metric,'unit':unit,'value':value,'calculation_surface':'selected_control_zone',
                     'evidence':'Synthetic control configuration, not a DIALux result'} for metric,unit,value in [
        ('automatic_control_remaining_power_percent','%',50),('automatic_controlled_area','m2',250),
        ('occupancy_reduction_delay','min',15),('manual_override_duration','min',120),
        ('manual_override_controlled_area','m2',250)]]
    return measurements,context


def test_exact_control_boundaries_pass_only_the_supplied_scope():
    measurements,context = inputs()
    result = evaluate_profile(PROFILE,measurements,context)
    assert result['status'] == 'pass' and len(result['criteria']) == 5
    assert all(r['source']['sha256'] == '9fae5eb2134caa7f5645735d618d82da0cf3f284e576a9f6402de9b8357f95b7'
               for r in result['criteria'])


@pytest.mark.parametrize('index',range(5))
def test_exceeding_each_control_limit_fails(index):
    measurements,context = inputs()
    measurements[index]['value'] += .001
    result = evaluate_profile(PROFILE,measurements,context)
    assert result['status'] == 'fail' and result['criteria'][index]['status'] == 'fail'


@pytest.mark.parametrize('power',[0,70,150])
def test_automatic_control_uses_150w_boundary_not_lpd_exception(power):
    measurements,context = inputs()
    context['complete_fixed_lighting_power']['value'] = power
    result = evaluate_profile(PROFILE,measurements,context)
    assert result['status'] == 'unverified'
    assert all(r['status'] == 'not_applicable' for r in result['criteria'])


@pytest.mark.parametrize('key',['design_code','bec_section5_scope_confirmed','space_use',
    'automatic_control_required_reviewed','occupied_24_hours_7_days','control_zone_mapping_reviewed',
    'control_zone_nonempty_reviewed','complete_fixed_lighting_power','occupant_sensors_deployed','manual_override_installed'])
def test_missing_scope_never_passes(key):
    measurements,context = inputs()
    del context[key]
    assert evaluate_profile(PROFILE,measurements,context)['status'] == 'unverified'


def test_absent_optional_devices_skip_only_their_clauses():
    measurements,context = inputs()
    for key in ['occupant_sensors_deployed','manual_override_installed']:
        context[key]['value'] = False
    result = evaluate_profile(PROFILE,measurements[:2],context)
    assert result['status'] == 'pass'
    assert [r['status'] for r in result['criteria']] == ['pass','pass']+['not_applicable']*3


@pytest.mark.parametrize('key,value',[('occupied_24_hours_7_days',True),('space_use','carpark'),('design_code','BEC 2021')])
def test_different_occupancy_use_or_edition_is_not_adopted(key,value):
    measurements,context = inputs()
    context[key]['value'] = value
    assert evaluate_profile(PROFILE,measurements,context)['status'] == 'unverified'


@pytest.mark.parametrize('change',['missing','wrong_unit','wrong_zone','negative','illuminance_only'])
def test_control_evidence_cannot_be_replaced_by_illumination(change):
    measurements,context = inputs()
    if change == 'missing': measurements[0]['evidence'] = ''
    elif change == 'wrong_unit': measurements[0]['unit'] = 'W'
    elif change == 'wrong_zone': measurements[0]['calculation_surface'] = 'WP1'
    elif change == 'negative': measurements[0]['value'] = -1
    else: measurements = [{'metric':'average_perpendicular_illuminance','unit':'lx','value':500,
                           'calculation_surface':'WP1','evidence':'Synthetic result'}]
    assert evaluate_profile(PROFILE,measurements,context)['status'] == 'unverified'
