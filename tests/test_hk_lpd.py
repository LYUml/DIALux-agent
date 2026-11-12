import json
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from regulations import evaluate_profile


def evaluate(area, lpd, power=100, missing=None):
    profile=json.loads((ROOT/'resources/profiles/hk-bec2024-office-lpd.json').read_text())
    values={'design_code':'BEC 2024','bec_section5_scope_confirmed':True,
            'space_use':'office','single_function_space':True,'enclosed':True,
            'space_boundary_5_4_3_reviewed':True,'lpd_power_basis_5_4_2_reviewed':True}
    context={k:{'value':v,'evidence':'Synthetic boundary test; not a project assessment'} for k,v in values.items()}
    context['internal_area']={'value':area,'unit':'m2','evidence':'Synthetic test area'}
    context['complete_fixed_lighting_power']={'value':power,'unit':'W','evidence':'Synthetic test power'}
    if missing:del context[missing]
    measurement={'metric':'lighting_power_density','unit':'W/m2','calculation_surface':'space',
                 'value':lpd,'evidence':'Synthetic test value; no real building'}
    return evaluate_profile(profile,[measurement],context)


@pytest.mark.parametrize('area,limit',[(15,9),(15.01,8.5),(200,8.5),(200.01,7.2)])
def test_official_band_boundaries(area,limit):
    assert evaluate(area,limit)['status']=='pass'
    assert evaluate(area,limit+.01)['status']=='fail'
    assert len([r for r in evaluate(area,limit)['criteria'] if r['status']=='pass'])==1


@pytest.mark.parametrize('power',[0,70])
def test_low_power_exception_is_not_whole_project_pass(power):
    result=evaluate(24,8,power=power)
    assert result['status']=='unverified'
    assert all(r['status']=='not_applicable' for r in result['criteria'])


def test_above_exception_boundary():
    assert evaluate(24,8,power=70.01)['status']=='pass'


@pytest.mark.parametrize('missing',['design_code','bec_section5_scope_confirmed','internal_area','lpd_power_basis_5_4_2_reviewed'])
def test_missing_scope_cannot_pass(missing):
    assert evaluate(24,8,missing=missing)['status']=='unverified'


def test_negative_lpd_cannot_pass():
    assert evaluate(24,-1)['status']=='unverified'
