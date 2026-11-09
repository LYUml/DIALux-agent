import json
from pathlib import Path

import pytest
from shapely.geometry import Polygon, box

from src.cad_labels import place_fixture_labels
from src.layout import plan_grid


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
