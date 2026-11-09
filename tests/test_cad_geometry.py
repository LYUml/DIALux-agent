import hashlib
import ezdxf
import pytest
from src.cad_geometry import drawing_extract_boundary


def extract(path,handle,origin=None,angle=0):
    return drawing_extract_boundary(str(path),handle,hashlib.sha256(path.read_bytes()).hexdigest(),origin or [0,0],angle)


def test_concave_mm_boundary_with_explicit_storey_transform(tmp_path):
    doc=ezdxf.new(); doc.units=4
    e=doc.modelspace().add_lwpolyline([(10000,20000),(13000,20000),(13000,21000),(11000,21000),(11000,23000),(10000,23000)],close=True)
    path=tmp_path/'concave.dxf'; doc.saveas(path)
    before=path.read_bytes()
    result=extract(path,e.dxf.handle,[10,20],90)
    assert result['area_m2']==pytest.approx(5)
    assert result['contour'][1]==pytest.approx([0,-3])
    assert result['contour'][-1]==pytest.approx([3,0])
    assert result['source_to_metre_scale']==.001
    assert not result['semantic_room_boundary_verified']
    assert path.read_bytes()==before


@pytest.mark.parametrize('kind',['open','bulge','width','variable_width','extrusion','self_cross','units','paperspace'])
def test_ambiguous_or_unsupported_boundary_is_rejected(tmp_path,kind):
    doc=ezdxf.new(); doc.units=6
    model=doc.paperspace() if kind=='paperspace' else doc.modelspace()
    points=[(0,0),(4,0),(4,3),(0,3)]
    if kind=='self_cross': points=[(0,0),(4,3),(4,0),(0,3)]
    e=model.add_lwpolyline(points,close=kind!='open')
    if kind=='bulge': e.set_points([(0,0,1),(4,0,0),(4,3,0),(0,3,0)],format='xyb')
    if kind=='width': e.dxf.const_width=.2
    if kind=='variable_width': e.set_points([(0,0,.2,.2),(4,0,0,0),(4,3,0,0),(0,3,0,0)],format='xyse')
    if kind=='extrusion': e.dxf.extrusion=(0,0,-1)
    if kind=='units': doc.units=0
    path=tmp_path/'fixture.dxf'; doc.saveas(path)
    with pytest.raises(ValueError): extract(path,e.dxf.handle)


def test_stale_source_hash_cannot_select_reused_handle(tmp_path):
    doc=ezdxf.new(); doc.units=6
    e=doc.modelspace().add_lwpolyline([(0,0),(2,0),(2,2),(0,2)],close=True)
    path=tmp_path/'fixture.dxf'; doc.saveas(path)
    with pytest.raises(ValueError,match='hash'):
        drawing_extract_boundary(str(path),e.dxf.handle,'0'*64,[0,0],0)
