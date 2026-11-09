import copy
import pytest
from src import mixed_schedule as mixed

@pytest.fixture
def case(monkeypatch):
 groups=[];products=[];rows=[];sections=[]
 for i,name in enumerate(['First','Second'],1):
  groups.append({'report_group':name,'layout':{'schema':'dialux-agent/layout/v1','origin':'supplied_native_observations',
   'units':'m','coordinate_frame':'active_storey','observations_sha256':'a'*64,'source_group_id':'native_'+name,
   'fixture_count':1,'fixtures':[{'id':f'L{i}','position_m':[i,1,3],'rotation_deg':0}]}})
  products.append({'group_name':name,'article_number':str(i),'quantity':1,'power_w':i*10})
  rows.append({'report_luminaire_number':i,'position_m':[i,1,3],'page':i,'group_name':name})
  sections.append(dict(first_page=i,last_page=i,expected_count=1,expected_group=name,expected_article_number=str(i)))
 report={'products':products,'fixtures':rows,'path':'native.pdf','sha256':'b'*64,'room_header':'Room'}
 monkeypatch.setattr(mixed,'read_report_arrangements',lambda **k:copy.deepcopy(report))
 request={'groups':groups,'report_request':dict(path='native.pdf',sections=sections,expected_count=2,expected_header='Room'),
          'alignment':dict(translation_m=[0,0,0],rotation_deg=0,evidence='Synthetic explicit identity correspondence')}
 return request,report

def test_keeps_each_product_and_spatial_link(case):
 request,report=case
 request['groups'].reverse()
 r=mixed.build_mixed_luminaire_schedule(**request)
 assert r['quantity']==2 and r['total_reported_fixture_power_w']==30
 assert [(x['fixture_id'],x['article_number']) for x in r['fixtures']]==[('L2','2'),('L1','1')]
 assert not r['group_mapping_authenticated'] and not r['photometry_identity_verified']

@pytest.mark.parametrize('change',['duplicate_drawing_id','duplicate_source','duplicate_group','missing_group','coincident_report',
 'wrong_position','bad_hash','no_alignment','wrong_count','planned_layout','swapped_mapping'])
def test_rejects_cross_group_or_observation_errors(case,change):
 request,report=case;groups=request['groups']
 if change=='duplicate_drawing_id': groups[1]['layout']['fixtures'][0]['id']='L1'
 if change=='duplicate_source': groups[1]['layout']['source_group_id']='native_First'
 if change=='duplicate_group': groups[1]['report_group']='First'
 if change=='missing_group': groups.pop()
 if change=='coincident_report': report['fixtures'][1]['position_m']=[1,1,3]
 if change=='wrong_position': groups[1]['layout']['fixtures'][0]['position_m']=[9,1,3]
 if change=='bad_hash': groups[0]['layout']['observations_sha256']='bad'
 if change=='no_alignment': request['alignment']['evidence']=''
 if change=='wrong_count': groups[0]['layout']['fixture_count']=2
 if change=='planned_layout': groups[0]['layout']['origin']='planned'
 if change=='swapped_mapping': groups[0]['report_group'],groups[1]['report_group']='Second','First'
 with pytest.raises(ValueError): mixed.build_mixed_luminaire_schedule(**request)
