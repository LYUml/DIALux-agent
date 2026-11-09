import copy
import ezdxf
import pytest
from src.cad import export_observed_layout_dxf
from src.design_data import observed_layout


@pytest.fixture
def drawing_case():
    spec={'units':'m','coordinate_frame':'active_storey','contour':[[0,0],[8,0],[8,6],[0,6]],
          'fixture':{'product_id':'SYNTHETIC','width_m':.6,'depth_m':.6,'mounting_height_m':3},
          'clearance_m':0,'assumptions':['Synthetic fixture dimensions only']}
    observed={'operation':'read_group_fixtures','coordinate_frame':'active_storey','offset':0,'next_offset':None,
              'group_id':'test-group','observed_count':2,'fixtures':[
                  {'position_m':[1.234,2.345,3],'rotation_deg':[0,0,37],'runtime_id':[1,2]},
                  {'position_m':[5.678,4.321,3],'rotation_deg':[0,0,13],'runtime_id':[1,3]}]}
    return spec,observed,['L012','L007']


def test_native_positions_not_regenerated_or_sorted(drawing_case,tmp_path):
    spec,observed,ids=drawing_case
    target=tmp_path/'actual.dxf'
    result=export_observed_layout_dxf(spec,observed,ids,str(target))
    layout=result['observed_layout']
    assert [f['id'] for f in layout['fixtures']]==ids
    assert [f['position_m'] for f in layout['fixtures']]==[f['position_m'] for f in observed['fixtures']]
    assert layout['fixtures'][0]['observed_runtime_id']==[1,2]
    doc=ezdxf.readfile(target)
    records={e.get_attrib_text('FIXTURE_ID'):e for e in doc.modelspace().query('INSERT')}
    for identity,fixture in zip(ids,observed['fixtures']):
        assert tuple(records[identity].dxf.insert)[:2]==pytest.approx(fixture['position_m'][:2])
        assert records[identity].dxf.rotation==fixture['rotation_deg'][2]
    assert not layout['photometry_identity_verified']
    assert not result['native_dwg_verified']


@pytest.mark.parametrize('kind',['count','duplicate_id','invalid_id','outside','partial','missing_assumptions'])
def test_bad_observed_export_never_writes_output(drawing_case,tmp_path,kind):
    spec,observed,ids=copy.deepcopy(drawing_case)
    if kind=='count': ids.pop()
    if kind=='duplicate_id': ids[1]=ids[0]
    if kind=='invalid_id': ids[0]='bad id'
    if kind=='outside': observed['fixtures'][0]['position_m'][0]=-.1
    if kind=='partial': observed['next_offset']=4
    if kind=='missing_assumptions': spec['assumptions']=[]
    target=tmp_path/'bad.dxf'
    with pytest.raises(ValueError): export_observed_layout_dxf(spec,observed,ids,str(target))
    assert not target.exists()

