import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import desktop
import windows_worker


def test_snapshot_batches_buttons_without_hiding_duplicates_or_disabled_controls():
    calls = []
    def button(key, enabled):
        return SimpleNamespace(element_info=SimpleNamespace(automation_id=key), is_enabled=lambda:enabled)
    buttons = [button('Save',True),button('Save',True),button('CalculationButtonStart',False),
               button('DiscardResultsButton',True),button('Unrelated',True)]
    def descendants(**criteria):
        calls.append(criteria)
        return buttons if criteria == {'control_type':'Button'} else []
    main = SimpleNamespace(descendants=descendants, window_text=lambda:'Synthetic test')
    state = windows_worker.snapshot(SimpleNamespace(windows=lambda:[]), main, {'pid':1,'exe':'test'})
    assert calls.count({'control_type':'Button'}) == 1
    assert state['controls'] == {'Save':{'count':2,'enabled':False},
        'CalculationButtonStart':{'count':1,'enabled':False},
        'DiscardResultsButton':{'count':1,'enabled':True}}
    assert state['dialogs'] == []


@pytest.fixture
def reminder():
    return {'title':'DIALux','automation_id':'InformationBox','class':'Window',
            'children':[{'type':'Edit','text':'The project has not been saved for 5 minutes.\r\nSave now?'},
                        *[{'type':'Button','text':text} for text in ('','Yes','No')]]}


@pytest.mark.parametrize('mutation', ['none','overwrite','other_id','extra_edit','cancel','extra_dialog'])
def test_save_reminder_recognition_is_narrow(reminder, mutation, monkeypatch):
    if mutation == 'overwrite': reminder['children'][0]['text'] = 'Overwrite existing file?'
    if mutation == 'other_id': reminder['automation_id'] = 'SaveProject'
    if mutation == 'extra_edit': reminder['children'].append({'type':'Edit','text':'Other question'})
    if mutation == 'cancel': reminder['children'].append({'type':'Button','text':'Cancel'})
    if mutation == 'extra_dialog':
        state = {'dialogs':[reminder,reminder]}
        monkeypatch.setattr(windows_worker,'unique_control',lambda *a:pytest.fail('Dialog acted on'))
        assert windows_worker.defer_save_reminder(None,None,None,state) is state
    else:
        assert windows_worker.is_save_reminder(reminder) == (mutation == 'none')


def test_wrong_project_never_dismisses_reminder(tmp_path, reminder, monkeypatch):
    path = tmp_path/'intended.evo'
    path.write_bytes(b'fixture')
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:{'title':'other.evo - DIALux evo 14.1','dialogs':[reminder]})
    monkeypatch.setattr(windows_worker,'defer_save_reminder',lambda *a:pytest.fail('Dismissed wrong project reminder'))
    with pytest.raises(ValueError,match='does not match'):
        windows_worker.prepare_project(None,None,None,str(path))


def test_unknown_dialog_identity_is_retained_for_diagnosis(tmp_path, monkeypatch):
    path = tmp_path/'test.evo'
    path.write_bytes(b'fixture')
    state = {'title':str(path)+' - DIALux evo 14.1',
             'dialogs':[{'title':'Transient fixture','automation_id':'UnknownWindow','class':'Window','children':[]}]}
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:state)
    with pytest.raises(ValueError, match='UnknownWindow'):
        windows_worker.prepare_project(None,None,None,str(path))


@pytest.mark.parametrize('identity', [None, '', 'not-an-array'])
def test_arrangement_read_rejects_bad_identity_before_ui(identity,monkeypatch):
    monkeypatch.setattr(windows_worker,'project_tree',lambda *a:pytest.fail('UI accessed'))
    with pytest.raises(ValueError,match='arrangement tree'):
        windows_worker.read_arrangement(None,None,None,'test.evo',identity)


def test_arrangement_read_refuses_filtered_inventory(monkeypatch):
    monkeypatch.setattr(windows_worker,'project_tree',lambda *a:{'search_text':'filter'})
    monkeypatch.setattr(windows_worker,'wait_control',lambda *a:pytest.fail('Selected filtered array'))
    with pytest.raises(ValueError,match='unfiltered'):
        windows_worker.read_arrangement(None,None,None,'test.evo','Building_Luminaires_Array')


def saved_toast(path):
    return {'title':'','automation_id':'','class':'Popup','children':[
        {'type':'Text','text':f'The project has been saved at {path}.'},
        {'type':'Text','text':'Show in the Explorer'},
        *[{'type':'Button','text':v} for v in ('','Delete','Show in the Explorer')]]}


