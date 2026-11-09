from pathlib import Path
import sys

import ezdxf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from cad import drawing_convert, drawing_inspect


def test_survey_keeps_units_handles_and_does_not_promote_grid_to_boundary(tmp_path):
    doc = ezdxf.new()
    doc.units = 4
    model = doc.modelspace()
    good = model.add_lwpolyline([(0, 0), (600, 0), (600, 600), (0, 600)], close=True,
                              dxfattribs={'layer': 'Ceiling Grid'})
    model.add_lwpolyline([(0, 0), (1, 0), (1, 1), (0, 1)], close=False,
                        dxfattribs={'layer': 'Ceiling Grid'})
    model.add_lwpolyline([(0, 0, 1), (1, 0, 0), (1, 1, 0), (0, 1, 0)], format='xyb', close=True,
                        dxfattribs={'layer': 'Ceiling Grid'})
    model.add_text('AREA = 42 m2', dxfattribs={'layer': 'ARCH'})
    path = tmp_path / 'test.dxf'
    doc.saveas(path)
    result = drawing_inspect(str(path))
    assert result['insunits'] == 4
    assert len(result['closed_four_vertex_grid_candidates']) == 1
    assert result['closed_four_vertex_grid_candidates'][0]['handle'] == good.dxf.handle
    assert not result['room_boundary_verified']
    assert result['texts'][0]['text'] == 'AREA = 42 m2'


def test_native_conversion_preserves_existing_destination(tmp_path):
    source = tmp_path / 'input.dwg'; source.write_bytes(b'fixture')
    core = tmp_path / 'accoreconsole.exe'; core.write_bytes(b'fixture')
    target = tmp_path / 'existing'; target.mkdir()
    with pytest.raises(ValueError, match='new output directory'):
        drawing_convert(str(source), str(target), str(core))
    assert source.read_bytes() == b'fixture'
    assert list(target.iterdir()) == []
