import json,hashlib
import pytest
from test_array_execution import case
from src.array_execution import _apply_array_transform
from src.array_commit import commit_array_fields
from src.array_audit import verify_array_execution

@pytest.fixture
def evidence(case):
 args,state,root=case;original=args['array_editor']
 reader=args['array_reader']
 def named_reader(*a):
  result=reader(*a);result['display_values']['ArrangementObjectName']='Array';return result
 args['array_reader']=named_reader
 def editor(project,arrangement,target,record):
  original(project,arrangement,target,lambda _:None)
  live=dict(arrangement['display_values'])
  def write(key,value,focus): live[key]=str(value)
  return commit_array_fields(arrangement['display_values'],target,lambda:dict(live),write,record)
 args['array_editor']=editor
 _apply_array_transform(**args)
 return root

def test_replays_complete_hash_bound_execution(evidence):
 r=verify_array_execution(str(evidence))
 assert r['fixture_count']==6 and r['preflight_replayed'] and r['field_sequence_verified']
 assert not r['source_authenticity_verified'] and not r['persistence_verified']

@pytest.mark.parametrize('field',['ElementCountX','ElementCountY'])
def test_count_snapshot_requires_exact_integer_not_position_tolerance(evidence,field):
 p=evidence/'journal.json';j=json.loads(p.read_text())
 j['commit']['after'][field]+=.0001
 p.write_text(json.dumps(j))
 with pytest.raises(ValueError,match='Committed field differs'):
  verify_array_execution(str(evidence))

@pytest.mark.parametrize('change',['incomplete','events','commit','request_hash','arrangement','page','group'])
def test_corrupted_or_inconsistent_evidence_is_rejected(evidence,change):
 p=evidence/'journal.json';j=json.loads(p.read_text())
 if change=='incomplete': j['state']='pending_mutation'
 if change=='events': j['field_events'].pop()
 if change=='commit': j['commit']['after']['PolygonPosition_X']=999
 if change=='request_hash':
  q=evidence/'request.json';q.write_text(q.read_text()+' ')
 if change=='arrangement':
  q=evidence/'arrangement.json';d=json.loads(q.read_text());d['display_values']['PolygonPosition_X']='999';q.write_text(json.dumps(d));j['arrangement_sha256']=hashlib.sha256(q.read_bytes()).hexdigest()
 if change=='page':
  q=evidence/'after/page-0000.json';q.write_text(q.read_text()+' ')
 if change=='group': j['group_id']='different'
 p.write_text(json.dumps(j))
 with pytest.raises(ValueError): verify_array_execution(str(evidence))