def test_save_toast_waits_without_clicking_and_rejects_other_project(tmp_path,monkeypatch):
    path=tmp_path/'test.evo'
    toast=saved_toast(path)
    assert windows_worker.is_saved_notification(toast,path)
    assert not windows_worker.is_saved_notification(toast,tmp_path/'other.evo')
    state={'dialogs':[toast]}
    after={'dialogs':[]}
    calls=[]
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:calls.append(True) or after)
    monkeypatch.setattr(windows_worker.time,'sleep',lambda *a:None)
    monkeypatch.setattr(windows_worker,'unique_control',lambda *a:pytest.fail('Clicked notification'))
    assert windows_worker.wait_saved_notification(None,None,None,path,state) is after
    assert calls==[True]
    calls.clear()
    assert windows_worker.wait_saved_notification(None,None,None,tmp_path/'other.evo',state) is state
    assert not calls


def test_toast_wait_never_hides_an_additional_unknown_dialog(tmp_path,monkeypatch):
    path=tmp_path/'test.evo'
    state={'dialogs':[saved_toast(path),{'class':'Window'}]}
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:pytest.fail('Waited through unknown dialog'))
    assert windows_worker.wait_saved_notification(None,None,None,path,state) is state


@pytest.mark.parametrize('outcome', ['gone', 'persistent', 'unknown', 'additional', 'other_project'])
def test_recognized_save_toast_empty_transition_has_one_deadline(tmp_path, monkeypatch, outcome):
    path = tmp_path/'test.evo'
    empty = {'title':'', 'automation_id':'', 'class':'Popup', 'children':[]}
    initial = {'dialogs':[saved_toast(path)]}
    faded = {'dialogs':[empty]}
    final = {'dialogs': [] if outcome == 'gone' else [empty] if outcome == 'persistent'
             else [{**empty, 'title':'Unknown'}] if outcome == 'unknown'
             else [empty, {'class':'Window'}] if outcome == 'additional'
             else [saved_toast(tmp_path/'other.evo')]}
    clock = [0.]; polls = []
    monkeypatch.setattr(windows_worker.time, 'monotonic', lambda:clock[0])
    monkeypatch.setattr(windows_worker.time, 'sleep', lambda seconds:clock.__setitem__(0, clock[0]+seconds))
    def snapshot(*args):
        polls.append(True)
        return faded if len(polls) == 1 else final
    monkeypatch.setattr(windows_worker, 'snapshot', snapshot)
    monkeypatch.setattr(windows_worker, 'unique_control', lambda *a:pytest.fail('Acted on popup'))
    assert windows_worker.wait_saved_notification(None,None,None,path,initial) is final
    assert len(polls) <= 41
    assert (clock[0] >= 8) is (outcome == 'persistent')
    if outcome != 'persistent': assert len(polls) == 2
    # An initially unknown empty popup is not promoted to a recognized toast.
    polls.clear()
    assert windows_worker.wait_saved_notification(None,None,None,path,faded) is faded
    assert not polls


def test_toast_wait_is_bounded_and_project_is_rechecked(tmp_path,monkeypatch):
    path=tmp_path/'test.evo'; path.write_bytes(b'fixture')
    state={'title':str(path)+' - DIALux evo 14.1','dialogs':[saved_toast(path)]}
    clock=iter([0,9])
    monkeypatch.setattr(windows_worker.time,'monotonic',lambda:next(clock))
    assert windows_worker.wait_saved_notification(None,None,None,path,state) is state
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:state)
    monkeypatch.setattr(windows_worker,'wait_saved_notification',lambda *a:{'title':'other.evo - DIALux evo 14.1','dialogs':[]})
    with pytest.raises(ValueError,match='does not match'):
        windows_worker.prepare_project(None,None,None,str(path))


@pytest.mark.parametrize('minutes', [5, 10, 20, 40])
def test_reminder_defers_without_saving_and_reads_fresh_state(reminder, monkeypatch, minutes):
    reminder['children'][0]['text'] = f'The project has not been saved for {minutes} minutes.\r\nSave now?'
    actions = []
    controls = [SimpleNamespace(element_info=SimpleNamespace(control_type=c['type']),
        window_text=lambda c=c:c['text'], click=lambda c=c:actions.append(c['text'])) for c in reminder['children']]
    window = SimpleNamespace(element_info=SimpleNamespace(automation_id='InformationBox'),
        window_text=lambda:'DIALux',class_name=lambda:'Window',
        descendants=lambda **kw:[c for c in controls if not kw or c.element_info.control_type==kw['control_type']])
    monkeypatch.setattr(windows_worker,'unique_control',lambda *a:window)
    monkeypatch.setattr(windows_worker.time,'sleep',lambda *a:None)
    after = {'dialogs':[]}
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:after)
    assert windows_worker.defer_save_reminder(None,None,None,{'dialogs':[reminder]}) is after
    assert actions == ['No']


@pytest.mark.parametrize('text', [
    'The project has not been saved for 10 minutes.\r\nOverwrite now?',
    'The project has not been saved for 0 minutes.\r\nSave now?',
    'The project has not been saved for 10 minutes.\r\nSave now? Extra text',
])
def test_unobserved_save_prompts_are_not_dismissed(reminder, text):
    reminder['children'][0]['text'] = text
    assert not windows_worker.is_save_reminder(reminder)


