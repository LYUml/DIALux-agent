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


@pytest.mark.parametrize('rotation', [13, 23, 113])
@pytest.mark.parametrize('start,reverse', [(i, r) for i in range(4) for r in (False, True)])
def test_vertex_start_and_winding_do_not_change_grid(tmp_path, rotation, start, reverse):
    path = fixture(tmp_path)
    def extract():
        return drawing_read_tile_grid(str(path), hashlib.sha256(path.read_bytes()).hexdigest(),
                                      'Tiles', [10, 20], rotation)['grid']
    expected = extract()
    doc = ezdxf.readfile(path)
    for entity in doc.modelspace():
        points = list(entity.get_points())
        points = points[start:]+points[:start]
        entity.set_points(list(reversed(points)) if reverse else points)
    doc.saveas(path)
    actual = extract()
    for key in expected:
        assert actual[key] == pytest.approx(expected[key], abs=1e-8)


def test_large_layer_has_unique_traceable_cells(tmp_path):
    doc = ezdxf.new()
    doc.units = 4
    handles = set()
    for iy in range(40):
        for ix in range(70):
            x, y = ix*600, iy*600
            e = doc.modelspace().add_lwpolyline([(x,y),(x+600,y),(x+600,y+600),(x,y+600)],
                                               close=True, dxfattribs={'layer':'Tiles'})
            handles.add(e.dxf.handle)
    path = tmp_path/'large.dxf'
    doc.saveas(path)
    result = drawing_read_tile_grid(str(path), hashlib.sha256(path.read_bytes()).hexdigest(),
                                   'Tiles', [0,0], 0)
    assert result['tile_count'] == 2800
    assert {r['entity_handle'] for r in result['tiles']} == handles
    assert {tuple(r['cell']) for r in result['tiles']} == {(x,y) for y in range(40) for x in range(70)}
    assert result['grid']['origin_m'] == pytest.approx([.3,.3])
