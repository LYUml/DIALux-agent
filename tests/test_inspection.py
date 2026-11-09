import copy,json
from pathlib import Path
import pytest
from src import placement


@pytest.fixture
def pages(tmp_path):
    project=tmp_path/'test.evo';project.write_bytes(b'fixture')
    first={'operation':'read_group_fixtures','path':str(project),'group_id':'group','coordinate_frame':'active_storey',
           'container_node_count':2,'realized_node_count':2,'observed_count':1,'offset':0,'next_offset':1,
           'inventory_token':'token','fixtures':[{'runtime_id':[7,1],'position_m':[1,2,3],'rotation_deg':[0,0,0]}]}
    second=copy.deepcopy(first);second.update(offset=1,next_offset=None)
    second['fixtures'][0].update(runtime_id=[7,2],position_m=[4,2,3])
    return project,first,second


def test_inspection_persists_each_page_and_combined_evidence(pages,tmp_path,monkeypatch):
    project,first,second=pages
    def read(*a,**kw):
        assert kw['expected_count']==2
        if kw.get('offset',0)==0: return first
        journal=json.loads((tmp_path/'run'/'journal.json').read_text())
        assert journal['read_count']==1 and len(journal['pages'])==1
        return second
    monkeypatch.setattr(placement,'desktop_group_fixtures',read)
    result=placement._inspect_group_checkpoint(str(project),'group',2,str(tmp_path/'run'))
    assert result['state']=='collected'
    assert len(json.loads(Path(result['observed_path']).read_text())['fixtures'])==2
    assert not result['atomic_snapshot_verified']


@pytest.mark.parametrize('kind',['token','duplicate','wrong_group','wrong_frame','skipped_offset','truncated','geometry'])
def test_inconsistent_scan_retains_first_page_without_success(pages,tmp_path,monkeypatch,kind):
    project,first,second=pages
    if kind=='token': second['inventory_token']='changed'
    if kind=='duplicate': second['fixtures'][0]['runtime_id']=[7,1]
    if kind=='wrong_group': second['group_id']='other'
    if kind=='wrong_frame': second['coordinate_frame']='room_local'
    if kind=='skipped_offset': second['offset']=2
    if kind=='truncated': first['next_offset']=None
    if kind=='geometry': second['fixtures'][0]['position_m'][0]=float('nan')
    responses=iter([first,second])
    monkeypatch.setattr(placement,'desktop_group_fixtures',lambda *a,**k:next(responses))
    directory=tmp_path/'run'
    with pytest.raises(ValueError,match='Inspection failed'):
        placement._inspect_group_checkpoint(str(project),'group',2,str(directory))
    journal=json.loads((directory/'journal.json').read_text())
    assert journal['state']=='failed'
    assert not (directory/'observed.json').exists()
    assert journal['read_count']==(0 if kind=='truncated' else 1)
    with pytest.raises(FileExistsError):
        placement._inspect_group_checkpoint(str(project),'group',2,str(directory))

def test_public_inspection_uses_one_long_lived_worker(monkeypatch):
    from src import desktop
    calls=[]
    monkeypatch.setattr(desktop,'_run',lambda *a,**k:calls.append((a,k)) or {'state':'collected'})
    assert placement.inspect_group_checkpoint('x.evo','group',168,'evidence')['state']=='collected'
    assert calls==[(('inspect-group','x.evo'),{'parameters':{'group_id':'group','expected_count':168,'evidence_directory':'evidence'}})]


def test_worker_reuses_one_context_for_all_pages(pages,tmp_path,monkeypatch):
    from src import windows_worker
    project,first,second=pages
    contexts=[]
    def read(*args,**options):
        context=options['_context']
        contexts.append(context)
        if len(contexts)==1:
            context['retained_reference']=object()
            return first
        assert context is contexts[0] and 'retained_reference' in context
        return second
    monkeypatch.setattr(windows_worker,'read_group_fixtures',read)
    result=windows_worker.inspect_group(None,None,None,str(project),{
        'group_id':'group','expected_count':2,'evidence_directory':str(tmp_path/'persistent')})
    assert result['observed_count']==2 and len(contexts)==2


def test_persistent_reader_rejects_identity_change_before_selection(monkeypatch):
    from src import windows_worker
    from types import SimpleNamespace
    monkeypatch.setattr(windows_worker,'prepare_project',lambda *a:None)
    monkeypatch.setattr(windows_worker,'unique_control',lambda *a:pytest.fail('UI selection attempted'))
    context={'project':str(Path('x.evo').resolve()),'group_id':'group','inventory':{},
             'nodes':[{'runtime_id':[7,1],'tree_item_id':'group_child'}],
             'source_elements':{(7,1):SimpleNamespace(GetRuntimeId=lambda:[7,2],CurrentAutomationId='group_child')}}
    with pytest.raises(ValueError,match='Persistent fixture identity changed'):
        windows_worker.read_group_fixtures(None,None,None,'x.evo','group',_context=context)