@pytest.mark.parametrize('name', ['', 'bad{ENTER}', 'bad^a', ' trailing ', 'x'*81, 12])
def test_arrangement_name_rejects_unsafe_or_invalid_input_before_ui(name, monkeypatch):
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: pytest.fail('UI accessed'))
    with pytest.raises(ValueError, match='name'):
        windows_worker.edit_arrangement(None,None,None,'test.evo',
            {'tree_item_id':'group','values':{'ArrangementObjectName':name}})


def test_project_tool_recovers_from_output_mode(monkeypatch):
    actions = []
    mode = SimpleNamespace(element_info=SimpleNamespace(automation_id=''),
        window_text=lambda: 'Dial.Dialux.InteractionModes.LightingDesignMode',
        select=lambda: actions.append('lighting'))
    main = SimpleNamespace(descendants=lambda **k:[mode])
    def wait(parent, kind, identity):
        assert identity == 'ProjectTreeTool'
        assert actions == ['lighting']
        return SimpleNamespace(select=lambda: actions.append('tree'))
    monkeypatch.setattr(windows_worker, 'wait_control', wait)
    windows_worker.select_lighting_tool(main,'ProjectTreeTool')
    assert actions == ['lighting','tree']


def test_missing_lighting_mode_and_goto_refuse_tool_fallback(monkeypatch):
    main = SimpleNamespace(descendants=lambda **k:[])
    monkeypatch.setattr(windows_worker, 'wait_control', lambda *a: pytest.fail('Tool accessed'))
    with pytest.raises(ValueError, match='MenuGotoConstructionMode'):
        windows_worker.select_lighting_tool(main,'ProjectTreeTool')


def test_rename_rejects_realized_duplicate_before_clearing_results(monkeypatch):
    candidate = SimpleNamespace(element_info=SimpleNamespace(runtime_id=[1]), is_visible=lambda:True)
    label = SimpleNamespace(element_info=SimpleNamespace(automation_id='_textBlock'), window_text=lambda:'Existing')
    other = SimpleNamespace(element_info=SimpleNamespace(runtime_id=[2]), descendants=lambda **k:[label])
    main = SimpleNamespace(descendants=lambda **k:[other])
    monkeypatch.setattr(windows_worker,'prepare_project',lambda *a:(Path('test.evo'),{}))
    monkeypatch.setattr(windows_worker,'select_lighting_tool',lambda *a:None)
    monkeypatch.setattr(windows_worker,'wait_control',lambda *a:candidate)
    monkeypatch.setattr(windows_worker,'unique_control',lambda *a:pytest.fail('Mutation attempted'))
    with pytest.raises(ValueError,match='already appears'):
        windows_worker.edit_arrangement(None,main,None,'test.evo',
            {'tree_item_id':'group','values':{'ArrangementObjectName':'Existing'}})


def test_room_context_rejects_empty_label_before_ui(monkeypatch):
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: pytest.fail('UI accessed'))
    with pytest.raises(ValueError, match='Room name'):
        windows_worker.room_context(None,None,None,'test.evo','')


def test_close_project_refuses_unsaved_changes_before_menu_action(monkeypatch):
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: (Path('test.evo'),
                        {'title':'test.evo* - DIALux evo 14.1'}))
    monkeypatch.setattr(windows_worker, 'unique_control', lambda *a: pytest.fail('Menu invoked'))
    with pytest.raises(ValueError, match='modified'):
        windows_worker.close_project(None,None,None,'test.evo',False)


def test_fixture_pages_reject_stale_order_and_require_continuation_token():
    nodes = [{'runtime_id':[7,1,i]} for i in range(5)]
    page, token, next_offset = windows_worker.fixture_page(nodes, 'group', 0, 2, None)
    assert len(page) == 2 and next_offset == 2
    last, _, tail = windows_worker.fixture_page(nodes, 'group', 4, 2, token)
    assert len(last) == 1 and tail is None
    with pytest.raises(ValueError, match='requires'):
        windows_worker.fixture_page(nodes, 'group', 2, 2, None)
    with pytest.raises(ValueError, match='changed'):
        windows_worker.fixture_page(list(reversed(nodes)), 'group', 2, 2, token)
    with pytest.raises(ValueError, match='limit'):
        windows_worker.fixture_page(nodes, 'group', 0, 100, None)


@pytest.mark.parametrize('runtime,prior,target', [
    ([], [1,2,3], [2,3,4]), ([True], [1,2,3], [2,3,4]),
    ([1], [1,2], [2,3,4]), ([1], [1,2,3], [2,3,float('inf')]),
    ([1], [1,2,3], [2,3,True])])
