import json
from pathlib import Path

import pytest
from shapely.geometry import Polygon, box

from src.cad_labels import place_fixture_labels
from src.layout import plan_grid
from src.cad import export_layout_dxf, _fixture_records
import ezdxf


def test_label_avoids_observed_keepout_collision():
    spec = json.loads((Path(__file__).parents[1]/'examples/synthetic-grid-layout.json').read_text())
    layout = plan_grid(spec)
    labels = place_fixture_labels(spec, layout, .25)
    fixture = next(f for f in layout['fixtures'] if f['id'] == 'L0013')
    assert labels['L0013']['center_m'][1] > fixture['position_m'][1]
    envelopes = [box(*v['envelope_m']) for v in labels.values()]
    for index, envelope in enumerate(envelopes):
        assert Polygon(spec['contour']).contains(envelope)
        assert not any(envelope.intersects(Polygon(p)) for p in spec['exclusions'])
        assert not any(envelope.intersects(other) for other in envelopes[index+1:])


def test_dense_room_refuses_unplaceable_label():
    spec = {'contour': [[0,0],[1,0],[1,1],[0,1]], 'fixture': {'width_m': .9, 'depth_m': .9}}
    layout = {'fixtures': [{'id': 'L0001', 'position_m': [.5,.5,3], 'rotation_deg': 0}]}
    with pytest.raises(ValueError, match='No clear label'):
        place_fixture_labels(spec, layout, .25)


def test_rotated_fixture_labels_remain_horizontal_and_preserve_anchor(tmp_path):
    spec = json.loads((Path(__file__).parents[1]/'examples/synthetic-grid-layout.json').read_text())
    spec['grid']['rotation_deg'] = 30
    spec['annotations'] = {'fixture_height_m': .25, 'note_height_m': .35}
    path = tmp_path/'rotated.dxf'
    result = export_layout_dxf(spec, str(path))
    doc = ezdxf.readfile(path)
    for insert in doc.modelspace().query('INSERT[layer=="LUMINAIRES"]'):
        label = insert.get_attrib('FIXTURE_ID')
        assert label.dxf.rotation == 0
        assert insert.dxf.rotation == 30
        assert tuple(label.dxf.align_point)[:2] == pytest.approx(
            result['label_placement'][label.dxf.text]['center_m'])
    before = _fixture_records(path)
    first = next(iter(doc.modelspace().query('INSERT[layer=="LUMINAIRES"]'))).get_attrib('FIXTURE_ID')
    first.dxf.insert = (999, 999, 0)  # derived glyph origin is not the alignment anchor
    doc.saveas(path)
    assert _fixture_records(path) == before
    first.dxf.align_point = (999, 999, 0)
    doc.saveas(path)
    assert _fixture_records(path) != before
