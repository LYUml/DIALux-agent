import copy,json
from pathlib import Path
import pytest
from src.array_execution import _apply_array_transform
from src.placement import _inspect_group_checkpoint
from src.layout import plan_grid

@pytest.fixture
def case(tmp_path):
 data=json.loads((Path(__file__).parents[1]/'examples/synthetic-array-transform.json').read_text())
 project=tmp_path/'synthetic.evo';project.write_bytes(b'original synthetic saved file')
 group='Project_Storey_Luminaires_Array'
 observed=data['observed'];observed.update(path=str(project),group_id=group)
 arrangement=data['arrangement'];arrangement.update(path=str(project),tree_item_id=group)
 state={'observed':observed,'writes':0,'mode':'normal'}
 root=tmp_path/'evidence'
 def inspect(project,group,count,folder):
  def page_reader(*a,**kw):
   start=kw.get('offset',0);end=min(start+4,count)
   return {**copy.deepcopy(state['observed']),'fixtures':copy.deepcopy(state['observed']['fixtures'][start:end]),
           'offset':start,'next_offset':end if end<count else None,'observed_count':end-start}
  return _inspect_group_checkpoint(project,group,count,folder,page_reader=page_reader)
 def editor(project,arrangement,values,record):
  assert json.loads((root/'journal.json').read_text())['state']=='pending_mutation'
  record({'state':'pending_field','field':'PolygonPosition_X'})
  state['writes']+=1
  if state['mode']=='throw': raise RuntimeError('unknown native outcome')
  if state['mode']!='no_move':
   for old,new in zip(state['observed']['fixtures'],plan_grid(data['spec'])['fixtures']):
    old['position_m']=new['position_m'];old['rotation_deg']=[0,0,new['rotation_deg']]
  if state['mode']=='identity': state['observed']['fixtures'][0]['runtime_id']=[99]
  return {'native_project_saved':False}
 args=dict(expected_project=str(project),spec=data['spec'],group_id=group,evidence_directory=str(root),
           inspector=inspect,array_reader=lambda *a:copy.deepcopy(arrangement),array_editor=editor)
 return args,state,root

def test_complete_before_after_and_unsaved_scope(case):
 args,state,root=case;r=_apply_array_transform(**args)
 assert r['state']=='geometry_verified_unsaved' and state['writes']==1
 assert r['after_verification']['geometry']['matched_count']==6
 assert not r['persistence_verified'] and not r['calculation_verified'] and not r['native_project_saved']
 assert (root/'before/observed.json').exists() and (root/'after/observed.json').exists()

@pytest.mark.parametrize('mode',['throw','no_move','identity'])
def test_failed_or_unverified_mutation_never_reports_success(case,mode):
 args,state,root=case;state['mode']=mode
 with pytest.raises(ValueError,match='requires inspection'): _apply_array_transform(**args)
 journal=json.loads((root/'journal.json').read_text())
 assert journal['state']=='failed' and not journal['native_outcome_verified']
 assert journal['field_events'][0]['state']=='pending_field'
 with pytest.raises(FileExistsError): _apply_array_transform(**args)
 assert state['writes']==1

def test_nonrigid_before_geometry_prevents_edits(case):
 args,state,root=case;state['observed']['fixtures'][0]['position_m'][0]+=.5
 with pytest.raises(ValueError): _apply_array_transform(**args)
 assert state['writes']==0
