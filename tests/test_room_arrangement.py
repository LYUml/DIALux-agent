import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from src import windows_worker as worker


def request(tmp_path):
    return dict(room_name='Synthetic corridor', group_name='Corridor', product_id='product',
                parent_id='Building_Storey_Luminaires', expected_groups=[],
                evidence_directory=str(tmp_path/'evidence'))


def test_existing_journal_prevents_ui_or_repeat(tmp_path, monkeypatch):
    spec=request(tmp_path)
    Path(spec['evidence_directory']).mkdir()
    monkeypatch.setattr(worker,'prepare_project',lambda *a:pytest.fail('UI accessed'))
    with pytest.raises(ValueError,match='already exists'):
        worker.arrange_room(None,None,None,'project.evo',spec)


def test_changed_inventory_prevents_creation_and_journal(tmp_path, monkeypatch):
    spec=request(tmp_path)
    monkeypatch.setattr(worker,'prepare_project',lambda *a:(Path('project.evo'),{}))
    monkeypatch.setattr(worker,'project_tree',lambda *a:{'search_text':'','items':[
        {'tree_item_id':'Building_Storey_Luminaires_Unexpected','expandable':True}]})
    with pytest.raises(ValueError,match='differ'):
        worker.arrange_room(None,None,None,'project.evo',spec)
    assert not Path(spec['evidence_directory']).exists()


def test_creation_exception_keeps_pending_intent_and_blocks_same_run(tmp_path,monkeypatch):
    spec=request(tmp_path)
    monkeypatch.setattr(worker,'prepare_project',lambda *a:(Path('project.evo'),
        {'controls':{'DiscardResultsButton':{'enabled':False}}}))
    monkeypatch.setattr(worker,'project_tree',lambda *a:{'search_text':'','items':[]})
    monkeypatch.setattr(worker,'room_context',lambda *a:{'active_room_verified':False})
    monkeypatch.setattr(worker,'singleton_room_context',lambda *a:{'active_room_verified':False})
    monkeypatch.setattr(worker,'select_lighting_tool',lambda *a:None)
    monkeypatch.setattr(worker,'snapshot',lambda *a:{'dialogs':[]})
    def click():
        journal=json.loads((Path(spec['evidence_directory'])/'journal.json').read_text())
        assert journal['state']=='pending_native_creation'
        raise RuntimeError('Native outcome unknown')
    monkeypatch.setattr(worker,'unique_control',lambda *a:SimpleNamespace(click=click))
    text=SimpleNamespace(window_text=lambda:'product',is_visible=lambda:True)
    main=SimpleNamespace(descendants=lambda **k:[] if k.get('control_type')=='Menu' else [text])
    with pytest.raises(ValueError,match='requires inspection'):
        worker.arrange_room(None,main,None,'project.evo',spec)
    journal=json.loads((Path(spec['evidence_directory'])/'journal.json').read_text())
    assert journal['failed_at']=='pending_native_creation'
    assert journal['state']=='failed'
    with pytest.raises(ValueError,match='already exists'):
        worker.arrange_room(None,main,None,'project.evo',spec)

@pytest.mark.parametrize('key,value', [('group_name','name{ENTER}'),('group_name','x'*41),
    ('expected_groups',['same','same']),('expected_groups','not-list'),('parent_id','wrong-parent')])
def test_invalid_creation_request_never_touches_ui(tmp_path,monkeypatch,key,value):
    spec=request(tmp_path)
    spec[key]=value
    monkeypatch.setattr(worker,'prepare_project',lambda *a:pytest.fail('UI accessed'))
    with pytest.raises(ValueError):
        worker.arrange_room(None,None,None,'project.evo',spec)

@pytest.mark.parametrize('case', ['success', 'filtered', 'two_rooms', 'wrong_label', 'wrong_identity', 'not_selected'])
def test_singleton_room_requires_complete_unique_named_selection(tmp_path, monkeypatch, case):
    parent='Building_Storey_Luminaires'
    identity='Building_Storey_Rooms and spaces_Test room'
    runtime=[7,1,2]
    element=SimpleNamespace(CurrentAutomationId=identity, GetRuntimeId=lambda:runtime)
    label=SimpleNamespace(element_info=SimpleNamespace(automation_id='_textBlock'), window_text=lambda:'Other' if case=='wrong_label' else 'Test room')
    calls=[]
    item=SimpleNamespace(element_info=SimpleNamespace(automation_id='wrong' if case=='wrong_identity' else identity,runtime_id=runtime),
        descendants=lambda **k:[label], select=lambda:calls.append('select'), is_selected=lambda:case!='not_selected')
    monkeypatch.setattr(worker,'project_tree',lambda *a:{'search_text':'filter' if case=='filtered' else ''})
    monkeypatch.setattr(worker,'wait_control',lambda *a:object())
    monkeypatch.setattr(worker,'container_elements',lambda *a:[element,element] if case=='two_rooms' else [element])
    monkeypatch.setattr(worker,'materialize_tree_item',lambda *a:item)
    monkeypatch.setattr(worker,'unique_control',lambda *a:SimpleNamespace(click_input=lambda:calls.append('activate')))
    monkeypatch.setattr(worker,'prepare_project',lambda *a:calls.append('guard'))
    if case=='success':
        result=worker.singleton_room_context(None,None,None,'test.evo',parent,'Test room')
        assert calls==['select','activate','guard']
        assert result['runtime_id']==runtime and result['active_room_verified'] is False
    else:
        with pytest.raises(ValueError):
            worker.singleton_room_context(None,None,None,'test.evo',parent,'Test room')
        assert 'activate' not in calls
