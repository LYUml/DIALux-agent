"""Check supplied fixture footprints against source-pinned CAD tile coverage."""
import hashlib
import json
import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

if __package__:
    from .cad_grid import drawing_read_tile_grid
    from .layout import number, polygon
else:
    from cad_grid import drawing_read_tile_grid
    from layout import number, polygon


def verify_layout_tile_coverage(layout: dict, grid_request: dict) -> dict:
    """Re-read CAD; do not extrapolate tile coverage into missing grid cells.

    This checks supplied planar footprints, not native fixture dimensions,
    physical ceiling conditions, product identity or lighting performance.
    """
    if not isinstance(layout, dict) or layout.get('schema') != 'dialux-agent/layout/v1':
        raise ValueError('Expected a supplied layout/v1')
    if layout.get('units') != 'm' or layout.get('coordinate_frame') != 'active_storey':
        raise ValueError('Expected explicit metre active_storey layout')
    fixtures = layout.get('fixtures')
    if not isinstance(fixtures, list) or not 1 <= len(fixtures) <= 2000:
        raise ValueError('Expected 1 to 2000 supplied fixtures')
    if type(layout.get('fixture_count')) is not int or layout['fixture_count'] != len(fixtures):
        raise ValueError('Fixture count differs from supplied records')
    ids = [f.get('id') for f in fixtures]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Unique fixture IDs required')
    source = drawing_read_tile_grid(**grid_request)
    grid = source['grid']
    sx, sy = grid['spacing_x_m'], grid['spacing_y_m']
    ox, oy = grid['origin_m']
    a = math.radians(grid['rotation_deg'])
    c, s = math.cos(a), math.sin(a)
    tiles = []
    for tile in source['tiles']:
        ix, iy = tile['cell']
        corners = []
        for dx, dy in [(-.5,-.5),(.5,-.5),(.5,.5),(-.5,.5)]:
            x, y = (ix+dx)*sx, (iy+dy)*sy
            corners.append((ox+x*c-y*s, oy+x*s+y*c))
        tiles.append(Polygon(corners))
    coverage = unary_union(tiles)
    tolerance = source['tolerance_m']
    allowed = coverage.buffer(tolerance)
    checks = []
    for fixture in fixtures:
        shape = polygon(fixture.get('footprint_m'), 'fixture footprint')
        position = fixture.get('position_m')
        if not isinstance(position, list) or len(position) != 3:
            raise ValueError('Fixture position requires XYZ')
        x, y, z = [number(v, 'fixture position') for v in position]
        if max(abs(shape.centroid.x-x), abs(shape.centroid.y-y)) > tolerance:
            raise ValueError('Footprint centroid differs from fixture position')
        if not math.isfinite(shape.area):
            raise ValueError('Nonfinite footprint area')
        checks.append({'fixture_id': fixture['id'], 'covered': bool(allowed.covers(shape)),
                       'uncovered_area_m2': shape.difference(coverage).area})
    return {'schema': 'dialux-agent/tile-coverage/v1',
            'source': source['source'], 'source_sha256': source['sha256'],
            'layer': source['layer'], 'tile_count': source['tile_count'],
            'layout_sha256': hashlib.sha256(json.dumps(layout, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            'grid_request': grid_request, 'tolerance_m': tolerance,
            'all_supplied_footprints_covered': all(r['covered'] for r in checks),
            'fixtures': checks, 'semantic_ceiling_verified': False,
            'native_fixture_dimensions_verified': False, 'simulation_verified': False,
            'warning': 'Checks supplied footprints against canonical rectangles reconstructed from the selected CAD layer; no missing cells are filled. Does not prove ceiling suitability, fixture dimensions, native placement or photometry.'}
