from pathlib import Path
import sys

import ezdxf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from cad import drawing_convert, drawing_inspect, export_layout_dxf, _fixture_records
from layout import plan_grid
import json
import copy
import subprocess


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


def test_layout_export_preserves_fixture_identity_geometry_and_test_label(tmp_path):
    spec = json.loads((Path(__file__).resolve().parents[1] / 'examples/synthetic-grid-layout.json').read_text())
    spec['grid']['rotation_deg'] = 30
    layout = plan_grid(spec)
    target = tmp_path / 'layout.dxf'
    result = export_layout_dxf(spec, str(target), layout)
    doc = ezdxf.readfile(target)
    inserts = {e.get_attrib_text('FIXTURE_ID'): e for e in doc.modelspace().query('INSERT')}
    assert len(inserts) == layout['fixture_count'] > 0
    assert doc.units == 6
    for fixture in layout['fixtures']:
        entity = inserts[fixture['id']]
        assert tuple(entity.dxf.insert)[:2] == pytest.approx(fixture['position_m'][:2])
        assert entity.dxf.rotation == pytest.approx(30)
        assert entity.dxf.handle == result['fixture_handles'][fixture['id']]
    assert any('NOT FOR SUBMISSION' in e.dxf.text for e in doc.modelspace().query('TEXT'))
    assert result['dxf_readback_verified']
    assert not result['native_dwg_verified']
    assert not result['print_verified']
    before = target.read_bytes()
    with pytest.raises(ValueError, match='new .dxf'):
        export_layout_dxf(spec, str(target), layout)
    assert target.read_bytes() == before
    changed = copy.deepcopy(layout)
    changed['fixtures'][0]['position_m'][0] += 1
    with pytest.raises(ValueError, match='does not match'):
        export_layout_dxf(spec, str(tmp_path / 'changed.dxf'), changed)
    assert not (tmp_path / 'changed.dxf').exists()


def test_native_readback_rejects_ambiguous_identity(tmp_path):
    doc = ezdxf.new()
    doc.units = 6
    block = doc.blocks.new('PANEL')
    block.add_attdef('FIXTURE_ID')
    for x in (0, 1):
        entity = doc.modelspace().add_blockref('PANEL', (x, 0), dxfattribs={'layer': 'LUMINAIRES'})
        entity.add_auto_attribs({'FIXTURE_ID': 'L0001'})
    path = tmp_path / 'duplicate.dxf'
    doc.saveas(path)
    with pytest.raises(ValueError, match='duplicate fixture ID'):
        _fixture_records(path)


def test_native_timeout_preserves_partial_console_evidence(tmp_path, monkeypatch):
    source = tmp_path / 'source.dwg'
    source.write_bytes(b'fixture')
    core = tmp_path / 'accoreconsole.exe'
    core.write_bytes(b'fixture')
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 90, output='Startup stalled'.encode('utf-16le'))
    monkeypatch.setattr(subprocess, 'run', timeout)
    target = tmp_path / 'failed'
    with pytest.raises(ValueError, match='timed out'):
        drawing_convert(str(source), str(target), str(core))
    assert (target / 'console.log').read_text() == 'Startup stalled'
    assert not (target / 'manifest.json').exists()
    assert source.read_bytes() == b'fixture'