def test_fixture_edit_invalid_identity_or_geometry_never_touches_ui(runtime, prior, target, monkeypatch):
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: pytest.fail('UI accessed'))
    with pytest.raises(ValueError):
        windows_worker.edit_fixture(None, None, None, 'test.evo',
                                    {'runtime_id':runtime, 'expected_position_m':prior, 'position_m':target})


def test_fixture_stale_position_rejected_before_clearing_results(monkeypatch):
    monkeypatch.setattr(windows_worker,'select_lighting_tool',lambda *a:None)
    monkeypatch.setattr(windows_worker, 'set_storey_context', lambda *a: None)
    node = SimpleNamespace(element_info=SimpleNamespace(runtime_id=(7,1,2)),
                           is_visible=lambda: True, select=lambda: None, is_selected=lambda: True)
    monkeypatch.setattr(windows_worker,'container_elements',lambda *a:[SimpleNamespace(GetRuntimeId=lambda:[7,1,2])])
    monkeypatch.setattr(windows_worker,'materialize_tree_item',lambda *a:node)
    tree = SimpleNamespace(descendants=lambda **k: [node])
    def control(parent, kind, identity):
        if identity == 'DiscardResultsButton': pytest.fail('Cleared results before validating position')
        if kind == 'TabItem': return SimpleNamespace(select=lambda: None)
        if kind == 'List': return tree
        if kind == 'Edit': return SimpleNamespace(get_value=lambda: '2.0')
        pytest.fail('Unexpected control')
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: (Path('test.evo'),
                        {'controls': {'DiscardResultsButton': {'enabled': True}}}))
    monkeypatch.setattr(windows_worker, 'unique_control', control)
    monkeypatch.setattr(windows_worker, 'wait_control', control)
    with pytest.raises(ValueError, match='changed since inspection'):
        windows_worker.edit_fixture(None, None, None, 'test.evo',
                                    {'runtime_id':[7,1,2], 'expected_position_m':[1,1,1], 'position_m':[3,3,3]})


@pytest.mark.parametrize('failure', [None, 'selection', 'selection_without_dialog', 'position', 'unknown_dialog', 'missing_final_field', 'other_axis_changed', 'selection_during_readback'])
def test_movement_reminder_requires_identity_and_partial_coordinate_readback(monkeypatch, failure):
    values = [1., 1., 1.]
    pending = []
    lost_selection = []
    actions = []
    prepared = []
    node = SimpleNamespace(element_info=SimpleNamespace(runtime_id=[7,1,2]),
                           is_visible=lambda:True, select=lambda:None,
                           is_selected=lambda:not lost_selection and not (failure in ('selection','selection_without_dialog') and actions))
    def prepare(*args):
        prepared.append(True)
        if len(prepared)>1 and failure == 'unknown_dialog':
            raise ValueError('Unknown secondary dialog')
        return Path('test.evo'), {'controls':{'DiscardResultsButton':{'enabled':False}}}
    def control(parent, kind, identity):
        if kind == 'TabItem': return SimpleNamespace(select=lambda:None)
        if kind == 'List': return object()
        if failure == 'missing_final_field' and len(actions)==2:
            raise ValueError('Expected one PositionVectorControl_X, found 0')
        axis = 'XYZ'.index(identity[-1])
        def set_value(text):
            values[axis] = float(text)
            pending[:] = [axis]
        def focus():
            if pending and pending[0] != axis:
                changed = pending.pop()
                actions.append(changed)
                if failure == 'position': values[changed] = 1.
                if failure == 'other_axis_changed': values[2] = 7.
        def type_keys(*args, **kwargs):
            pytest.fail('Fixture commits must not use keyboard navigation')
        return SimpleNamespace(get_value=lambda:str(values[axis]), is_enabled=lambda:True,
                               iface_value=SimpleNamespace(CurrentIsReadOnly=False, SetValue=set_value),
                               set_focus=focus, type_keys=type_keys)
    monkeypatch.setattr(windows_worker,'prepare_project',prepare)
    monkeypatch.setattr(windows_worker,'unique_control',control)
    monkeypatch.setattr(windows_worker,'wait_control',control)
    def batch(main,keys):
        result={key:control(main,'Edit',key).get_value() for key in keys}
        if failure=='selection_during_readback' and actions: lost_selection.append(True)
        return result
    monkeypatch.setattr(windows_worker,'read_edit_values',batch)
    monkeypatch.setattr(windows_worker,'container_elements',lambda *a:[SimpleNamespace(GetRuntimeId=lambda:[7,1,2])])
    monkeypatch.setattr(windows_worker,'materialize_tree_item',lambda *a:node)
    monkeypatch.setattr(windows_worker,'select_lighting_tool',lambda *a:None)
    monkeypatch.setattr(windows_worker,'set_storey_context',lambda *a:None)
    monkeypatch.setattr(windows_worker.time,'sleep',lambda *a:None)
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:{'dialogs':[] if failure in ('selection_without_dialog','missing_final_field','other_axis_changed','selection_during_readback') else [{}]})
    parameters = {'runtime_id':[7,1,2], 'expected_position_m':[1,1,1], 'position_m':[2,3,1]}
    if failure:
        with pytest.raises(ValueError) as caught:
            windows_worker.edit_fixture(None,None,None,'test.evo',parameters)
        if failure == 'missing_final_field':
            assert 'after_axis' in str(caught.value) and 'completed_axes=' in str(caught.value)
            assert actions == [0,1]
            return
        assert actions == [0]  # never send another coordinate after a failed guard
    else:
        result = windows_worker.edit_fixture(None,None,None,'test.evo',parameters)
        assert result['after_position_m'] == [2,3,1]
        assert actions == [0,1]


