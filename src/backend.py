"""Validated adapter over the licensed MCP_Dialux serializer."""
from pathlib import Path
import math
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor' / 'MCP_Dialux'))
from dialux.stf import Estancia, escribir
from dialux.leer_stf import leer
from shapely.geometry import Polygon


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{field} must be a finite JSON number')
    return float(value)


def _validate_room(spec):
    if not isinstance(spec, dict):
        raise ValueError('Room specification must be an object')
    name = spec['name']
    if not isinstance(name, str) or not name.strip() or any(c in name for c in '\r\n[]'):
        raise ValueError('Invalid room name')
    name.encode('latin-1', errors='strict')
    if spec['units'] != 'm':
        raise ValueError('Explicit metre units required')
    if (not isinstance(spec['assumptions'], list) or not spec['assumptions']
            or any(not isinstance(a, str) or not a.strip() for a in spec['assumptions'])):
        raise ValueError('Document input sources or assumptions')
    contour = spec['contour']
    if (not isinstance(contour, list) or len(contour) < 3
            or any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in contour)):
        raise ValueError('Invalid contour coordinates')
    contour = [tuple(_number(v, 'Contour coordinate') for v in p) for p in contour]
    polygon = Polygon(contour)
    if not polygon.is_valid or polygon.area <= 0:
        raise ValueError('Contour must be a valid positive-area polygon')
    height, plane = _number(spec['height_m'], 'height_m'), _number(spec['workplane_m'], 'workplane_m')
    mf = _number(spec['maintenance_factor'], 'maintenance_factor')
    reflections = [_number(spec[k], k) for k in ('ceiling_reflectance_pct', 'wall_reflectance_pct', 'floor_reflectance_pct')]
    if not all(math.isfinite(x) for x in [height, plane, mf, *reflections]):
        raise ValueError('Parameters must be finite')
    if not 0 <= plane < height or not 0 < mf <= 1 or not all(0 <= x <= 100 for x in reflections):
        raise ValueError('Invalid height, workplane, maintenance factor or reflectances')
    room = Estancia(name, [tuple(map(float, p)) for p in contour], height, plane, *reflections, mf)
    return room, polygon


def create_room(spec: dict, output: str) -> dict:
    if not isinstance(spec, dict):
        raise ValueError('Room specification must be an object')
    path = Path(output).resolve()
    if path.suffix.lower() != '.stf':
        raise ValueError('Output must have .stf extension')
    if path.exists():
        raise ValueError('Output already exists; choose a new version')
    room, polygon = _validate_room(spec)
    # Serialize privately, then acquire the destination exclusively. The earlier
    # existence check is useful feedback but cannot prevent a concurrent writer.
    with tempfile.TemporaryDirectory(prefix='dialux-stf-') as staging:
        staged = Path(staging) / 'room.stf'
        escribir([room], staged, proyecto='DIALux-agent', autor='DIALux-agent')
        data = staged.read_bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)
    return {'path': str(path), 'area_m2': polygon.area, 'room_count': 1,
            'assumptions': spec['assumptions'], 'dialux_import_verified': False,
            'warnings': ['Geometry exchange only; no photometry or simulation results.']}


def inspect_stf(path: str) -> dict:
    return leer(Path(path).resolve(strict=True))


def create_rooms(specs: list[dict], output: str) -> dict:
    """Serialize nonoverlapping same-level rooms using the licensed upstream writer.

    Shared boundaries are allowed. This validates exchange geometry, not native
    wall construction, room import, storey levels or lighting results.
    """
    if not isinstance(specs, list) or not specs or len(specs) > 100:
        raise ValueError('Expected 1 to 100 explicit same-level room specifications')
    validated = [_validate_room(spec) for spec in specs]
    names = [room.nombre for room, _ in validated]
    if len(set(names)) != len(names):
        raise ValueError('Room names must be unique')
    for index, (_, shape) in enumerate(validated):
        for _, other in validated[:index]:
            if shape.intersection(other).area > 1e-9:
                raise ValueError('Same-level room interiors overlap')
    target = Path(output).resolve()
    if target.suffix.lower() != '.stf' or target.exists():
        raise ValueError('Choose a new .stf output path')
    with tempfile.TemporaryDirectory(prefix='dialux-rooms-') as staging:
        staged = Path(staging) / 'rooms.stf'
        escribir([room for room, _ in validated], staged, proyecto='DIALux-agent', autor='DIALux-agent')
        parsed = leer(staged)
        if len(parsed['salas']) != len(specs):
            raise ValueError('Serialized room-count readback failed')
        data = staged.read_bytes()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(data)
    return {'path': str(target), 'room_count': len(specs),
            'rooms': [{'name': room.nombre, 'area_m2': shape.area, 'assumptions': spec['assumptions']}
                      for (room, shape), spec in zip(validated, specs)],
            'dialux_import_verified': False,
            'warnings': ['Same-level geometry exchange only; native wall topology, openings, obstacles and photometry are not verified.']}
