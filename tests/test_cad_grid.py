import hashlib
import math

import ezdxf
import pytest

from src.cad_grid import drawing_read_tile_grid


def fixture(tmp_path, kind='normal'):
    doc = ezdxf.new()
    doc.units = 4
    angle = math.radians(23)
    cells = [(0, 0), (1, 0), (0, 2), (3, 2)]
    if kind == 'duplicate':
        cells.append((0, 0))
    for index, (ix, iy) in enumerate(cells):
        points = []
        for x, y in [(0, 0), (600, 0), (600, 300), (0, 300)]:
            x += ix*600 + (30 if kind == 'off_grid' and index == 2 else 0)
            y += iy*300
            points.append((10000+x*math.cos(angle)-y*math.sin(angle),
                           20000+x*math.sin(angle)+y*math.cos(angle)))
        if kind == 'skew' and index == 2:
            points[2] = (points[2][0]+20, points[2][1])
        e = doc.modelspace().add_lwpolyline(points, close=True, dxfattribs={'layer': 'Tiles'})
        if index == 2:
            if kind == 'elevation': e.dxf.elevation = 10
            if kind == 'width': e.dxf.const_width = 10
            if kind == 'open': e.closed = False
    if kind == 'line': doc.modelspace().add_line((0, 0), (1, 1), dxfattribs={'layer': 'Tiles'})
    if kind == 'units': doc.units = 0
    path = tmp_path/'tiles.dxf'
    doc.saveas(path)
    return path


def read(path, **kw):
    return drawing_read_tile_grid(str(path), hashlib.sha256(path.read_bytes()).hexdigest(),
                                  kw.get('layer', 'Tiles'), [10, 20], 13)


def test_rotated_rectangular_tiles_with_holes(tmp_path):
    path = fixture(tmp_path)
    original = path.read_bytes()
    result = read(path, layer='tiles')
    grid = result['grid']
    assert grid['rotation_deg'] == pytest.approx(10)
    assert grid['spacing_x_m'] == pytest.approx(.6)
    assert grid['spacing_y_m'] == pytest.approx(.3)
    a = math.radians(10)
    assert grid['origin_m'] == pytest.approx([.3*math.cos(a)-.15*math.sin(a),
                                             .3*math.sin(a)+.15*math.cos(a)])
    assert {tuple(t['cell']) for t in result['tiles']} == {(0, 0), (1, 0), (0, 2), (3, 2)}
    assert not result['semantic_ceiling_grid_verified']
    assert path.read_bytes() == original


@pytest.mark.parametrize('kind', ['duplicate', 'off_grid', 'skew', 'elevation', 'width', 'open', 'line', 'units'])
def test_rejects_ambiguous_grid(tmp_path, kind):
    with pytest.raises(ValueError): read(fixture(tmp_path, kind))


def test_hash_and_selection_required(tmp_path):
    path = fixture(tmp_path)
    with pytest.raises(ValueError, match='hash-pinned'):
        drawing_read_tile_grid(str(path), '0'*64, 'Tiles', [0, 0], 0)
    with pytest.raises(ValueError): read(path, layer='Missing')