def test_tree_identity_with_quotes_survives_worker_transport(monkeypatch):
    identity = 'Building_"Test"_Luminaires'
    monkeypatch.setattr(desktop.sys, 'platform', 'win32')
    def run(command, **kwargs):
        assert command[2] == 'project-tree'
        assert json.loads(command[command.index('--parameters') + 1]) == identity
        assert not kwargs.get('shell', False)
        return SimpleNamespace(returncode=0, stdout='{"items":[]}')
    monkeypatch.setattr(desktop.subprocess, 'run', run)
    assert desktop.desktop_project_tree('test.evo', identity) == {'items': []}


@pytest.mark.parametrize('identity', ['', ' ', None, 3])
def test_group_reader_rejects_missing_identity_before_ui(identity, monkeypatch):
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: pytest.fail('UI accessed'))
    with pytest.raises(ValueError, match='group_id'):
        windows_worker.read_group_fixtures(None, None, None, 'test.evo', identity)


@pytest.mark.parametrize('kind,text,nested,expected', [
    ('Text', '2.000 m', False, True), ('Text', '-0.5 m', False, True),
    ('Edit', '2.000 m', False, False), ('Text', 'Continue?', False, False),
    ('Text', '2.000 m', True, False)])
def test_dimension_popup_is_strictly_noninteractive(kind, text, nested, expected):
    child = SimpleNamespace(element_info=SimpleNamespace(control_type=kind),
                            window_text=lambda: text, children=lambda: [object()] if nested else [])
    window = SimpleNamespace(children=lambda: [child], class_name=lambda: 'Popup', window_text=lambda: '')
    assert windows_worker.is_dimension_label(window) == expected


@pytest.mark.parametrize('kind,expected', [('Text', True), ('Separator', True), ('Button', False), ('Edit', False)])
def test_tooltip_rejects_interactive_descendants(kind, expected):
    content = SimpleNamespace(element_info=SimpleNamespace(control_type=kind))
    tooltip = SimpleNamespace(element_info=SimpleNamespace(control_type='ToolTip'), descendants=lambda: [content])
    window = SimpleNamespace(children=lambda: [tooltip], class_name=lambda: 'Popup', window_text=lambda: '')
    assert windows_worker.is_plain_tooltip(window) == expected


@pytest.mark.parametrize('values', [{'ElementCountX': 0}, {'ElementCountY': 1.5},
                                  {'ElementCountX': True}, {'PolygonPosition_X': float('nan')},
                                  {'Unknown': 2}])
def test_arrangement_invalid_parameters_rejected_before_ui(values, monkeypatch):
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: pytest.fail('UI accessed'))
    with pytest.raises(ValueError):
        windows_worker.edit_arrangement(None, None, None, 'test.evo', {'tree_item_id': 'exact', 'values': values})


def test_launch_temp_is_process_local_and_restored_on_failure(tmp_path, monkeypatch):
    import os
    import tempfile
    import psutil
    import pywinauto
    executable = tmp_path / 'DIALux_x64.exe'
    executable.write_bytes(b'fixture only')
    monkeypatch.setattr(psutil, 'process_iter', lambda *a: [])
    monkeypatch.setenv('TEMP', 'original-temp')
    monkeypatch.setenv('TMP', 'original-tmp')
    def start(*a, **k):
        assert os.environ['TEMP'] == os.environ['TMP']
        assert Path(os.environ['TEMP']).is_absolute()
        assert Path(os.environ['TEMP']).is_dir()
        assert os.environ['TEMP'] != 'original-temp'
        raise RuntimeError('simulated launch failure')
    monkeypatch.setattr(pywinauto, 'Application', lambda **k: SimpleNamespace(start=start))
    with tempfile.TemporaryDirectory(prefix='dx-') as scratch:
        with pytest.raises(RuntimeError, match='simulated'):
            windows_worker.launch(executable, runtime_temp=scratch)
    assert os.environ['TEMP'] == 'original-temp'
    assert os.environ['TMP'] == 'original-tmp'


def test_pdf_export_refuses_existing_output_before_ui(tmp_path, monkeypatch):
    target = tmp_path / 'existing.pdf'
    target.write_bytes(b'preserve')
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: pytest.fail('UI accessed'))
    with pytest.raises(ValueError, match='new .pdf path'):
        windows_worker.export_pdf(None, None, None, 'test.evo', target)
    assert target.read_bytes() == b'preserve'


