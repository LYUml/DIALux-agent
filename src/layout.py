"""Explicit ceiling-grid planning with Shapely footprint checks, not photometric simulation."""
import hashlib
import json
import math

from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def polygon(points, name):
    if not isinstance(points, list) or len(points) < 3 or any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in points):
        raise ValueError(f'{name} requires at least three XY coordinates')
    shape = Polygon([(number(p[0], name), number(p[1], name)) for p in points])
    if not shape.is_valid or shape.area <= 0:
        raise ValueError(f'{name} must be a valid positive-area polygon')
    return shape


def verify_observed_layout(layout: dict, observed: dict) -> dict:
    """Match supplied native UI readings to a planned fixture set, not a whole project.

    Position tolerance is 1 mm for native display rounding; rotation is 0.05 deg.
    Ambiguous nearby fixtures are rejected instead of assigned by list order.
    """
    if layout.get('schema') != 'dialux-agent/layout/v1' or layout.get('units') != 'm':
        raise ValueError('Expected metre-unit planned layout')
    if observed.get('operation') != 'read_group_fixtures':
        raise ValueError('Expected native group fixture observations')
    planned, actual = layout.get('fixtures'), observed.get('fixtures')
    if not isinstance(planned, list) or not isinstance(actual, list) or not planned or len(planned) != len(actual):
        raise ValueError('Nonempty planned and observed fixture counts must match')
    if len(planned) > 2000:
        raise ValueError('Comparison is limited to 2000 fixtures')
    if layout.get('fixture_count') != len(planned) or observed.get('observed_count') != len(actual):
        raise ValueError('Declared fixture counts do not match records')
    ids = [f.get('id') for f in planned]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError('Planned fixture IDs must be unique')
    def vector(value, label):
        if not isinstance(value, list) or len(value) != 3:
            raise ValueError(f'{label} requires XYZ')
        return [number(x, label) for x in value]
    positions = [vector(f.get('position_m'), 'observed position') for f in actual]
    rotations = [vector(f.get('rotation_deg'), 'observed rotation') for f in actual]
    used, matches = set(), []
    for fixture in planned:
        position = vector(fixture.get('position_m'), 'planned position')
        angle = number(fixture.get('rotation_deg'), 'planned rotation')
        candidates = [i for i, point in enumerate(positions) if max(abs(a-b) for a,b in zip(position, point)) <= .001]
        if len(candidates) != 1 or candidates[0] in used:
            raise ValueError(f'Unmatched or ambiguous fixture: {fixture["id"]}')
        index = candidates[0]
        if any(abs((a-b+180) % 360-180) > .05 for a,b in zip(rotations[index], [0,0,angle])):
            raise ValueError(f'Rotation differs for fixture: {fixture["id"]}')
        used.add(index)
        matches.append({'fixture_id': fixture['id'], 'observed_index': index,
                        'position_error_m': [b-a for a,b in zip(position, positions[index])]})
    return {'schema': 'dialux-agent/layout-readback/v1', 'matched_count': len(matches), 'matches': matches,
            'supplied_fixture_geometry_matches': True, 'whole_project_verified': False,
            'photometry_identity_verified': False, 'simulation_verified': False,
            'position_tolerance_m': .001, 'rotation_tolerance_deg': .05,
            'layout_sha256': hashlib.sha256(json.dumps(layout, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            'observations_sha256': hashlib.sha256(json.dumps(observed, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            'warning': 'Matches supplied rounded observations only; does not authenticate their origin or prove no hidden fixtures exist.'}


def plan_grid(spec: dict) -> dict:
    """Plan exact grid-aligned fixture footprints inside an explicit room and outside exclusions.

    Coordinates are metres; grid origin is the center of lattice cell (0,0).
    No minimum illuminance, optical obstruction or code compliance is inferred.
    """
    if not isinstance(spec, dict) or spec.get('units') != 'm':
        raise ValueError('Layout requires an object with explicit metre units')
    assumptions = spec.get('assumptions')
    if not isinstance(assumptions, list) or not assumptions or any(not isinstance(a, str) or not a.strip() for a in assumptions):
        raise ValueError('Document sources or assumptions')
    room = polygon(spec['contour'], 'contour')
    exclusions = [polygon(p, 'exclusion') for p in spec.get('exclusions', [])]
    for shape in exclusions:
        if not room.covers(shape):
            raise ValueError('Every exclusion must lie inside the room')
    grid, fixture = spec['grid'], spec['fixture']
    origin = grid['origin_m']
    if not isinstance(origin, list) or len(origin) != 2:
        raise ValueError('grid.origin_m requires two coordinates')
    ox, oy = (number(v, 'origin') for v in origin)
    sx, sy = number(grid['spacing_x_m'], 'spacing_x_m'), number(grid['spacing_y_m'], 'spacing_y_m')
    angle = number(grid.get('rotation_deg', 0), 'rotation_deg') % 360
    width, depth = number(fixture['width_m'], 'width_m'), number(fixture['depth_m'], 'depth_m')
    z = number(fixture['mounting_height_m'], 'mounting_height_m')
    clearance = number(spec.get('clearance_m', 0), 'clearance_m')
    product = fixture.get('product_id')
    if not isinstance(product, str) or not product.strip():
        raise ValueError('fixture.product_id is required')
    if min(sx, sy, width, depth, z) <= 0 or clearance < 0 or sx < width or sy < depth:
        raise ValueError('Positive dimensions and nonoverlapping grid spacing required')
    # Transform the boundary once; do not round centers before testing footprints.
    local = affinity.rotate(affinity.translate(room, -ox, -oy), -angle, origin=(0, 0))
    xmin, ymin, xmax, ymax = local.bounds
    ix0, ix1 = math.ceil(xmin / sx), math.floor(xmax / sx)
    iy0, iy1 = math.ceil(ymin / sy), math.floor(ymax / sy)
    count = max(0, ix1 - ix0 + 1) * max(0, iy1 - iy0 + 1)
    if count > 100000:
        raise ValueError('Grid exceeds 100000 candidates; inspect units and spacing')
    allowed = room.buffer(-clearance) if clearance else room
    blocked = unary_union(exclusions).buffer(clearance) if exclusions else None
    fixtures, rejected = [], {'boundary': 0, 'exclusion': 0}
    for iy in range(iy0, iy1 + 1):
        for ix in range(ix0, ix1 + 1):
            x, y = ix * sx, iy * sy
            footprint = box(x - width / 2, y - depth / 2, x + width / 2, y + depth / 2)
            footprint = affinity.translate(affinity.rotate(footprint, angle, origin=(0, 0)), ox, oy)
            if not allowed.covers(footprint):
                rejected['boundary'] += 1
                continue
            if blocked is not None and blocked.intersects(footprint):
                rejected['exclusion'] += 1
                continue
            center = footprint.centroid
            fixtures.append({'id': f'L{len(fixtures)+1:04d}', 'product_id': product,
                             'grid_index': [ix, iy], 'position_m': [center.x, center.y, z],
                             'rotation_deg': angle, 'footprint_m': [list(p) for p in list(footprint.exterior.coords)[:-1]]})
    return {'schema': 'dialux-agent/layout/v1', 'units': 'm', 'fixtures': fixtures,
            'fixture_count': len(fixtures), 'candidate_count': count, 'rejected': rejected,
            'room_area_m2': room.area, 'assumptions': assumptions,
            'input_sha256': hashlib.sha256(json.dumps(spec, sort_keys=True, allow_nan=False).encode()).hexdigest(),
            'simulation_verified': False, 'compliance_status': 'not_evaluated',
            'warnings': ['Placement geometry only; no optical/shadow calculation or illuminance guarantee.',
                         'Exclusions are planar placement keep-out areas, not simulated obstructions.']}
