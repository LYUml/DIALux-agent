"""Read an explicitly selected DXF tile layer as a rectangular lattice."""
import hashlib
import math
from pathlib import Path

import ezdxf

if __package__:
    from .layout import number, polygon
else:
    from layout import number, polygon


def drawing_read_tile_grid(path: str, expected_sha256: str, layer: str,
                           storey_origin_m: list[float], storey_rotation_deg: float) -> dict:
    """Require all selected entities to be congruent straight rectangular tiles.

    Missing cells are allowed, duplicate cells are not. This verifies a geometric
    lattice, not the semantic meaning of the layer or a room boundary.
    """
    source = Path(path).resolve(strict=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if source.suffix.lower() != '.dxf' or digest != expected_sha256:
        raise ValueError('Expected a hash-pinned DXF source')
    if not isinstance(layer, str) or not layer.strip():
        raise ValueError('Explicit layer required')
    if not isinstance(storey_origin_m, list) or len(storey_origin_m) != 2:
        raise ValueError('Explicit XY storey origin required')
    ox, oy = [number(v, 'storey origin') for v in storey_origin_m]
    rotation = number(storey_rotation_deg, 'storey rotation')
    doc = ezdxf.readfile(source)
    scales = {1: .0254, 2: .3048, 4: .001, 5: .01, 6: 1.}
    if doc.units not in scales:
        raise ValueError('Unsupported or unspecified INSUNITS')
    scale = scales[doc.units]
    entities = [e for e in doc.modelspace() if e.dxf.layer.casefold() == layer.casefold()]
    if not 2 <= len(entities) <= 10000:
        raise ValueError('Selected layer requires 2 to 10000 tiles')
    tolerance = .00001
    cosine, sine = math.cos(math.radians(rotation)), math.sin(math.radians(rotation))
    tiles = []
    basis = None
    for entity in entities:
        if entity.dxftype() != 'LWPOLYLINE' or not entity.closed:
            raise ValueError('Every selected entity must be a closed LWPOLYLINE')
        if tuple(entity.dxf.extrusion) != (0, 0, 1) or entity.dxf.get('const_width', 0):
            raise ValueError('Unsupported extrusion or polyline width')
        if entity.dxf.get('thickness', 0):
            raise ValueError('Tile thickness is unsupported')
        rows = list(entity.get_points('xyseb'))
        if len(rows) != 4:
            raise ValueError('Every tile requires exactly four vertices')
        points = []
        for row in rows:
            for value in row:
                number(float(value), 'tile coordinate')
            if any(row[2:]):
                raise ValueError('Tile curves and variable widths are unsupported')
            x, y = float(row[0]) * scale - ox, float(row[1]) * scale - oy
            points.append((x * cosine + y * sine, -x * sine + y * cosine))
        shape = polygon(points, 'tile')
        if basis is None:
            dx, dy = points[1][0] - points[0][0], points[1][1] - points[0][1]
            angle = math.atan2(dy, dx) % (math.pi / 2)
            # Floating point round-off at a quarter-turn must not swap axes
            # when the identical polyline starts at a different vertex.
            if min(angle, math.pi / 2 - angle) < 1e-12:
                angle = 0.0
            basis = math.cos(angle), math.sin(angle)
        c, s = basis
        projected = [(x * c + y * s, -x * s + y * c) for x, y in points]
        xmin, ymin = map(min, zip(*projected))
        xmax, ymax = map(max, zip(*projected))
        width, depth = xmax - xmin, ymax - ymin
        corners = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
        matches = []
        for point in projected:
            candidates = [i for i, corner in enumerate(corners)
                          if max(abs(a - b) for a, b in zip(point, corner)) <= tolerance]
            if len(candidates) != 1:
                raise ValueError('Tile is not a rectangle aligned to the common grid')
            matches.append(candidates[0])
        if len(set(matches)) != 4 or min(width, depth) <= tolerance * 10:
            raise ValueError('Degenerate or ambiguous tile')
        if not math.isfinite(shape.area):
            raise ValueError('Nonfinite tile area')
        tiles.append({'handle': entity.dxf.handle, 'center': [(xmin+xmax)/2, (ymin+ymax)/2],
                      'width': width, 'depth': depth,
                      'elevation_m': number(entity.dxf.elevation, 'tile elevation') * scale})
    first = tiles[0]
    sx, sy = first['width'], first['depth']
    bottom = min(t['center'][1] for t in tiles)
    anchor = min((t['center'] for t in tiles if t['center'][1] <= bottom + tolerance),
                 key=lambda p: p[0])
    occupied, records = set(), []
    for tile in tiles:
        if max(abs(tile['width']-sx), abs(tile['depth']-sy),
               abs(tile['elevation_m']-first['elevation_m'])) > tolerance:
            raise ValueError('Tiles differ in size or elevation')
        ix, iy = [round((v-a)/step) for v, a, step in zip(tile['center'], anchor, (sx, sy))]
        if max(abs(tile['center'][0]-anchor[0]-ix*sx),
               abs(tile['center'][1]-anchor[1]-iy*sy)) > tolerance:
            raise ValueError('Tile center is off the common lattice')
        if (ix, iy) in occupied:
            raise ValueError('Duplicate tile cell')
        occupied.add((ix, iy))
        records.append({'entity_handle': tile['handle'], 'cell': [ix, iy]})
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('Source changed during extraction')
    c, s = basis
    return {'schema': 'dialux-agent/cad-tile-grid/v1', 'source': str(source),
            'sha256': digest, 'layer': layer, 'insunits': int(doc.units),
            'source_to_metre_scale': scale, 'units': 'm', 'coordinate_frame': 'active_storey',
            'storey_origin_m': [ox, oy], 'storey_rotation_deg': rotation,
            'grid': {'origin_m': [anchor[0]*c-anchor[1]*s, anchor[0]*s+anchor[1]*c],
                     'spacing_x_m': sx, 'spacing_y_m': sy,
                     'rotation_deg': math.degrees(math.atan2(s, c))},
            'drawing_wcs_elevation_m': first['elevation_m'], 'tile_count': len(tiles),
            'tiles': records, 'tolerance_m': tolerance,
            'selected_layer_lattice_verified': True, 'semantic_ceiling_grid_verified': False,
            'room_boundary_verified': False,
            'warning': 'Missing cells are allowed. Lattice extension does not prove ceiling coverage or authorize fixture placement.'}