def test_luminaire_import_rejects_unsupported_file_before_ui(tmp_path, monkeypatch):
    path = tmp_path / 'wrong.exe'
    path.write_bytes(b'not photometry')
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: pytest.fail('UI accessed'))
    with pytest.raises(ValueError, match='photometry'):
        windows_worker.import_luminaire(None, None, None, 'test.evo', path, 'product')


def test_luminaire_requires_expected_product_before_worker(monkeypatch):
    monkeypatch.setattr(desktop, '_run', lambda *a, **k: pytest.fail('Worker accessed'))
    with pytest.raises(ValueError, match='nonempty'):
        desktop.desktop_import_luminaire('test.evo', 'fixture.uld', '')


def test_arrangement_refuses_existing_calculation_content(monkeypatch):
    state = {'controls': {'CalculationButtonStart': {'enabled': True},
                          'DiscardResultsButton': {'enabled': False}}}
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: (Path('test.evo'), state))
    text = SimpleNamespace(window_text=lambda: 'product', is_visible=lambda: True)
    window = SimpleNamespace(descendants=lambda **k: [text])
    monkeypatch.setattr(windows_worker, 'unique_control', lambda *a: pytest.fail('Placement invoked'))
    with pytest.raises(ValueError, match='duplicate placement'):
        windows_worker.arrange_space(None, window, None, 'test.evo', 'product')


def test_calculation_reports_process_exit_without_reading_stale_ui(monkeypatch):
    monkeypatch.setattr(windows_worker, "prepare_calculation_view", lambda *a: None)
    import psutil
    state = {'controls': {'CalculationButtonStart': {'enabled': True}}}
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *a: (Path('test.evo'), state))
    button = SimpleNamespace(element_info=SimpleNamespace(automation_id='CalculationButtonStart'),
                             is_enabled=lambda: True, click=lambda: None)
    window = SimpleNamespace(descendants=lambda **k: [button])
    monkeypatch.setattr(psutil, 'pid_exists', lambda pid: False)
    monkeypatch.setattr(windows_worker, 'snapshot', lambda *a: pytest.fail('Stale UI queried'))
    with pytest.raises(ValueError, match='process exited'):
        windows_worker.calculate(None, window, {'pid': 999}, 'test.evo')


def test_worker_timeout_reports_unknown_without_retry(monkeypatch):
    monkeypatch.setattr(desktop.sys, 'platform', 'win32')
    calls = []
    def timeout(*args, **kwargs):
        calls.append(args)
        raise subprocess.TimeoutExpired(args[0], 30)
    monkeypatch.setattr(desktop.subprocess, 'run', timeout)
    with pytest.raises(ValueError, match='outcome unknown'):
        desktop.desktop_save('test.evo')
    assert len(calls) == 1


def test_worker_failure_is_not_success(monkeypatch):
    monkeypatch.setattr(desktop.sys, 'platform', 'win32')
    monkeypatch.setattr(desktop.subprocess, 'run', lambda *a, **k:
                        SimpleNamespace(returncode=2, stdout=json.dumps({'error': 'Wrong active project'})))
    with pytest.raises(ValueError, match='Wrong active project'):
        desktop.desktop_save('test.evo')


def test_save_path_is_a_literal_argument(monkeypatch):
    monkeypatch.setattr(desktop.sys, 'platform', 'win32')
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout='{"status":"saved"}')
    monkeypatch.setattr(desktop.subprocess, 'run', run)
    path = 'C:/test room/a;literal.evo'
    assert desktop.desktop_save(path)['status'] == 'saved'
    assert calls[0][0][-1] == path
    assert not calls[0][1].get('shell', False)


def test_calculation_reset_is_explicit_and_bounded(monkeypatch):
    monkeypatch.setattr(desktop.sys, 'platform', 'win32')
    calls = []
    def run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout='{"status":"results_available"}')
    monkeypatch.setattr(desktop.subprocess, 'run', run)
    desktop.desktop_calculate('test.evo')
    desktop.desktop_calculate('test.evo', True)
    assert '--recalculate' not in calls[0][0]
    assert calls[1][0][-1] == '--recalculate'
    assert calls[1][1]['timeout'] == 75
    with pytest.raises(ValueError):
        desktop.desktop_calculate('test.evo', 'yes')
    assert len(calls) == 2


def test_uia_duplicate_tree_entries_are_not_arbitrary_first_match():
    def control(runtime):
        return SimpleNamespace(element_info=SimpleNamespace(runtime_id=runtime, automation_id='OpenProject'),
                               is_visible=lambda: True, is_enabled=lambda: True)
    one, two = control((1, 2, 3)), control((1, 2, 3))
    parent = SimpleNamespace(descendants=lambda **kwargs: [one, two])
    assert windows_worker.unique_control(parent, 'MenuItem', 'OpenProject') is two
    two.element_info.runtime_id = (4, 5, 6)
    with pytest.raises(ValueError, match='found 2'):
        windows_worker.unique_control(parent, 'MenuItem', 'OpenProject')


