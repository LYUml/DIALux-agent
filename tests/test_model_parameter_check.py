import pytest
from src.model_parameter_check import check_model_parameters


VALUES = dict(ceiling_reflectance_pct=70,wall_reflectance_pct=50,floor_reflectance_pct=20,
              maintenance_factor=.8,mounting_height_m=3.035,wall_zone_m=0,
              area_m2=24,height_m=3,workplane_m=.8)


@pytest.fixture
def evidence(monkeypatch):
    report = dict(parameters=dict(VALUES),report_sha256='a'*64,report='synthetic.pdf',
                  page=15,room_scene_header='Synthetic room')
    monkeypatch.setattr('src.model_parameter_check.read_model_parameters',lambda *args:report)
    return report, {key:dict(value=value,absolute_tolerance=0) for key,value in VALUES.items()}


def run(expectations,digest='a'*64):
    return check_model_parameters('synthetic.pdf','explicit-room',digest,expectations)


def test_complete_match_is_scoped_and_not_native_proof(evidence):
    _, expected = evidence
    result = run(expected)
    assert result['all_reported_parameters_match'] and len(result['checks']) == 9
    assert not result['live_model_verified'] and not result['fresh_calculation_verified']


@pytest.mark.parametrize('field', list(VALUES))
def test_each_reported_parameter_mismatch_is_visible(evidence,field):
    report, expected = evidence
    report['parameters'][field] += .25
    result = run(expected)
    assert not result['all_reported_parameters_match']
    assert [c['parameter'] for c in result['checks'] if not c['matches']] == [field]


def test_explicit_tolerance_boundary(evidence):
    report, expected = evidence
    report['parameters']['height_m'] += .25
    expected['height_m']['absolute_tolerance'] = .25
    assert run(expected)['all_reported_parameters_match']
    expected['height_m']['absolute_tolerance'] = .249
    assert not run(expected)['all_reported_parameters_match']


@pytest.mark.parametrize('kind',['missing','extra','boolean','negative_tolerance','infinite','hash','reflectance','maintenance'])
def test_rejects_unbound_or_invalid_expectations(evidence,kind):
    _, expected = evidence
    if kind == 'missing': del expected['wall_zone_m']
    if kind == 'extra': expected['made_up'] = dict(value=1,absolute_tolerance=0)
    if kind == 'boolean': expected['area_m2']['value'] = True
    if kind == 'negative_tolerance': expected['area_m2']['absolute_tolerance'] = -1
    if kind == 'infinite': expected['height_m']['value'] = float('inf')
    if kind == 'reflectance': expected['ceiling_reflectance_pct']['value'] = 101
    if kind == 'maintenance': expected['maintenance_factor']['value'] = 0
    with pytest.raises(ValueError): run(expected, 'b'*64 if kind=='hash' else 'a'*64)
