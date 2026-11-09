import hashlib

import ezdxf
import pytest

from src.tile_coverage import verify_layout_tile_coverage


def inputs(tmp_path, x=.5, width=.8):
    doc = ezdxf.new(); doc.units = 6
    for ix in [0, 2]:
        doc.modelspace().add_lwpolyline([(ix,0),(ix+1,0),(ix+1,1),(ix,1)], close=True,
                                       dxfattribs={'layer':'Tiles'})
    path = tmp_path/'source.dxf'; doc.saveas(path)
    request = dict(path=str(path), expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   layer='Tiles', storey_origin_m=[0,0], storey_rotation_deg=0)
    footprint = [[x-width/2,.1],[x+width/2,.1],[x+width/2,.9],[x-width/2,.9]]
    layout = dict(schema='dialux-agent/layout/v1', units='m', coordinate_frame='active_storey',
                  fixture_count=1, fixtures=[dict(id='L1',position_m=[x,.5,3],footprint_m=footprint)])
    return layout, request


def test_source_cell_coverage(tmp_path):
    layout, request = inputs(tmp_path)
    result = verify_layout_tile_coverage(layout, request)
    assert result['all_supplied_footprints_covered']
    assert result['fixtures'][0]['uncovered_area_m2'] == 0
    assert not result['native_fixture_dimensions_verified']


@pytest.mark.parametrize('x,width', [(1.5,.8),(.5,1.2),(1.5,2.8)])
def test_missing_cells_and_partial_overhang_are_not_filled(tmp_path,x,width):
    layout, request = inputs(tmp_path,x,width)
    result = verify_layout_tile_coverage(layout, request)
    assert not result['all_supplied_footprints_covered']
    assert result['fixtures'][0]['uncovered_area_m2'] > 0


@pytest.mark.parametrize('kind', ['hash','centroid','count','duplicate','units'])
def test_rejects_invalid_evidence(tmp_path,kind):
    layout, request = inputs(tmp_path)
    if kind == 'hash': request['expected_sha256'] = '0'*64
    if kind == 'centroid': layout['fixtures'][0]['position_m'][0] += .1
    if kind == 'count': layout['fixture_count'] = True
    if kind == 'duplicate':
        layout['fixtures'] *= 2; layout['fixture_count'] = 2
    if kind == 'units': layout['units'] = 'mm'
    with pytest.raises(ValueError): verify_layout_tile_coverage(layout,request)