def test_open_preserves_modified_current_project(tmp_path, monkeypatch):
    target = tmp_path/'next.evo'
    target.write_bytes(b'synthetic')
    current = tmp_path/'current.evo'
    monkeypatch.setattr(windows_worker, 'prepare_project', lambda *args:
                        (current, {'title': str(current)+'* - DIALux evo 14.1'}))
    with pytest.raises(ValueError, match='modified'):
        windows_worker.open_project(None, None, None, str(target), str(current), False)


def test_save_as_refuses_existing_output_before_touching_app(tmp_path):
    path = tmp_path/'original.evo'
    path.write_bytes(b'original project')
    with pytest.raises(ValueError, match='existing files'):
        windows_worker.save_as(None, None, None, 'current.evo', str(path))
    assert path.read_bytes() == b'original project'


def test_modern_save_dialog_commits_filename_before_submit(tmp_path):
    model = {'visible': 'old.evo', 'committed': 'old.evo', 'saved': None}
    def set_text(value): model['visible'] = value
    def commit(*args, **kwargs): model['committed'] = model['visible']
    filename = SimpleNamespace(element_info=SimpleNamespace(runtime_id=(1,), automation_id='1001'),
                               is_visible=lambda: True, set_edit_text=set_text, set_focus=lambda: None,
                               type_keys=commit, get_value=lambda: model['visible'])
    def save(): model['saved'] = model['committed']
    button = SimpleNamespace(element_info=SimpleNamespace(runtime_id=(2,), automation_id='1'),
                             is_visible=lambda: True, is_enabled=lambda: True, click=save)
    dialog = SimpleNamespace(element_info=SimpleNamespace(runtime_id=(3,)), is_visible=lambda: True,
                             window_text=lambda: 'Save project',
                             descendants=lambda control_type: [filename] if control_type == 'Edit' else [button])
    main = SimpleNamespace(descendants=lambda **kwargs: [dialog])
    target = tmp_path/'new project.evo'
    windows_worker.submit_file_dialog(main, 'Save project', target)
    assert model['saved'] == str(target)


@pytest.mark.parametrize('initially_open',[True,False])
def test_calculation_monitor_presence_not_tab_visibility(monkeypatch,initially_open):
    state={'open':initially_open,'clicks':0}
    tab=SimpleNamespace(element_info=SimpleNamespace(automation_id='ResultsMonitorTool'),is_visible=lambda:False)
    main=SimpleNamespace(descendants=lambda **k:[tab] if state['open'] else [])
    monkeypatch.setattr(windows_worker,'select_lighting_tool',lambda *a:None)
    monkeypatch.setattr(windows_worker.time,'sleep',lambda *a:None)
    def click():
        state['open']=True
        state['clicks']+=1
    monkeypatch.setattr(windows_worker,'unique_control',lambda *a:SimpleNamespace(click_input=click))
    windows_worker.prepare_calculation_view(main)
    assert state['clicks']==(0 if initially_open else 1)


def test_related_edit_fields_are_read_in_one_traversal(monkeypatch):
    calls=[]
    def control(identity,runtime,value):
        return SimpleNamespace(element_info=SimpleNamespace(automation_id=identity,runtime_id=runtime),
            is_visible=lambda:True,get_value=lambda:value)
    x=control('X',[1],'3.0'); y=control('Y',[2],'4.0')
    main=SimpleNamespace(descendants=lambda **k:(calls.append(k) or [x,x,y]))
    assert windows_worker.read_edit_values(main,['X','Y'])=={'X':'3.0','Y':'4.0'}
    assert len(calls)==1
    main=SimpleNamespace(descendants=lambda **k:[x,control('X',[3],'9.0'),y])
    with pytest.raises(ValueError,match='exactly one'): windows_worker.read_edit_values(main,['X','Y'])
    main=SimpleNamespace(descendants=lambda **k:[x])
    with pytest.raises(ValueError,match='exactly one'): windows_worker.read_edit_values(main,['X','Y'])


def test_expected_group_count_rejects_virtualized_subset_before_fixture_selection(monkeypatch):
    monkeypatch.setattr(windows_worker,'project_tree',lambda *a:{'items':[], 'search_text':''})
    monkeypatch.setattr(windows_worker,'wait_control',lambda *a:None)
    element=SimpleNamespace(CurrentAutomationId='group_fixture',GetRuntimeId=lambda:[1])
    monkeypatch.setattr(windows_worker,'container_elements',lambda *a:[element])
    monkeypatch.setattr(windows_worker,'unique_control',lambda *a:pytest.fail('Fixture accessed'))
    with pytest.raises(ValueError,match='virtualized/incomplete'):
        windows_worker.read_group_fixtures(None,None,None,'test.evo','group',expected_count=168)


