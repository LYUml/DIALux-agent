from pathlib import Path
import sys

import ezdxf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from cad import drawing_convert, drawing_inspect, export_layout_dxf, _fixture_records, plot_layout_native
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
    assert doc.styles.get('Standard').dxf.font == 'arial.ttf'
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


def test_native_plot_preserves_existing_output_directory(tmp_path, monkeypatch):
    source = tmp_path / 'input.dwg'; source.write_bytes(b'preserve')
    core = tmp_path / 'accoreconsole.exe'; core.write_bytes(b'fixture')
    target = tmp_path / 'plot'; target.mkdir()
    (target/'layout.pdf').write_bytes(b'preserve output')
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('Native process started'))
    with pytest.raises(ValueError, match='new ASCII'):
        plot_layout_native(str(source), str(target), ['L0001'], str(core))
    assert source.read_bytes() == b'preserve'
    assert (target/'layout.pdf').read_bytes() == b'preserve output'


@pytest.mark.parametrize('ids', [[], ['L0001','L0001'], ['L0001 extra'], [None]])
def test_native_plot_requires_unambiguous_fixture_labels(ids):
    with pytest.raises(ValueError, match='unique generated'):
        plot_layout_native('nonexistent.dwg', 'nonexistent', ids)


def test_pdf_scale_matches_geometry_not_annotation():
    from cad import verify_pdf_outline_scale
    outline=[[0,0],[6,0],[6,2],[4,2],[4,4],[0,4]]
    factor=1000/50*72/25.4
    points=[(200+x*factor,400-y*factor) for x,y in outline]
    points.append(points[0])
    curve={'pts':points,'path':[('m',points[0])]+[('l',p) for p in points[1:]]}
    result=verify_pdf_outline_scale([curve],outline,50)
    assert result['verified']
    assert result['maximum_coordinate_error_pt']<1e-10
    with pytest.raises(ValueError,match='Expected one'):
        verify_pdf_outline_scale([curve],outline,100)
    with pytest.raises(ValueError,match='found 2'):
        verify_pdf_outline_scale([curve,curve],outline,50)
    curve['path'][1]=('c',points[1])
    with pytest.raises(ValueError): verify_pdf_outline_scale([curve],outline,50)


@pytest.mark.parametrize('denominator,outline',[(True,[[0,0],[1,0],[0,1]]),(50,None),(None,[[0,0],[1,0],[0,1]]),(123,[[0,0],[1,0],[0,1]])])
def test_bad_fixed_scale_rejected_before_source_access(denominator,outline):
    with pytest.raises(ValueError):
        plot_layout_native('missing.dwg','missing',['L0001'],scale_denominator=denominator,scale_outline_m=outline)

@pytest.mark.parametrize('paper',['A4','A1\n_Y',None,1])
def test_bad_plot_paper_rejected_before_source_access(paper):
    with pytest.raises(ValueError,match='paper sizes'):
        plot_layout_native('missing.dwg','missing',['L0001'],paper=paper)


def test_drawing_annotation_sizes_are_explicit_and_preserved(tmp_path):
    spec=json.loads((Path(__file__).resolve().parents[1]/'examples/synthetic-grid-layout.json').read_text())
    spec['annotations']={'fixture_height_m':.25,'note_height_m':.35}
    target=tmp_path/'large-labels.dxf'
    export_layout_dxf(spec,str(target))
    doc=ezdxf.readfile(target)
    assert all(e.dxf.height==.25 for block in doc.modelspace().query('INSERT') for e in block.attribs)
    assert all(e.dxf.height==.35 for e in doc.modelspace().query('TEXT[layer=="NOTES"]'))
    spec['annotations']['fixture_height_m']=float('nan')
    with pytest.raises(ValueError):
        export_layout_dxf(spec,str(tmp_path/'invalid.dxf'))
    assert not (tmp_path/'invalid.dxf').exists()



def test_pdf_rectangle_path_uses_implicit_closure():
    from cad import verify_pdf_outline_scale
    factor=1000/100*72/25.4
    points=[(0,0),(30*factor,0),(30*factor,34*factor),(0,34*factor)]
    rect={'object_type':'rect','pts':points,'path':[('m',points[0])]+[('l',p) for p in points[1:]]+[('h',)]}
    assert verify_pdf_outline_scale([rect],[[0,0],[30,0],[30,34],[0,34]],100)['pdf_object_type']=='rect'
    with pytest.raises(ValueError): verify_pdf_outline_scale([rect],[[0,0],[30,0],[30,34],[0,34]],200)
    rect['object_type']='curve'
    with pytest.raises(ValueError): verify_pdf_outline_scale([rect],[[0,0],[30,0],[30,34],[0,34]],100)
