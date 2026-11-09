from pathlib import Path
import pytest
import ezdxf
from src.cad_symbols import fixture_block_records,compare_fixture_blocks
from src.cad import _fixture_records

@pytest.fixture
def drawing(tmp_path):
 p=tmp_path/'symbols.dxf';doc=ezdxf.new();doc.units=6
 for index,(w,d) in enumerate([(0.6,0.6),(1.2,0.3)],1):
  block=doc.blocks.new('TYPE'+str(index));block.add_lwpolyline([(0,0),(w,0),(w,d),(0,d)],close=True)
  block.add_line((0,0),(w,d));block.add_attdef('FIXTURE_ID',(0,-.2),height=.1)
  doc.modelspace().add_blockref(block.name,(index*2,0),dxfattribs={'layer':'LUMINAIRES'}).add_auto_attribs({'FIXTURE_ID':'L'+str(index)})
 doc.saveas(p);return p

def test_multiple_dimensions_and_roundoff(drawing):
 records=fixture_block_records(drawing)
 assert set(records)=={'TYPE1','TYPE2'}
 assert records['TYPE1']['shapes']!=records['TYPE2']['shapes']
 other=fixture_block_records(drawing);other['TYPE1']['base_point']=(1e-10,0,0)
 compare_fixture_blocks(records,other)

@pytest.mark.parametrize('change',['width','line','closed','bulge','base','attribute','extra','thickness'])
def test_detects_shape_changes_when_insertion_records_are_identical(drawing,change):
 before=fixture_block_records(drawing);insertions=_fixture_records(drawing)
 doc=ezdxf.readfile(drawing);block=doc.blocks.get('TYPE2');poly=list(block.query('LWPOLYLINE'))[0]
 if change=='width': poly.set_points([(0,0),(2,0),(2,.3),(0,.3)])
 if change=='line': list(block.query('LINE'))[0].dxf.end=(1,1,0)
 if change=='closed': poly.closed=False
 if change=='bulge':
  points=list(poly.get_points());points[0]=(0,0,0,0,.5);poly.set_points(points)
 if change=='base': block.block.dxf.base_point=(.1,0,0)
 if change=='attribute': list(block.query('ATTDEF'))[0].dxf.height=.2
 if change=='extra': block.add_line((0,0),(1,0))
 if change=='thickness': poly.dxf.thickness=.1
 doc.saveas(drawing)
 assert _fixture_records(drawing)==insertions
 with pytest.raises(ValueError,match='shapes'): compare_fixture_blocks(before,fixture_block_records(drawing))

def test_unknown_entity_refused(drawing):
 doc=ezdxf.readfile(drawing);doc.blocks.get('TYPE2').add_circle((0,0),.2);doc.saveas(drawing)
 with pytest.raises(ValueError,match='Unsupported'): fixture_block_records(drawing)