def test_item_container_enumerates_unrealized_rows_and_rejects_repetition():
    elements=[SimpleNamespace(GetRuntimeId=lambda i=i:[7,i]) for i in range(30)]
    class Container:
        def FindItemByProperty(self,previous,prop,value):
            index=0 if previous==0 else elements.index(previous)+1
            return elements[index] if index<len(elements) else None
    assert windows_worker.container_elements(SimpleNamespace(iface_item_container=Container()))==elements
    repeat=SimpleNamespace(FindItemByProperty=lambda *a:elements[0])
    with pytest.raises(ValueError,match='repeated'):
        windows_worker.container_elements(SimpleNamespace(iface_item_container=repeat))

@pytest.mark.parametrize('identity',['','group','x_Furniture and objects_','x_Furniture and objects_a_Furniture and objects_b',None])
def test_furniture_read_refuses_nonexplicit_identity_before_ui(identity,monkeypatch):
    monkeypatch.setattr(windows_worker,'project_tree',lambda *a:pytest.fail('UI accessed'))
    with pytest.raises(ValueError,match='furniture tree'):
        windows_worker.read_furniture(None,None,None,'test.evo',identity)


def test_furniture_tool_recovers_construction_mode(monkeypatch):
    actions=[]
    mode=SimpleNamespace(element_info=SimpleNamespace(automation_id=''),
        window_text=lambda:'Dial.Dialux.InteractionModes.BuildingConstructionMode',select=lambda:actions.append('mode'))
    main=SimpleNamespace(descendants=lambda **kw:[mode])
    tool=SimpleNamespace(select=lambda:actions.append('furniture'))
    monkeypatch.setattr(windows_worker,'wait_control',lambda *a:tool)
    windows_worker.select_furniture_tool(main)
    assert actions==['mode','furniture']


def test_lighting_tool_uses_native_goto_when_mode_tab_unrealized(monkeypatch):
    actions=[]
    main=SimpleNamespace(descendants=lambda **kw:[])
    menu=SimpleNamespace(iface_expand_collapse=SimpleNamespace(Expand=lambda:actions.append('expand')))
    command=SimpleNamespace(iface_invoke=SimpleNamespace(Invoke=lambda:actions.append('invoke')))
    tool=SimpleNamespace(select=lambda:actions.append('select'))
    monkeypatch.setattr(windows_worker,'unique_control',lambda *a:menu)
    monkeypatch.setattr(windows_worker,'wait_control',lambda parent,kind,identity:command if kind=='MenuItem' else tool)
    windows_worker.select_lighting_tool(main,'LuminaireArrangementTool')
    assert actions==['expand','invoke','select']

def test_open_waits_for_expanded_menu_before_invoking(tmp_path,monkeypatch):
    target=tmp_path/'test.evo';target.write_bytes(b'fixture')
    actions=[]
    main=SimpleNamespace(set_focus=lambda:actions.append('focus'))
    monkeypatch.setattr(windows_worker,'snapshot',lambda *a:{'title':'DIALux evo test','dialogs':[]})
    def unique(parent,kind,key):
        assert key=='File'
        return SimpleNamespace(iface_expand_collapse=SimpleNamespace(Expand=lambda:actions.append('expand')))
    def wait(parent,kind,key):
        assert actions==['focus','expand'] and key=='OpenProject'
        raise ValueError('Menu unavailable; no invocation')
    monkeypatch.setattr(windows_worker,'unique_control',unique)
    monkeypatch.setattr(windows_worker,'wait_control',wait)
    with pytest.raises(ValueError,match='no invocation'):
        windows_worker.open_project(None,main,None,str(target))

@pytest.mark.parametrize('outcome',['gone','persistent','named','additional'])
def test_empty_popup_wait_is_bounded_and_never_dismisses(monkeypatch,outcome):
    empty={'title':'','automation_id':'','class':'Popup','children':[]}
    initial={'dialogs':[empty]};clock=[0.];polls=[]
    monkeypatch.setattr(windows_worker.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(windows_worker.time,'sleep',lambda seconds:clock.__setitem__(0,clock[0]+seconds))
    after={'dialogs':[] if outcome=='gone' else [empty] if outcome=='persistent' else
           [{**empty,'title':'Unknown'}] if outcome=='named' else [empty,{'title':'Other'}]}
    def snapshot(*args):polls.append(True);return after
    monkeypatch.setattr(windows_worker,'snapshot',snapshot)
    assert windows_worker.wait_empty_popup(None,None,None,initial) is after
    assert 1<=len(polls)<=16
    assert (clock[0]>=3) is (outcome=='persistent')
    if outcome!='persistent':assert len(polls)==1
    assert windows_worker.wait_empty_popup(None,None,None,{'dialogs':[empty,empty]})['dialogs']==[empty,empty]
