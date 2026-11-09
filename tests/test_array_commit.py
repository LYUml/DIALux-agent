import copy
import pytest
from src.array_commit import commit_array_fields,MOTION_FIELDS

@pytest.fixture
def case():
 values={'ElementCountX':'3','ElementCountY':'2','PolygonPosition_X':'3.000','PolygonPosition_Y':'2.000','PolygonPosition_Z':'3.035','ArrangementRotation_Z':'0.0','ArrangementObjectName':'Synthetic'}
 target=dict(zip(MOTION_FIELDS,[3.1,2.2,3.035,5]))
 return values,target

def test_ordered_intent_full_readback_and_noop(case):
 expected,target=case;live=copy.deepcopy(expected);events=[]
 def write(key,value,focus):
  assert events[-1]['state']=='pending_field' and events[-1]['field']==key
  assert focus!=key and focus in MOTION_FIELDS
  live[key]=str(value)
 result=commit_array_fields(expected,target,lambda:dict(live),write,events.append)
 assert result['completed_fields']==['PolygonPosition_X','PolygonPosition_Y','ArrangementRotation_Z']
 assert [e['state'] for e in events]==['pending_field','field_verified']*3
 assert result['after']['ElementCountX']==3 and not result['fixture_geometry_verified']

@pytest.mark.parametrize('field',['ElementCountX','ElementCountY','PolygonPosition_Z','ArrangementRotation_Z','ArrangementObjectName'])
def test_unrequested_changes_stop_after_first_axis(case,field):
 expected,target=case;live=copy.deepcopy(expected);writes=[];journal=[]
 def write(key,value,focus):
  writes.append(key);live[key]=str(value);live[field]='Changed' if field=='ArrangementObjectName' else '9'
 with pytest.raises(ValueError): commit_array_fields(expected,target,lambda:dict(live),write,journal.append)
 assert writes==['PolygonPosition_X'] and journal[-1]['state']=='pending_field'

def test_stale_state_never_writes(case):
 expected,target=case;live={**expected,'PolygonPosition_X':'4'}
 with pytest.raises(ValueError,match='initial state'):
  commit_array_fields(expected,target,lambda:live,lambda *a:pytest.fail('write'),lambda *a:pytest.fail('intent'))

def test_journal_failure_prevents_write(case):
 expected,target=case
 def fail(_): raise OSError('disk unavailable')
 with pytest.raises(OSError): commit_array_fields(expected,target,lambda:expected,lambda *a:pytest.fail('write'),fail)

@pytest.mark.parametrize('change',['nan','boolean','count_edit','missing_field','invalid_count','numeric_display'])
def test_invalid_request_never_reads(case,change):
 expected,target=case
 if change=='nan': target['PolygonPosition_X']=float('nan')
 if change=='boolean': target['PolygonPosition_X']=True
 if change=='count_edit': target['ElementCountX']=4
 if change=='missing_field': expected.pop('ElementCountY')
 if change=='invalid_count': expected['ElementCountX']='1.5'
 if change=='numeric_display': expected['PolygonPosition_X']=3
 with pytest.raises(ValueError): commit_array_fields(expected,target,lambda:pytest.fail('read'),None,None)
