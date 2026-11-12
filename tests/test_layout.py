import copy
import json
from pathlib import Path
import sys

import pytest
from shapely import affinity
from shapely.geometry import Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from layout import plan_grid


@pytest.fixture
def spec():
    return json.loads((Path(__file__).resolve().parents[1] / 'resources/examples/synthetic-grid-layout.json').read_text())


def test_every_full_footprint_fits_and_avoids_exclusion(spec):
    result = plan_grid(spec)
    allowed = Polygon(spec['contour']).buffer(-spec['clearance_m'])
    blocked = Polygon(spec['exclusions'][0]).buffer(spec['clearance_m'])
    assert result['fixture_count'] > 0
    assert result['fixture_count'] + sum(result['rejected'].values()) == result['candidate_count']
    assert result['rejected']['boundary'] and result['rejected']['exclusion']
    for f in result['fixtures']:
        shape = Polygon(f['footprint_m'])
        assert allowed.covers(shape)
        assert not blocked.intersects(shape)
        ix, iy = f['grid_index']
        assert f['position_m'][:2] == pytest.approx([.9 + 1.8 * ix, .9 + 1.8 * iy])
    assert not result['simulation_verified']


def test_translated_rotated_grid_preserves_selection(spec):
    original = plan_grid(spec)
    transformed = copy.deepcopy(spec)
    def transform(points):
        shape = affinity.translate(affinity.rotate(Polygon(points), 30, origin=(0,0)), 18, -12)
        return [list(p) for p in list(shape.exterior.coords)[:-1]]
    transformed['contour'] = transform(spec['contour'])
    transformed['exclusions'] = [transform(p) for p in spec['exclusions']]
    from shapely.geometry import Point
    origin = affinity.translate(affinity.rotate(Point(.9,.9),30,origin=(0,0)),18,-12)
    transformed['grid']['origin_m'] = [origin.x, origin.y]
    transformed['grid']['rotation_deg'] = 30
    rotated = plan_grid(transformed)
    assert [f['grid_index'] for f in rotated['fixtures']] == [f['grid_index'] for f in original['fixtures']]


@pytest.mark.parametrize('case', ['bowtie','outside_exclusion','overlap','nonfinite','unit'])
def test_invalid_geometry_is_rejected(spec, case):
    if case == 'bowtie': spec['contour'] = [[0,0],[4,4],[0,4],[4,0]]
    elif case == 'outside_exclusion': spec['exclusions'] = [[[20,20],[21,20],[21,21],[20,21]]]
    elif case == 'overlap': spec['grid']['spacing_x_m'] = .1
    elif case == 'nonfinite': spec['fixture']['width_m'] = float('nan')
    else: spec['units'] = 'mm'
    with pytest.raises(ValueError): plan_grid(spec)
