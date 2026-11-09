import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import desktop
import windows_worker


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


def test_reminder_defers_without_saving_and_reads_fresh_state(reminder, monkeypatch):
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


def test_missing_or_ambiguous_lighting_mode_refuses_tool_fallback(monkeypatch):
    main = SimpleNamespace(descendants=lambda **k:[])
    monkeypatch.setattr(windows_worker, 'wait_control', lambda *a: pytest.fail('Tool accessed'))
    with pytest.raises(ValueError, match='lighting-design'):
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
    monkeypatch.setattr(windows_worker, 'set_storey_context', lambda *a: None)
    node = SimpleNamespace(element_info=SimpleNamespace(runtime_id=(7,1,2)),
                           is_visible=lambda: True, select=lambda: None, is_selected=lambda: True)
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
    with pytest.raises(RuntimeError, match='simulated'):
        windows_worker.launch(executable)
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
