import copy
import ezdxf
import pytest
from shapely.geometry import box
from src import mixed_schedule
from src.mixed_cad import export_mixed_scheduled_layout_dxf

@pytest.fixture
def case(tmp_path,monkeypatch):
 spec=dict(units='m',coordinate_frame='active_storey',contour=[[0,0],[8,0],[8,6],[0,6]],clearance_m=0,
  assumptions=['Synthetic differing dimensions for renderer verification'])
 groups=[];products=[];rows=[];sections=[]
 for i,(w,d) in enumerate([(.6,.6),(1.2,.3)],1):
  name='Group'+str(i);pos=[i*2,2,3]
  observed=dict(operation='read_group_fixtures',coordinate_frame='active_storey',offset=0,next_offset=None,observed_count=1,group_id=name,
    fixtures=[dict(position_m=pos,rotation_deg=[0,0,0],runtime_id=[7,i],name='Synthetic')])
  groups.append(dict(report_group=name,fixture=dict(product_id=name,width_m=w,depth_m=d,mounting_height_m=3),observed=observed,fixture_ids=['L00'+str(i)]))
  products.append(dict(group_name=name,article_number=str(i),quantity=1,power_w=20,luminaire_flux_lm=2000,reported_label=name))
  rows.append(dict(group_name=name,position_m=pos,report_luminaire_number=i,page=i))
  sections.append(dict(first_page=i,last_page=i,expected_count=1,expected_group=name,expected_article_number=str(i)))
 monkeypatch.setattr(mixed_schedule,'read_report_arrangements',lambda **k:dict(products=products,fixtures=rows,path='synthetic.pdf',sha256='b'*64,room_header='Room'))
 return dict(spec=spec,groups=groups,report_request=dict(path='synthetic.pdf',sections=sections,expected_count=2,expected_header='Room'),
  alignment=dict(translation_m=[0,0,0],rotation_deg=0,evidence='Synthetic identity transform'),output=str(tmp_path/'mixed.dxf'))

def test_symbols_and_labels_use_each_product_dimensions(case):
 before=copy.deepcopy(case);r=export_mixed_scheduled_layout_dxf(**case);assert case==before
 doc=ezdxf.readfile(r['path']);inserts=list(doc.modelspace().query('INSERT[layer=="LUMINAIRES"]'))
 assert len({e.dxf.name for e in inserts})==2
 for e,g in zip(inserts,case['groups']):
  points=list(doc.blocks.get(e.dxf.name).query('LWPOLYLINE'))[0].get_points('xy')
  assert max(p[0] for p in points)-min(p[0] for p in points)==pytest.approx(g['fixture']['width_m'])
  assert max(p[1] for p in points)-min(p[1] for p in points)==pytest.approx(g['fixture']['depth_m'])
  x,y=g['observed']['fixtures'][0]['position_m'][:2];w,d=g['fixture']['width_m'],g['fixture']['depth_m']
  label=box(*r['label_placement'][g['fixture_ids'][0]]['envelope_m'])
  assert not label.intersects(box(x-w/2,y-d/2,x+w/2,y+d/2))
 text=' '.join(e.dxf.text for e in doc.modelspace().query('TEXT[layer=="SCHEDULE"]'))
 assert 'L001' in text and 'L002' in text and 'Group1' in text and 'Group2' in text
 assert '0.6 x 0.6 m (supplied)' in text and '1.2 x 0.3 m (supplied)' in text

@pytest.mark.parametrize('change',['overlap','outside','duplicate_id','bad_dimension','partial','missing_assumptions'])
def test_invalid_mixed_inputs_never_write(case,change):
 from pathlib import Path
 if change=='overlap': case['groups'][1]['observed']['fixtures'][0]['position_m']=[2.5,2,3]
 if change=='outside': case['groups'][1]['observed']['fixtures'][0]['position_m']=[9,2,3]
 if change=='duplicate_id': case['groups'][1]['fixture_ids']=['L001']
 if change=='bad_dimension': case['groups'][1]['fixture']['width_m']=0
 if change=='partial': case['groups'][1]['observed']['next_offset']=1
 if change=='missing_assumptions': case['spec']['assumptions']=[]
 with pytest.raises(ValueError): export_mixed_scheduled_layout_dxf(**case)
 assert not Path(case['output']).exists()
