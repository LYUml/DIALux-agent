import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest
from shapely.affinity import rotate
from shapely.geometry import Point
from src.array_transform import plan_array_transform
from src.layout import plan_grid


def inputs():
    spec = {'units':'m','contour':[[0,0],[6,0],[6,4],[0,4]],'assumptions':['Synthetic rigid-array test'],
            'grid':{'origin_m':[1,1],'spacing_x_m':2,'spacing_y_m':2,'rotation_deg':0},
            'fixture':{'product_id':'SYNTHETIC','width_m':.5,'depth_m':.5,'mounting_height_m':3.035}}
    layout = plan_grid(spec)
    observed = {'operation':'read_group_fixtures','coordinate_frame':'active_storey',
                'path':'synthetic.evo','group_id':'group','offset':0,'next_offset':None,
                'inventory_token':'synthetic-token','container_node_count':6,'observed_count':6,
                'fixtures':[{'position_m':f['position_m'],'rotation_deg':[0,0,0],'runtime_id':[7,i]}
                            for i,f in enumerate(layout['fixtures'])]}
    arrangement = {'operation':'read_arrangement','coordinate_frame':'active_storey',
                   'path':'synthetic.evo','tree_item_id':'group','display_values':{
                       'ElementCountX':'3','ElementCountY':'2','PolygonPosition_X':'3',
                       'PolygonPosition_Y':'2','PolygonPosition_Z':'3.035','ArrangementRotation_Z':'0'}}
    return spec,observed,arrangement


def test_rigid_translation_predicts_full_geometry_without_mutating_inputs():
    spec,observed,arrangement = inputs()
    spec['grid']['origin_m'] = [1.1,1.2]
    spec['fixture']['mounting_height_m'] = 3.135
    prior = copy.deepcopy((spec,observed,arrangement))
    result = plan_array_transform(spec,observed,arrangement)
    assert result['requested_values'] == pytest.approx({'PolygonPosition_X':3.1,'PolygonPosition_Y':2.2,
                                                       'PolygonPosition_Z':3.135,'ArrangementRotation_Z':0})
    assert result['predicted_geometry']['matched_count'] == 6
    assert not result['native_mutation_verified'] and not result['source_authenticity_verified']
    assert (spec,observed,arrangement) == prior


def test_rotation_about_native_centre_matches_all_six_fixtures():
    spec,observed,arrangement = inputs()
    point = rotate(Point(1,1),5,origin=(3,2))
    spec['grid'].update(origin_m=[point.x,point.y],rotation_deg=5)
    result = plan_array_transform(spec,observed,arrangement)
    assert result['requested_values'] == pytest.approx({'PolygonPosition_X':3,'PolygonPosition_Y':2,
                                                       'PolygonPosition_Z':3.035,'ArrangementRotation_Z':5})
    assert result['rotation_delta_deg'] == 5
    assert result['predicted_geometry']['matched_count'] == 6


def test_nonzero_observed_array_angle_is_used_not_assumed_zero():
    spec,observed,arrangement = inputs()
    arrangement['display_values']['ArrangementRotation_Z'] = '5'
    for fixture in observed['fixtures']:
        point = rotate(Point(*fixture['position_m'][:2]),5,origin=(3,2))
        fixture['position_m'][:2] = [point.x,point.y]
        fixture['rotation_deg'][2] = 5
    result = plan_array_transform(spec,observed,arrangement)
    assert result['rotation_delta_deg'] == -5
    assert result['predicted_geometry']['matched_count'] == 6


@pytest.mark.parametrize('change',['centre','individual_position','individual_angle','spacing','count',
    'incomplete','continued','duplicate_runtime','project','group','missing_field','nonfinite','fractional_count'])
def test_unsupported_or_inconsistent_array_is_refused(change):
    spec,observed,arrangement = inputs()
    values = arrangement['display_values']
    if change == 'centre': values['PolygonPosition_X'] = '3.1'
    elif change == 'individual_position':
        # Preserve centroid: a centroid-only guard would miss this distortion.
        observed['fixtures'][0]['position_m'][0] += .1
        observed['fixtures'][1]['position_m'][0] -= .1
    elif change == 'individual_angle': observed['fixtures'][0]['rotation_deg'][2] = 1
    elif change == 'spacing': spec['grid']['spacing_x_m'] = 1.9
    elif change == 'count': values['ElementCountX'] = '4'
    elif change == 'incomplete': observed['container_node_count'] = 7
    elif change == 'continued': observed['next_offset'] = 6
    elif change == 'duplicate_runtime': observed['fixtures'][1]['runtime_id'] = observed['fixtures'][0]['runtime_id']
    elif change == 'project': arrangement['path'] = 'other.evo'
    elif change == 'group': arrangement['tree_item_id'] = 'other'
    elif change == 'missing_field': del values['PolygonPosition_Z']
    elif change == 'nonfinite': values['PolygonPosition_Z'] = 'nan'
    elif change == 'fractional_count': values['ElementCountX'] = '2.5'
    with pytest.raises(ValueError): plan_array_transform(spec,observed,arrangement)


@pytest.mark.parametrize('change',['observation_type','arrangement_type','fixture_type','token_type','offset_bool'])
def test_invalid_evidence_shapes_are_refused(change):
    spec,observed,arrangement = inputs()
    if change == 'observation_type': observed = []
    elif change == 'arrangement_type': arrangement = None
    elif change == 'fixture_type': observed['fixtures'][0] = None
    elif change == 'token_type': observed['inventory_token'] = True
    elif change == 'offset_bool': observed['offset'] = False
    with pytest.raises(ValueError): plan_array_transform(spec,observed,arrangement)


def test_public_cli_from_another_working_directory(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([sys.executable,str(root/'src/dialux_agent.py'),
        'layout-array-transform-plan','--request',str(root/'resources/examples/synthetic-array-transform.json')],
        cwd=tmp_path,capture_output=True,text=True,encoding='utf-8',timeout=20)
    assert result.returncode == 0, result.stderr+result.stdout
    payload = json.loads(result.stdout)
    assert payload['predicted_geometry']['matched_count'] == 6
    assert payload['requested_values']['PolygonPosition_X'] == pytest.approx(3.1)
    assert not payload['native_mutation_verified']
