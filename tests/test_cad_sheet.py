import json
from pathlib import Path
import pytest
import ezdxf
from src.cad import export_layout_dxf
from src.cad_schedule import schedule_records
from src.cad_sheet import add_sheet


def config():
    return dict(paper='A3',scale_denominator=100,title='Synthetic lighting layout',drawing_number='TEST-001',revision='A')


def test_sheet_preserves_fixture_coordinates_and_reads_back(tmp_path):
    spec=json.loads(Path('resources/examples/synthetic-apply-grid.json').read_text())
    plain=tmp_path/'plain.dxf';framed=tmp_path/'framed.dxf'
    export_layout_dxf(spec,str(plain));spec['sheet']=config()
    result=export_layout_dxf(spec,str(framed))
    from src.cad import _fixture_records
    assert _fixture_records(plain)==_fixture_records(framed)
    assert len(schedule_records(framed,'SHEET'))==12
    left,bottom,right,top=result['sheet']['frame_m']
    assert right-left==pytest.approx(38)
    assert top-bottom==pytest.approx(25.7)
    assert not result['sheet']['native_print_verified']


@pytest.mark.parametrize('field,value',[('title','Bad %%d'),('revision','x\ny'),('scale_denominator',True),('paper','A4')])
def test_invalid_metadata_rejected(field,value):
    doc=ezdxf.new();doc.units=6;doc.modelspace().add_line((0,0),(1,1))
    request=config();request[field]=value
    with pytest.raises(ValueError):add_sheet(doc,request)


def test_oversize_content_refused_without_rescaling():
    doc=ezdxf.new();doc.units=6;line=doc.modelspace().add_line((0,0),(100,100))
    with pytest.raises(ValueError,match='does not fit'):add_sheet(doc,config())
    assert tuple(line.dxf.end)==(100,100,0)
    assert 'SHEET' not in doc.layers
