"""Validated adapter over the licensed MCP_Dialux serializer."""
from pathlib import Path
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor' / 'MCP_Dialux'))
from dialux.stf import Estancia, escribir
from dialux.leer_stf import leer
from shapely.geometry import Polygon


def _number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{field} must be a finite JSON number')
    return float(value)


def create_room(spec: dict, output: str) -> dict:
    if not isinstance(spec, dict):
        raise ValueError('Room specification must be an object')
    path = Path(output).resolve()
    if path.suffix.lower() != '.stf':
        raise ValueError('Output must have .stf extension')
    if path.exists():
        raise ValueError('Output already exists; choose a new version')
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
    escribir([room], path, proyecto='DIALux-agent', autor='DIALux-agent')
    return {'path': str(path), 'area_m2': polygon.area, 'room_count': 1,
            'assumptions': spec['assumptions'], 'dialux_import_verified': False,
            'warnings': ['Geometry exchange only; no photometry or simulation results.']}


def inspect_stf(path: str) -> dict:
    return leer(Path(path).resolve(strict=True))
