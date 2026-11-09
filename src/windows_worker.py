"""Windows-only worker. No Codex, sky client, coordinate clicks or remote server."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import sys
import time


def launch(executable, runtime_temp=None):
    import psutil
    from pywinauto import Application
    path = Path(executable).resolve(strict=True)
    if path.name.lower() != 'dialux_x64.exe':
        raise ValueError('Expected the installed DIALux_x64.exe')
    running = [p for p in psutil.process_iter(['name', 'exe'])
               if (p.info['name'] or '').lower() == 'dialux_x64.exe']
    if len(running) > 1:
        raise ValueError('Multiple DIALux processes are running')
    if running:
        if not running[0].info['exe'] or Path(running[0].info['exe']).resolve() != path:
            raise ValueError('Running DIALux executable differs from requested executable')
        app = Application(backend='uia').connect(process=running[0].pid)
    else:
        # libzmq 4.3.5's Windows IPC signaler failed with inherited 8.3 TEMP
        # on the validation machine. Use a plain, bounded path for this child
        # process only; never alter Windows/user environment configuration.
        scratch = Path(runtime_temp or Path(__file__).resolve().parents[1] / 'local' / 'tmp').resolve()
        if not str(scratch).isascii() or len(str(scratch)) > 70:
            raise ValueError('Use --runtime-temp with an ASCII directory path of at most 70 characters')
        scratch.mkdir(parents=True, exist_ok=True)
        previous = {key: os.environ.get(key) for key in ('TEMP', 'TMP')}
        try:
            os.environ.update(TEMP=str(scratch), TMP=str(scratch))
            app = Application(backend='uia').start('"' + str(path) + '"', timeout=20)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
    app.window(auto_id='MainWindow').wait('exists visible', timeout=30)
    return connect()


def connect():
    import psutil
    from pywinauto import Application
    candidates = []
    for process in psutil.process_iter(['pid', 'name', 'exe']):
        if (process.info['name'] or '').lower() == 'dialux_x64.exe':
            candidates.append(process.info)
    if len(candidates) != 1:
        raise ValueError(f'Expected exactly one DIALux process, found {len(candidates)}')
    process = candidates[0]
    if not process['exe'] or Path(process['exe']).name.lower() != 'dialux_x64.exe':
        raise ValueError('Could not verify DIALux executable')
    app = Application(backend='uia').connect(process=process['pid'], timeout=5)
    main = app.window(auto_id='MainWindow').wrapper_object()
    return app, main, process


def is_dimension_label(window):
    """Recognize only the observed noninteractive metric popup, at either UIA level."""
    children = window.children()
    return (window.class_name() == 'Popup' and not window.window_text()
            and len(children) == 1 and children[0].element_info.control_type == 'Text'
            and re.fullmatch(r'-?\d+(?:\.\d+)? m', children[0].window_text()) is not None
            and not children[0].children())


def is_plain_tooltip(window):
    children = window.children()
    return (window.class_name() == 'Popup' and not window.window_text()
            and len(children) == 1 and children[0].element_info.control_type == 'ToolTip'
            and all(c.element_info.control_type in {'Text', 'Image', 'Separator'} for c in children[0].descendants()))


def snapshot(app, main, process):
    controls = {}
    for control_id in ('Save', 'CalculationButtonStart', 'DiscardResultsButton'):
        matches = [c for c in main.descendants(control_type='Button') if c.element_info.automation_id == control_id]
        controls[control_id] = {'count': len(matches), 'enabled': len(matches) == 1 and matches[0].is_enabled()}
    dialogs = []
    for window in app.windows():
        if window.handle != main.handle and window.is_visible() and not is_dimension_label(window) and not is_plain_tooltip(window):
            dialogs.append({'title': window.window_text(), 'automation_id': window.element_info.automation_id, 'class': window.class_name(), 'children': [{'type': c.element_info.control_type, 'text': c.window_text()} for c in window.descendants()]})
    for window in main.descendants(control_type='Window'):
        if window.is_visible():
            children = window.children()
            # Arrangement selection exposes dimension labels as native popups.
            # Only an exact, noninteractive one-text metric label is exempt.
            if is_dimension_label(window) or is_plain_tooltip(window):
                continue
            button_ids = {c.element_info.automation_id for c in window.descendants(control_type='Button')}
            # Observed non-modal energy overlay; no other secondary UI is allowed.
            if not window.window_text() and button_ids == {
                'CloseEnergyTachometerButton', 'ShowEnergyTachometerMenuButton',
                'EnergyTachometerChangeToEnergyPerformanceToolButton'}:
                continue
            dialogs.append({'title': window.window_text(), 'automation_id': window.element_info.automation_id, 'class': window.class_name(), 'children': [{'type': c.element_info.control_type, 'text': c.window_text()} for c in window.descendants()]})
    return {'backend': 'pywinauto-uia', 'pid': process['pid'], 'executable': process['exe'],
            'title': main.window_text(), 'controls': controls, 'dialogs': dialogs,
            'uses_codex_computer_use': False}


def is_save_reminder(dialog):
    """Match only the observed English periodic reminder, not save/overwrite prompts."""
    children = dialog.get('children', [])
    prompts = [c.get('text', '') for c in children if c.get('type') == 'Edit']
    return (dialog.get('automation_id') == 'InformationBox'
            and dialog.get('title') == 'DIALux' and dialog.get('class') == 'Window'
            and all(c.get('type') in {'Button', 'Image', 'Text', 'Edit'} for c in children)
            and len(prompts) == 1 and isinstance(prompts[0], str)
            and re.fullmatch(r'The project has not been saved for [1-9][0-9]* minutes\.\r\nSave now\?', prompts[0]) is not None
            and sorted(c.get('text', '') for c in children if c.get('type') == 'Button') == ['', 'No', 'Yes'])


def defer_save_reminder(app, main, process, state):
    if len(state['dialogs']) != 1 or not is_save_reminder(state['dialogs'][0]):
        return state
    window = unique_control(main, 'Window', 'InformationBox')
    current = {'title': window.window_text(), 'automation_id': window.element_info.automation_id,
               'class': window.class_name(), 'children': [
                   {'type': c.element_info.control_type, 'text': c.window_text()} for c in window.descendants()]}
    if not is_save_reminder(current):
        raise ValueError('Save reminder changed before dismissal')
    buttons = [c for c in window.descendants(control_type='Button') if c.window_text() == 'No']
    if len(buttons) != 1:
        raise ValueError('Expected one save-reminder No button')
    buttons[0].click()
    time.sleep(.2)
    return snapshot(app, main, process)


def is_saved_notification(dialog, expected_project):
    children = dialog.get('children', [])
    texts = [c.get('text', '') for c in children if c.get('type') == 'Text' and c.get('text', '').strip()]
    prefix = 'The project has been saved at '
    messages = [t for t in texts if t.startswith(prefix) and t.endswith('.')]
    if len(messages) != 1 or sorted(texts) != sorted(['Show in the Explorer', messages[0]]):
        return False
    return (dialog.get('class') == 'Popup' and dialog.get('title') == ''
            and dialog.get('automation_id') == ''
            and all(c.get('type') in {'Custom','Image','Text','Button'} for c in children)
            and sorted(c.get('text', '') for c in children if c.get('type') == 'Button') == ['', 'Delete', 'Show in the Explorer']
            and Path(messages[0][len(prefix):-1]).resolve() == Path(expected_project).resolve())


def wait_saved_notification(app, main, process, expected, state):
    """Wait for an exact current-project save toast; never click its buttons."""
    deadline = time.monotonic()+8
    while (len(state['dialogs']) == 1 and is_saved_notification(state['dialogs'][0], expected)
           and time.monotonic() < deadline):
        time.sleep(.2)
        state = snapshot(app, main, process)
    return state


def prepare_project(app, main, process, expected_project, must_exist=True):
    expected = Path(expected_project).resolve(strict=must_exist)
    if expected.suffix.lower() != '.evo':
        raise ValueError('Expected an existing native .evo project')
    def verify_title(state):
        prefix, separator, version = state['title'].rpartition(' - DIALux evo ')
        if not separator or Path(prefix.rstrip('* ')).resolve() != expected:
            raise ValueError('Active project does not match expected_project')
    state = snapshot(app, main, process)
    verify_title(state)
    state = wait_saved_notification(app, main, process, expected, state)
    verify_title(state)
    state = defer_save_reminder(app, main, process, state)
    if state['dialogs']:
        raise ValueError('A DIALux secondary window/dialog is open; inspect before acting: '
                         + json.dumps(state['dialogs'], ensure_ascii=True))
    # WPF commands can report disabled while DIALux is inactive. Activation is
    # explicit and affects foreground focus, though Invoke does not move the mouse.
    main.set_focus()
    time.sleep(.3)
    state = snapshot(app, main, process)
    state = wait_saved_notification(app, main, process, expected, state)
    verify_title(state)
    state = defer_save_reminder(app, main, process, state)
    if state['dialogs']:
        raise ValueError('A dialog appeared after activation; operation was not invoked: '
                         + json.dumps(state['dialogs'], ensure_ascii=True))
    return expected, state


def save(app, main, process, expected_project):
    expected, state = prepare_project(app, main, process, expected_project)
    if not state['controls']['Save']['enabled']:
        raise ValueError('Save button is unavailable')
    before = expected.stat().st_mtime_ns
    button = [c for c in main.descendants(control_type='Button') if c.element_info.automation_id == 'Save'][0]
    button.click()  # UIA Invoke pattern, not shared mouse input
    deadline = time.monotonic() + 10
    previous = None
    stable = 0
    while time.monotonic() < deadline:
        stat = expected.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
        stable = stable + 1 if signature == previous else 0
        previous = signature
        if stat.st_mtime_ns != before and stable >= 3 and stat.st_size > 0 and main.is_enabled():
            data = expected.read_bytes()
            return {'operation': 'save', 'status': 'saved', 'path': str(expected),
                    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                    'evidence': 'Expected project matched; native file updated and stabilized after UIA Invoke',
                    'uses_codex_computer_use': False}
        time.sleep(.2)
    raise ValueError('Save was invoked but file update was not observed; outcome unverified, do not blindly retry')


def calculate(app, main, process, expected_project, recalculate=False):
    import psutil
    expected, state = prepare_project(app, main, process, expected_project)
    prepare_calculation_view(main)
    def button(control_id):
        found = [c for c in main.descendants(control_type='Button') if c.element_info.automation_id == control_id]
        if len(found) != 1 or not found[0].is_enabled():
            raise ValueError(f'Expected one enabled {control_id}')
        return found[0]
    if not state['controls']['CalculationButtonStart']['enabled']:
        if not recalculate:
            raise ValueError('Calculation unavailable; use recalculate only to explicitly discard cached results')
        button('DiscardResultsButton').click()
        time.sleep(.4)
        state = snapshot(app, main, process)
        if state['dialogs']:
            raise ValueError('Dialog after result reset; calculation not started')
    button('CalculationButtonStart').click()
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if not psutil.pid_exists(process['pid']):
            raise ValueError('DIALux process exited during calculation; no result verified. Inspect Windows Application Error logs before retry.')
        state = snapshot(app, main, process)
        if state['dialogs']:
            raise ValueError('Dialog during calculation; outcome unverified')
        texts = main.descendants(control_type='Text')
        obsolete = any('Obsolete results' in c.window_text() for c in texts if c.is_visible())
        busy = any(c.element_info.automation_id == 'CalculationCommandText' and c.window_text() == 'Cancel'
                   for c in texts)
        results = [{'id': c.element_info.automation_id, 'text': c.window_text()}
                   for c in texts
                   if c.element_info.automation_id in {'ResultsMonitorSurfaceResultAverage',
                                                       'ResultsMonitorSurfaceUniformityAverage'} and c.is_visible()]
        if (not state['controls']['CalculationButtonStart']['enabled']
                and state['controls']['DiscardResultsButton']['enabled'] and results and not obsolete and not busy):
            return {'operation': 'calculate', 'status': 'results_available', 'path': str(expected),
                    'results': results, 'native_project_saved': False,
                    'results_scoped': False,
                    'results_scope_warning': 'Monitor values have no verified room/surface identity. Use a scoped native report for assessment.',
                    'evidence': 'Calculation invoked from enabled state; results controls available afterward',
                    'uses_codex_computer_use': False}
        time.sleep(.3)
    raise ValueError('Calculation completion not observed within 45 seconds; outcome unverified')


def unique_control(parent, control_type, automation_id):
    # WPF menus can expose the same element twice in the tree. Runtime identity,
    # not arbitrary first-match selection, distinguishes that from ambiguity.
    matches = {c.element_info.runtime_id: c for c in parent.descendants(control_type=control_type)
               if c.element_info.automation_id == automation_id and c.is_visible()}
    if len(matches) != 1:
        raise ValueError(f'Expected one {automation_id}, found {len(matches)}')
    control = next(iter(matches.values()))
    if not control.is_enabled():
        raise ValueError(f'{automation_id} is disabled')
    return control


def wait_control(parent, control_type, automation_id, timeout=5):
    deadline = time.monotonic() + timeout
    while True:
        try:
            return unique_control(parent, control_type, automation_id)
        except ValueError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(.2)


def submit_file_dialog(main, title, path):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        matches = {c.element_info.runtime_id: c for c in main.descendants(control_type='Window')
                   if c.window_text() == title and c.is_visible()}
        if len(matches) == 1:
            dialog = next(iter(matches.values()))
            # Windows uses 1148 for Open and 1001 for the observed Save dialog.
            edits = {c.element_info.runtime_id: c for c in dialog.descendants(control_type='Edit')
                     if c.element_info.automation_id in {'1148', '1001'} and c.is_visible()}
            if not edits:
                time.sleep(.2)
                continue
            if len(edits) != 1:
                raise ValueError('Ambiguous native filename control')
            filename = next(iter(edits.values()))
            filename.set_edit_text(str(path))
            if filename.element_info.automation_id == '1001':
                # This Save dialog reads a keyboard-committed model; ValuePattern
                # alone changed the visible edit but saved the old suggested name.
                filename.set_focus()
                filename.type_keys('{END}{SPACE}{BACKSPACE}', set_foreground=False)
            if filename.get_value() != str(path):
                raise ValueError('File name readback mismatch; dialog not submitted')
            unique_control(dialog, 'Button', '1').click()
            return
        time.sleep(.2)
    raise ValueError(f'Expected native file dialog not observed: {title}')


def import_stf(app, main, process, source_path):
    from backend import inspect_stf
    source = Path(source_path).resolve(strict=True)
    if source.suffix.lower() != '.stf':
        raise ValueError('Expected an STF input file')
    parsed = inspect_stf(str(source))
    if not parsed.get('salas'):
        raise ValueError('STF contains no parsed rooms')
    state = snapshot(app, main, process)
    if not state['title'].startswith('DIALux evo ') or state['dialogs']:
        raise ValueError('STF import requires an empty DIALux workspace; existing work is preserved')
    main.set_focus()
    time.sleep(.3)
    unique_control(main, 'MenuItem', 'File').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'Import').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'ImportStf').iface_invoke.Invoke()
    submit_file_dialog(main, 'Load STF file', source)
    expected = source.with_suffix('.evo')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        state = snapshot(app, main, process)
        if state['dialogs']:
            raise ValueError('Dialog after STF import; inspect before retrying')
        prefix, sep, _ = state['title'].rpartition(' - DIALux evo ')
        if sep and Path(prefix.rstrip('* ')).resolve() == expected and main.is_enabled():
            return {'operation': 'import_stf', 'status': 'project_loaded', 'source': str(source),
                    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                    'proposed_native_path': str(expected), 'native_project_saved': False,
                    'parsed_input_rooms': len(parsed['salas']), 'geometry_verified_in_evo': False,
                    'uses_codex_computer_use': False}
        time.sleep(.3)
    raise ValueError('Imported project title not observed; outcome unverified')


def save_as(app, main, process, expected_project, target_path):
    target = Path(target_path).resolve()
    if target.suffix.lower() != '.evo' or target.exists():
        raise ValueError('Save As requires a new .evo path; existing files are preserved')
    if not target.parent.is_dir():
        raise ValueError('Save As parent directory must already exist')
    prepare_project(app, main, process, expected_project, must_exist=False)
    unique_control(main, 'MenuItem', 'File').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'SaveAs').iface_invoke.Invoke()
    submit_file_dialog(main, 'Save project', target)
    deadline = time.monotonic() + 20
    previous = None
    stable = 0
    while time.monotonic() < deadline:
        state = snapshot(app, main, process)
        if state['dialogs']:
            # A save notification is also an unnamed UIA window. Wait read-only
            # for it to disappear; never answer an overwrite/unknown dialog.
            time.sleep(.3)
            continue
        if target.exists():
            stat = target.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            stable = stable + 1 if previous == signature else 0
            previous = signature
            prefix, sep, _ = state['title'].rpartition(' - DIALux evo ')
            if (stable >= 2 and stat.st_size > 0 and sep and not prefix.endswith('*')
                    and Path(prefix).resolve() == target and main.is_enabled()):
                return {'operation': 'save_as', 'status': 'saved', 'path': str(target),
                        'bytes': stat.st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                        'uses_codex_computer_use': False}
        time.sleep(.3)
    raise ValueError('Save As completion not observed; outcome unverified')


def close_project(app, main, process, expected_project, save_current=False):
    expected, state = prepare_project(app, main, process, expected_project)
    prefix = state['title'].rpartition(' - DIALux evo ')[0]
    if prefix.endswith('*'):
        if not save_current:
            raise ValueError('Current project is modified; explicitly save before closing')
        save(app, main, process, expected_project)
        deadline = time.monotonic() + 5
        while snapshot(app, main, process)['dialogs'] and time.monotonic() < deadline:
            time.sleep(.2)
        prepare_project(app, main, process, expected_project)
    unique_control(main, 'MenuItem', 'File').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'CloseProject').iface_invoke.Invoke()
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        state = snapshot(app, main, process)
        if not state['dialogs'] and state['title'].startswith('DIALux evo '):
            return {'operation':'close_project', 'closed_project':str(expected), 'title':state['title'],
                    'uses_codex_computer_use':False}
        time.sleep(.3)
    raise ValueError('Project close not verified; inspect before retry')


def open_project(app, main, process, target_path, expected_current=None, save_current=False):
    target = Path(target_path).resolve(strict=True)
    if target.suffix.lower() != '.evo':
        raise ValueError('Only native .evo projects can be opened by this operation')
    if expected_current:
        current, state = prepare_project(app, main, process, expected_current)
        if current == target:
            return {'operation': 'open', 'status': 'already_open', 'path': str(target)}
        if state['title'].split(' - DIALux evo ')[0].rstrip().endswith('*'):
            if not save_current:
                raise ValueError('Current project is modified; save it or explicitly set save_current')
            save(app, main, process, expected_current)
    else:
        state = snapshot(app, main, process)
        if not state['title'].startswith('DIALux evo ') or state['dialogs']:
            raise ValueError('An existing project requires expected_current_project')
        main.set_focus()
    unique_control(main, 'MenuItem', 'File').iface_expand_collapse.Expand()
    unique_control(main, 'MenuItem', 'OpenProject').iface_invoke.Invoke()
    deadline = time.monotonic() + 10
    dialog = None
    while time.monotonic() < deadline:
        dialogs = {c.element_info.runtime_id: c for c in main.descendants(control_type='Window')
                   if c.window_text() == 'Open project' and c.is_visible()}
        if len(dialogs) == 1:
            dialog = next(iter(dialogs.values()))
            break
        time.sleep(.2)
    if dialog is None:
        raise ValueError('Native Open project dialog not observed')
    filename = unique_control(dialog, 'Edit', '1148')
    filename.set_edit_text(str(target))
    if filename.get_value() != str(target):
        raise ValueError('File name readback mismatch; open not submitted')
    unique_control(dialog, 'Button', '1').click()
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        state = snapshot(app, main, process)
        if state['dialogs']:
            raise ValueError('Unexpected dialog while opening; inspect current state')
        prefix, sep, _ = state['title'].rpartition(' - DIALux evo ')
        if sep and Path(prefix.rstrip('* ')).resolve() == target and main.is_enabled():
            return {'operation': 'open', 'status': 'opened', 'path': str(target),
                    'title': state['title'], 'uses_codex_computer_use': False}
        time.sleep(.3)
    raise ValueError('Requested project title not observed; open outcome unverified')


def import_luminaire(app, main, process, expected_project, path, product_id):
    source = Path(path).resolve(strict=True)
    if source.suffix.lower() not in {'.uld', '.ies', '.ldt'}:
        raise ValueError('Expected ULD, IES or LDT photometry')
    if not isinstance(product_id, str) or not product_id.strip():
        raise ValueError('Expected product identifier is required for UI readback')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    prepare_project(app, main, process, expected_project)
    unique_control(main, 'MenuItem', 'File').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'Import').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'ImportLuminaire').iface_invoke.Invoke()
    submit_file_dialog(main, 'Load luminaire files', source)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if snapshot(app, main, process)['dialogs']:
            time.sleep(.2)
            continue
        texts = [c.window_text() for c in main.descendants(control_type='Text') if c.is_visible()]
        if product_id in texts:
            values = {}
            for key in ('TotalLuminaireFlux_1', 'Load_1', 'LightOutputRatio_1', 'LightEfficiency_1'):
                values[key] = unique_control(main, 'Edit', key).get_value()
            return {'operation': 'import_luminaire', 'status': 'active_luminaire_observed',
                    'source': str(source), 'sha256': digest, 'product_id': product_id,
                    'photometry_display': values, 'placed_in_room': False,
                    'native_project_saved': False, 'uses_codex_computer_use': False,
                    'evidence': 'File dialog submitted; expected product and photometry visible. Existing catalog entries may be reused by DIALux.'}
        time.sleep(.2)
    raise ValueError('Expected active luminaire not observed; import outcome unverified')


def arrange_space(app, main, process, expected_project, product_id):
    expected, state = prepare_project(app, main, process, expected_project)
    if not product_id or product_id not in [c.window_text() for c in main.descendants(control_type='Text') if c.is_visible()]:
        raise ValueError('Expected active luminaire is not visible')
    if state['controls']['CalculationButtonStart']['enabled'] or state['controls']['DiscardResultsButton']['enabled']:
        raise ValueError('Existing calculation-ready content or results detected; refuse potentially duplicate placement')
    unique_control(main, 'Button', 'aid_ArrangementFromSpace').click()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            values = {key: unique_control(main, 'Edit', key).get_value() for key in
                      ('ArrangementObjectName', 'ElementCountX', 'ElementCountY',
                       'PolygonPosition_X', 'PolygonPosition_Y', 'PolygonPosition_Z')}
        except ValueError:
            time.sleep(.2)
            continue
        return {'operation': 'arrange_space', 'status': 'arrangement_observed',
                'coordinate_frame': 'active_view_context',
                'path': str(expected), 'arrangement': values,
                'native_project_saved': False, 'uses_codex_computer_use': False,
                'evidence': 'Native automatic arrangement invoked in current space; selected arrangement parameters read back. No illuminance target guarantee.'}
    raise ValueError('Arrangement was invoked but readback failed; inspect before retry')



def arrange_room(app, main, process, expected_project, parameters):
    """Journal one new native arrangement; geometry acceptance remains separate."""
    required = {'room_name', 'group_name', 'product_id', 'parent_id', 'expected_groups', 'evidence_directory'}
    if not isinstance(parameters, dict) or set(parameters) != required:
        raise ValueError('Expected explicit room, group, product, parent, existing groups and evidence directory')
    for key in required - {'expected_groups'}:
        if not isinstance(parameters[key], str) or not parameters[key].strip():
            raise ValueError('Arrangement request strings must be nonempty')
    name = parameters['group_name']
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,39}', name) or name != name.strip():
        raise ValueError('New group name must be 1 to 40 plain ASCII letters/digits/spaces/._-')
    groups = parameters['expected_groups']
    if not isinstance(groups, list) or any(not isinstance(g, str) or not g for g in groups) or len(set(groups)) != len(groups):
        raise ValueError('expected_groups must contain unique exact group IDs')
    parent = parameters['parent_id']
    if not parent.endswith('_Luminaires'):
        raise ValueError('Expected exact native storey Luminaires parent ID')
    directory = Path(parameters['evidence_directory']).resolve()
    if directory.exists():
        raise ValueError('Evidence directory already exists; inspect prior operation, never retry blindly')
    expected, _ = prepare_project(app, main, process, expected_project)
    before = project_tree(app, main, process, str(expected), parent)
    def group_nodes(tree):
        if tree['search_text']:
            raise ValueError('Project tree is filtered')
        return [n for n in tree['items'] if n['tree_item_id'].startswith(parent + '_') and n['expandable']]
    nodes = group_nodes(before)
    if sorted(n['tree_item_id'] for n in nodes) != sorted(groups):
        raise ValueError('Realized groups differ from expected_groups; no placement attempted')
    if any(name in n['labels'] for n in before['items']):
        raise ValueError('Requested group name already exists in realized tree')
    before_ids = {tuple(n['runtime_id']) for n in nodes}
    journal = {'schema':'dialux-agent/arrangement-run/v1', 'project':str(expected),
               'request':parameters, 'before_tree':before, 'state':'preparing',
               'native_project_saved':False, 'whole_project_verified':False}
    directory.mkdir(parents=True, exist_ok=False)
    def record():
        temporary = directory / 'journal.tmp'
        temporary.write_text(json.dumps(journal, indent=2, allow_nan=False), encoding='utf-8')
        temporary.replace(directory / 'journal.json')
    record()
    try:
        journal['room_selection'] = room_context(app, main, process, str(expected), parameters['room_name'])
        select_lighting_tool(main, 'LuminaireArrangementTool')
        if parameters['product_id'] not in [c.window_text() for c in main.descendants(control_type='Text') if c.is_visible()]:
            raise ValueError('Expected active product is not visible')
        _, state = prepare_project(app, main, process, str(expected))
        journal['state'] = 'pending_native_creation'
        record()  # A crash from this point leaves durable intent, not a safe retry.
        if state['controls']['DiscardResultsButton']['enabled']:
            unique_control(main, 'Button', 'DiscardResultsButton').click()
            time.sleep(.4)
        if snapshot(app, main, process)['dialogs']:
            raise ValueError('Dialog before placement')
        unique_control(main, 'Button', 'aid_ArrangementFromSpace').click()
        time.sleep(.7)
        after = project_tree(app, main, process, str(expected), parent)
        observed = group_nodes(after)
        new = [n for n in observed if tuple(n['runtime_id']) not in before_ids]
        if len(new) != 1 or not before_ids <= {tuple(n['runtime_id']) for n in observed}:
            raise ValueError('Expected exactly one new realized group and all previous groups')
        journal['created_node'] = new[0]
        journal['state'] = 'created_pending_name'
        record()
        candidates = [c for c in main.descendants(control_type='ListItem')
                      if tuple(c.element_info.runtime_id) == tuple(new[0]['runtime_id'])]
        if len(candidates) != 1 or not candidates[0].is_visible():
            raise ValueError('New group is not uniquely selectable')
        candidates[0].select()
        if not candidates[0].is_selected():
            raise ValueError('New group selection not observed')
        select_lighting_tool(main, 'LuminaireArrangementTool')
        control = unique_control(main, 'Edit', 'ArrangementObjectName')
        control.click_input()
        control.type_keys('^a', pause=.1)
        control.type_keys(name, pause=.2, with_spaces=True)
        control.type_keys('{TAB}', pause=.1)
        time.sleep(.3)
        if unique_control(main, 'Edit', 'ArrangementObjectName').get_value() != name:
            raise ValueError('Created group name did not commit')
        final = project_tree(app, main, process, str(expected), parent)
        matches = [n for n in group_nodes(final) if n['labels'] == [name]]
        if len(matches) != 1 or matches[0]['runtime_id'] != new[0]['runtime_id']:
            raise ValueError('Renamed group identity differs')
        journal.update(state='created_unverified', group_id=matches[0]['tree_item_id'], after_tree=final,
                       room_geometry_verified=False, existing_fixture_geometry_verified=False)
        record()
        return {'operation':'arrange_room', 'state':journal['state'], 'group_id':journal['group_id'],
                'journal':str(directory/'journal.json'), 'native_project_saved':False,
                'room_geometry_verified':False, 'existing_fixture_geometry_verified':False,
                'uses_codex_computer_use':False,
                'warning':'Only realized group identity verified. Read new and previous fixture geometry before accepting placement; do not repeat creation.'}
    except Exception as exc:
        journal['failed_at'] = journal['state']
        journal.update(state='failed', error=str(exc))
        record()
        raise ValueError(f'Arrangement outcome requires inspection: {directory / "journal.json"}: {exc}') from exc


def prepare_calculation_view(main):
    # Report output can hide result rows even after the solver finishes. The
    # monitor's dock tab itself is hidden in the observed layout, so visibility
    # of that TabItem is not an open/closed test; presence is the useful signal.
    select_lighting_tool(main, 'LuminaireArrangementTool')
    if not any(c.element_info.automation_id == 'ResultsMonitorTool'
               for c in main.descendants(control_type='TabItem')):
        unique_control(main, 'Button', 'ShowResultsMonitor').click_input()
        time.sleep(.3)
    if not any(c.element_info.automation_id == 'ResultsMonitorTool'
               for c in main.descendants(control_type='TabItem')):
        raise ValueError('Results monitor did not open; calculation not invoked')


def select_lighting_tool(main, tool_id):
    """Recover construction tools after native report output changes the mode."""
    matches = [c for c in main.descendants(control_type='TabItem')
               if c.element_info.automation_id == tool_id]
    if not matches:
        modes = [c for c in main.descendants(control_type='TabItem')
                 if c.window_text() == 'Dial.Dialux.InteractionModes.LightingDesignMode']
        if not modes and tool_id in {'LuminaireArrangementTool','ProjectTreeTool'}:
            # WPF may omit unselected top-mode tabs from UIA. Use the native
            # Goto command instead of relying on a screen coordinate.
            unique_control(main,'MenuItem','MenuGotoConstructionMode').iface_expand_collapse.Expand()
            wait_control(main,'MenuItem','MenuGotoShow'+tool_id).iface_invoke.Invoke()
            wait_control(main,'TabItem',tool_id).select()
            return
        if len(modes) != 1:
            raise ValueError('Expected one native lighting-design mode')
        modes[0].select()
        wait_control(main, 'TabItem', tool_id).select()
    else:
        unique_control(main, 'TabItem', tool_id).select()


def project_tree(app, main, process, expected_project, expand_id=None):
    """Inventory realized tree nodes, optionally expand one exact visible node."""
    if expand_id is not None and (not isinstance(expand_id, str) or not expand_id.strip()):
        raise ValueError('expand_id must be a nonempty string')
    expected, _ = prepare_project(app, main, process, expected_project)
    select_lighting_tool(main, 'ProjectTreeTool')
    tree = wait_control(main, 'List', 'FilterTreeListBox')
    search = unique_control(main, 'Edit', 'ProjectTreeToolSearch').get_value()
    if expand_id:
        try:
            candidates = [e for e in container_elements(tree) if e.CurrentAutomationId == expand_id]
        except ValueError:
            candidates = None
        if candidates is not None:
            if len(candidates) != 1:
                raise ValueError('Expansion target not unique in native item container')
            item = materialize_tree_item(candidates[0])
        else:
            item = wait_control(tree, 'ListItem', expand_id)
        if not item.is_visible():
            raise ValueError('Expansion target is not visible')
        checkbox = unique_control(item, 'CheckBox', 'ExpandCheckBox')
        if checkbox.get_toggle_state() == 0:
            checkbox.click_input()
            deadline = time.monotonic() + 5
            while checkbox.get_toggle_state() != 1:
                if time.monotonic() > deadline:
                    raise ValueError('Tree expansion not observed; inspect before retry')
                time.sleep(.1)
            time.sleep(.4)
        elif checkbox.get_toggle_state() != 1:
            raise ValueError('Unexpected expansion checkbox state')
    records = []
    for item in tree.descendants(control_type='ListItem'):
        identity = item.element_info.automation_id
        if not identity:
            continue
        labels = [c.window_text() for c in item.descendants(control_type='Text')
                  if c.element_info.automation_id == '_textBlock']
        checkboxes = [c for c in item.descendants(control_type='CheckBox')
                      if c.element_info.automation_id == 'ExpandCheckBox']
        records.append({'tree_item_id': identity, 'labels': labels, 'visible': item.is_visible(),
                        'runtime_id': list(item.element_info.runtime_id),
                        'expandable': len(checkboxes) == 1,
                        'expanded': checkboxes[0].get_toggle_state() == 1 if len(checkboxes) == 1 else None})
    return {'operation': 'project_tree', 'path': str(expected), 'items': records,
            'search_text': search, 'complete_inventory': False, 'uses_codex_computer_use': False,
            'warning': 'Only realized UIA nodes are listed; collapsed, filtered or virtualized nodes may be absent. IDs can change after renaming or count edits.'}


def room_context(app, main, process, expected_project, room_name=None):
    if room_name is not None and (not isinstance(room_name, str) or not room_name.strip()):
        raise ValueError('Room name must be a nonempty exact label')
    expected, _ = prepare_project(app, main, process, expected_project)
    menu = unique_control(main, 'Menu', 'Menu_RoomContextSelectionButton')
    opener = unique_control(menu, 'MenuItem', '_menuItemControl')
    opener.iface_expand_collapse.Expand()
    time.sleep(.3)
    choices = {}
    for item in main.descendants(control_type='MenuItem'):
        if item.element_info.automation_id.startswith('MenuItem_ToggleButton_RoomContextSelectionButton_') and item.is_visible():
            labels = {t.window_text() for t in item.descendants(control_type='Text') if t.window_text()}
            if len(labels) != 1:
                opener.iface_expand_collapse.Collapse()
                raise ValueError('Room context menu label is ambiguous')
            choices[tuple(item.element_info.runtime_id)] = (next(iter(labels)), item)
    labels = [name for name, _ in choices.values()]
    if not labels:
        opener.iface_expand_collapse.Collapse()
        raise ValueError('No room context choices observed')
    if room_name is None:
        opener.iface_expand_collapse.Collapse()
    else:
        matches = [item for name, item in choices.values() if name == room_name]
        if len(matches) != 1:
            opener.iface_expand_collapse.Collapse()
            raise ValueError('Expected one exact room context label')
        matches[0].iface_invoke.Invoke()
        time.sleep(.4)
    return {'operation':'room_context', 'path':str(expected), 'available_room_names':labels,
            'requested_room':room_name, 'selection_invoked':room_name is not None,
            'active_room_verified':False, 'uses_codex_computer_use':False,
            'warning':'Native menu exposes no selected-state readback. Verify resulting geometry before accepting a room-scoped edit.'}


def read_space(app, main, process, expected_project, tree_item_id):
    expected, _ = prepare_project(app, main, process, expected_project)
    select_lighting_tool(main, 'ProjectTreeTool')
    item = wait_control(main, 'ListItem', tree_item_id)
    if not item.is_visible():
        raise ValueError('Space node must be visible')
    item.select()
    if not item.is_selected():
        raise ValueError('Space selection failed')
    unique_control(main, 'TabItem', 'SpaceTool').select()
    fields = ('ObjectName', 'Height', 'WorkplaneNameTextBox', 'WorkplaneHeightDoubleBox',
              'WorkplaneMarginDoubleBox', 'MaintenanceFactor')
    values = {key: wait_control(main, 'Edit', key).get_value() for key in fields}
    if snapshot(app, main, process)['dialogs']:
        raise ValueError('Dialog during space inspection; values not verified')
    return {'operation':'read_space', 'path':str(expected), 'tree_item_id':tree_item_id,
            'display_values':values, 'boundary_geometry_verified':False, 'uses_codex_computer_use':False}


def fixture_page(nodes, group_id, offset, limit, inventory_token):
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 4:
        raise ValueError('offset must be nonnegative; limit must be 1 to 4')
    token = hashlib.sha256(json.dumps([group_id, [n['runtime_id'] for n in nodes]]).encode()).hexdigest()
    if offset and inventory_token is None:
        raise ValueError('Continuation requires inventory_token from the first page')
    if inventory_token is not None and inventory_token != token:
        raise ValueError('Tree inventory identity/order changed; restart inspection')
    if not nodes or offset >= len(nodes):
        raise ValueError('No fixture nodes at requested offset')
    end = min(offset + limit, len(nodes))
    return nodes[offset:end], token, end if end < len(nodes) else None


def set_storey_context(main):
    """Numeric position controls are view-relative; normalize to active storey."""
    unique_control(main, 'Button', 'ToggleButton_StoreyContextSelectionButton').click_input()
    time.sleep(.3)


def read_edit_values(main, keys):
    """Collect related native fields in one UIA traversal; retain uniqueness checks."""
    controls = {key: {} for key in keys}
    for control in main.descendants(control_type='Edit'):
        key = control.element_info.automation_id
        if key in controls and control.is_visible():
            controls[key][tuple(control.element_info.runtime_id)] = control
    if any(len(matches) != 1 for matches in controls.values()):
        raise ValueError('Expected exactly one visible control for every requested edit field')
    return {key: next(iter(matches.values())).get_value() for key, matches in controls.items()}


def container_elements(tree):
    """Use the native ItemContainer pattern, including unrealized WPF rows."""
    from pywinauto import uia_defines
    try:
        container = tree.iface_item_container
    except uia_defines.NoPatternInterfaceError as exc:
        raise ValueError('Native item-container pattern unavailable') from exc
    element = container.FindItemByProperty(0, 0, uia_defines.vt_empty)
    elements, seen = [], set()
    while element:
        runtime = tuple(element.GetRuntimeId())
        if runtime in seen or len(elements) >= 10000:
            raise ValueError('Native item-container enumeration repeated or exceeded limit')
        seen.add(runtime)
        elements.append(element)
        element = container.FindItemByProperty(element, 0, uia_defines.vt_empty)
    return elements


def materialize_tree_item(element):
    from pywinauto.uia_defines import get_elem_interface, NoPatternInterfaceError
    from pywinauto.uia_element_info import UIAElementInfo
    from pywinauto.controls.uiawrapper import UIAWrapper
    try:
        get_elem_interface(element, 'VirtualizedItem').Realize()
    except NoPatternInterfaceError:
        pass
    item = UIAWrapper(UIAElementInfo(element))
    if not item.is_visible():
        item.iface_scroll_item.ScrollIntoView()
        time.sleep(.2)
    if not item.is_visible():
        raise ValueError('Native item could not be made visible')
    return item


def read_group_fixtures(app, main, process, expected_project, group_id, offset=0, limit=4, inventory_token=None, expected_count=None, _context=None):
    """Read visible individual fixture parameters from one exact expanded group."""
    import math
    if not isinstance(group_id, str) or not group_id.strip():
        raise ValueError('group_id must be a nonempty string')
    if expected_count is not None and (type(expected_count) is not int or not 1 <= expected_count <= 2000):
        raise ValueError('expected_count must be 1 to 2000')
    context = _context if _context is not None else {}
    if not context:
        marker='_Luminaires_'
        if group_id.count(marker)==1:
            project_tree(app,main,process,expected_project,group_id.split(marker)[0]+'_Luminaires')
        inventory = project_tree(app, main, process, expected_project, group_id)
        if inventory['search_text']:
            raise ValueError('Cannot inspect a filtered fixture inventory')
        tree = wait_control(main, 'List', 'FilterTreeListBox')
        elements = container_elements(tree)
        source_elements = {tuple(e.GetRuntimeId()): e for e in elements
                           if e.CurrentAutomationId.startswith(group_id + '_')}
        nodes = [{'runtime_id': list(runtime), 'tree_item_id': element.CurrentAutomationId}
                 for runtime, element in source_elements.items()]
        context.update(inventory=inventory, source_elements=source_elements, nodes=nodes,
                       project=str(Path(expected_project).resolve()), group_id=group_id,
                       elements=elements)
    else:
        if context['project'] != str(Path(expected_project).resolve()) or context['group_id'] != group_id:
            raise ValueError('Persistent inventory belongs to another project or group')
        prepare_project(app, main, process, expected_project)
        inventory, source_elements, nodes = (context[key] for key in ('inventory', 'source_elements', 'nodes'))
        # Keep all COM references alive, but never accept changed cached identities.
        for node in nodes:
            element = source_elements[tuple(node['runtime_id'])]
            if list(element.GetRuntimeId()) != node['runtime_id'] or element.CurrentAutomationId != node['tree_item_id']:
                raise ValueError('Persistent fixture identity changed; restart inspection')
    total = len(nodes)
    if expected_count is not None and total != expected_count:
        raise ValueError(f'Only {total} inventory fixture nodes for expected {expected_count}; virtualized/incomplete inventory, no fixture read attempted')
    nodes, token, next_offset = fixture_page(nodes, group_id, offset, limit, inventory_token)
    fields = ['PositionVectorControl_' + axis for axis in 'XYZ'] + ['RotationVectorControl_' + axis for axis in 'XYZ']
    fixtures = []
    for node in nodes:
        unique_control(main, 'TabItem', 'ProjectTreeTool').select()
        tree = wait_control(main, 'List', 'FilterTreeListBox')
        item = materialize_tree_item(source_elements[tuple(node['runtime_id'])])
        matches = [item] if list(item.element_info.runtime_id) == node['runtime_id'] else []
        if len(matches) != 1 or not matches[0].is_visible():
            raise ValueError('Fixture UI identity changed or is not visible; inventory again')
        matches[0].select()
        if not matches[0].is_selected():
            raise ValueError('Native fixture selection was not confirmed')
        select_lighting_tool(main, 'LuminaireArrangementTool')
        set_storey_context(main)
        deadline = time.monotonic() + 5
        while True:
            try:
                displayed = read_edit_values(main, fields + ['ArrangementObjectName'])
                break
            except ValueError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.2)
        values = [float(displayed[key]) for key in fields]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite native fixture parameter')
        if snapshot(app, main, process)['dialogs']:
            # A periodic reminder can arrive between page preparation and readback.
            # Recheck project identity before dismissing only the known reminder,
            # then reject any changed selection or parameter values.
            prepare_project(app, main, process, expected_project)
            if not matches[0].is_selected():
                raise ValueError('Fixture selection changed while deferring reminder')
            fresh = read_edit_values(main, fields + ['ArrangementObjectName'])
            if fresh != displayed or snapshot(app, main, process)['dialogs']:
                raise ValueError('Fixture readback changed after dialog; inspection incomplete')
        fixtures.append({'runtime_id': node['runtime_id'], 'tree_item_id': node['tree_item_id'],
                         'name': displayed['ArrangementObjectName'],
                         'position_m': values[:3], 'rotation_deg': values[3:]})
    return {'operation': 'read_group_fixtures', 'path': inventory['path'], 'group_id': group_id,
            'coordinate_frame': 'active_storey',
            'offset': offset, 'next_offset': next_offset, 'inventory_token': token, 'realized_node_count': total,
            'inventory_source': 'native_item_container', 'container_node_count': total,
            'fixtures': fixtures, 'observed_count': len(fixtures), 'complete_inventory': False,
            'uses_codex_computer_use': False,
            'warning': 'UI-displayed coordinates rounded by DIALux. Native ItemContainer covers this expanded group, not collapsed or filtered project content. Runtime IDs are session-local. realized_node_count is a compatibility alias for container_node_count.'}


def inspect_group(app, main, process, expected_project, parameters):
    if not isinstance(parameters, dict) or set(parameters) != {'group_id', 'expected_count', 'evidence_directory'}:
        raise ValueError('Expected group_id, expected_count and evidence_directory')
    if __package__:
        from .placement import _inspect_group_checkpoint
    else:
        from placement import _inspect_group_checkpoint
    context = {}
    def reader(project, group_id, **options):
        return read_group_fixtures(app, main, process, project, group_id, _context=context, **options)
    return _inspect_group_checkpoint(expected_project, page_reader=reader, **parameters)


def apply_grid(app, main, process, expected_project, parameters):
    if not isinstance(parameters,dict) or set(parameters)!={'spec','group_id','evidence_directory'}:
        raise ValueError('Expected grid spec, group_id and evidence_directory')
    if __package__:
        from .placement import _apply_grid_layout
        from .layout import plan_grid
    else:
        from placement import _apply_grid_layout
        from layout import plan_grid
    expected_count=len(plan_grid(parameters['spec'])['fixtures'])
    context={}
    started=False
    def reader(project,group,**options):
        nonlocal started
        if not started:
            _,state=prepare_project(app,main,process,project)
            if state['controls']['DiscardResultsButton']['enabled']:
                unique_control(main,'Button','DiscardResultsButton').click()
                time.sleep(.4)
                if snapshot(app,main,process)['dialogs']:
                    raise ValueError('Dialog clearing results before grid inspection; no movement attempted')
            started=True
        return read_group_fixtures(app,main,process,project,group,expected_count=expected_count,_context=context,**options)
    def editor(project,runtime,before,target):
        return edit_fixture(app,main,process,project,{'runtime_id':runtime,'expected_position_m':before,'position_m':target},
                            _elements=context['source_elements'])
    return _apply_grid_layout(expected_project=expected_project,page_reader=reader,fixture_editor=editor,**parameters)


def select_furniture_tool(main):
    matches=[c for c in main.descendants(control_type='TabItem') if c.element_info.automation_id=='FurnitureTool']
    if not matches:
        modes=[c for c in main.descendants(control_type='TabItem')
               if c.window_text()=='Dial.Dialux.InteractionModes.BuildingConstructionMode']
        if len(modes)!=1: raise ValueError('Expected one native building-construction mode')
        modes[0].select()
    wait_control(main,'TabItem','FurnitureTool').select()


def read_furniture(app, main, process, expected_project, tree_item_id):
    """Read one explicit native furniture reference point, rotation and size."""
    import math
    marker='_Furniture and objects_'
    if not isinstance(tree_item_id,str) or tree_item_id.count(marker)!=1 or not tree_item_id.split(marker)[1]:
        raise ValueError('Expected exact furniture tree item ID')
    parent=tree_item_id.split(marker)[0]+'_Furniture and objects'
    inventory=project_tree(app,main,process,expected_project,parent)
    if inventory['search_text']: raise ValueError('Filtered furniture inventory is not supported')
    tree=wait_control(main,'List','FilterTreeListBox')
    elements=[e for e in container_elements(tree) if e.CurrentAutomationId==tree_item_id]
    if len(elements)!=1: raise ValueError('Furniture identity missing or ambiguous')
    runtime=list(elements[0].GetRuntimeId())
    item=materialize_tree_item(elements[0]);item.select()
    if not item.is_selected() or list(item.element_info.runtime_id)!=runtime:
        raise ValueError('Furniture selection identity changed')
    select_furniture_tool(main)
    set_storey_context(main)
    fields=[prefix+axis for prefix in ('PositionVectorControl_','RotationVectorControl_','SizeVectorControl_') for axis in 'XYZ']
    displayed=read_edit_values(main,fields+['ArrangementObjectName','EditableName'])
    values=[float(displayed[key]) for key in fields]
    if not all(math.isfinite(v) for v in values) or min(values[6:])<=0:
        raise ValueError('Invalid native furniture parameters')
    if displayed['ArrangementObjectName']!=tree_item_id.split(marker)[1]:
        raise ValueError('Furniture displayed name differs from selected identity')
    if snapshot(app,main,process)['dialogs']: raise ValueError('Dialog during furniture readback')
    return {'operation':'read_furniture','path':inventory['path'],'tree_item_id':tree_item_id,
            'runtime_id':runtime,'name':displayed['ArrangementObjectName'],
            'prototype_label':displayed['EditableName'],'coordinate_frame':'active_storey',
            'reference_position_m':values[:3],'rotation_deg':values[3:6],'size_m':values[6:],
            'shape_verified':False,'material_verified':False,'uses_codex_computer_use':False,
            'warning':'UI-displayed native object reference point, not assumed geometric centre. Dimensions do not prove mesh shape, material or optical effect.'}


def edit_fixture(app, main, process, expected_project, parameters, _elements=None):
    """Move one realized fixture with session identity and prior-position guards."""
    import math
    if not isinstance(parameters, dict) or set(parameters) != {'runtime_id', 'expected_position_m', 'position_m'}:
        raise ValueError('Expected runtime_id, expected_position_m and position_m')
    runtime = parameters['runtime_id']
    if not isinstance(runtime, list) or not runtime or any(type(n) is not int for n in runtime):
        raise ValueError('runtime_id must be a nonempty integer list from current inspection')
    for key in ('expected_position_m', 'position_m'):
        vector = parameters[key]
        if not isinstance(vector, list) or len(vector) != 3 or any(
                isinstance(n, bool) or not isinstance(n, (float, int)) or not math.isfinite(n) for n in vector):
            raise ValueError('Positions require three finite numbers in metres')
    expected, state = prepare_project(app, main, process, expected_project)
    fields = ['PositionVectorControl_' + axis for axis in 'XYZ']
    selected_item = []
    completed_axes = []
    def field_control(key, stage, wait=False):
        try:
            return (wait_control if wait else unique_control)(main, 'Edit', key)
        except ValueError as exc:
            raise ValueError(f'Fixture {stage}; field={key}; runtime_id={runtime}; '
                             f'completed_axes={completed_axes}; inspect native state before retry: {exc}') from exc
    def select_and_read():
        unique_control(main, 'TabItem', 'ProjectTreeTool').select()
        tree = wait_control(main, 'List', 'FilterTreeListBox')
        elements = list(_elements.values()) if _elements is not None else container_elements(tree)
        native = [e for e in elements if list(e.GetRuntimeId()) == runtime]
        if len(native)!=1: raise ValueError('Fixture runtime identity is stale or ambiguous')
        item=materialize_tree_item(native[0])
        matches=[item] if list(item.element_info.runtime_id)==runtime else []
        if len(matches) != 1 or not matches[0].is_visible():
            raise ValueError('Fixture runtime identity is stale, ambiguous or not visible')
        matches[0].select()
        if not matches[0].is_selected():
            raise ValueError('Fixture selection failed')
        selected_item[:] = matches
        select_lighting_tool(main, 'LuminaireArrangementTool')
        set_storey_context(main)
        current = [float(field_control(key,'initial_readback',wait=True).get_value()) for key in fields]
        if any(not math.isclose(a,b,rel_tol=0,abs_tol=.00051) for a,b in zip(current, parameters['expected_position_m'])):
            raise ValueError('Fixture position changed since inspection; no movement attempted')
        return current
    before = select_and_read()
    if state['controls']['DiscardResultsButton']['enabled']:
        unique_control(main, 'Button', 'DiscardResultsButton').click()
        time.sleep(.4)
        if snapshot(app, main, process)['dialogs']:
            raise ValueError('Dialog clearing results; movement not attempted')
        select_and_read()
    committed = list(before)
    for axis_index, (key, value, old) in enumerate(zip(fields, parameters['position_m'], before)):
        if math.isclose(value, old, rel_tol=0, abs_tol=1e-10):
            continue
        item = selected_item[0]
        if list(item.element_info.runtime_id) != runtime or not item.is_selected():
            raise ValueError(f'Fixture selection changed before writing {key}; completed_axes={completed_axes}')
        control = field_control(key,'before_write')
        if not control.is_enabled() or control.iface_value.CurrentIsReadOnly:
            raise ValueError('Fixture position is not editable; partial movement possible')
        control.set_focus()
        # Replace the numeric field atomically through UIA. Character-by-character
        # replacement can be interrupted by a reminder and concatenate values.
        control.iface_value.SetValue(format(value, '.12g'))
        if not math.isclose(float(control.get_value()), value, rel_tol=0, abs_tol=.00051):
            raise ValueError('Fixture field replacement not observed; partial movement possible')
        control.type_keys('{TAB}', set_foreground=False)
        time.sleep(1)
        committed[axis_index] = value
        completed_axes.append(key)
        if snapshot(app, main, process)['dialogs']:
            prepare_project(app, main, process, expected_project)
            item = selected_item[0]
            if list(item.element_info.runtime_id) != runtime or not item.is_selected():
                raise ValueError('Fixture selection changed during movement reminder')
            observed = [float(field_control(field,'after_reminder').get_value()) for field in fields]
            if any(not math.isclose(a,b,rel_tol=0,abs_tol=.00051) for a,b in zip(observed, committed)):
                raise ValueError('Partial movement differs after reminder; inspect before retry')
    after = [float(field_control(key,'final_readback').get_value()) for key in fields]
    if any(not math.isclose(a,b,rel_tol=0,abs_tol=.00051) for a,b in zip(after, parameters['position_m'])):
        raise ValueError('Fixture movement readback differs; partial movement possible')
    return {'operation': 'edit_fixture', 'path': str(expected), 'runtime_id': runtime,
            'coordinate_frame': 'active_storey',
            'before_position_m': before, 'after_position_m': after, 'native_project_saved': False,
            'uses_codex_computer_use': False, 'other_fixtures_verified': False,
            'warning': 'Selected native coordinate fields committed. Independently inspect all fixtures and save/reopen before accepting the layout.'}


def read_arrangement(app, main, process, expected_project, tree_item_id):
    if not isinstance(tree_item_id,str) or tree_item_id.count('_Luminaires_') != 1:
        raise ValueError('Expected an explicit luminaire arrangement tree identity')
    parent = tree_item_id.split('_Luminaires_',1)[0]+'_Luminaires'
    inventory = project_tree(app, main, process, expected_project, parent)
    if inventory['search_text']:
        raise ValueError('Arrangement inspection requires an unfiltered tree')
    tree = wait_control(main,'List','FilterTreeListBox')
    matches = [e for e in container_elements(tree) if e.CurrentAutomationId == tree_item_id]
    if len(matches)!=1:
        raise ValueError('Arrangement identity is absent or ambiguous')
    item = materialize_tree_item(matches[0])
    item.select()
    if not item.is_selected():
        raise ValueError('Arrangement selection not confirmed')
    select_lighting_tool(main,'LuminaireArrangementTool')
    set_storey_context(main)
    allowed = {'ElementCountX','ElementCountY','PolygonPosition_X','PolygonPosition_Y',
               'PolygonPosition_Z','ArrangementRotation_Z','ArrangementObjectName'}
    available = {c.element_info.automation_id for c in main.descendants(control_type='Edit')
                 if c.is_visible() and c.element_info.automation_id in allowed}
    if not available-{'ArrangementObjectName'}:
        raise ValueError('No supported arrangement parameters exposed')
    values = read_edit_values(main,sorted(available))
    if snapshot(app,main,process)['dialogs']:
        raise ValueError('Dialog during arrangement readback')
    return {'operation':'read_arrangement','path':inventory['path'],'tree_item_id':tree_item_id,
            'display_values':values,'coordinate_frame':'active_storey',
            'fixture_positions_verified':False,'uses_codex_computer_use':False}


def edit_arrangement(app, main, process, expected_project, parameters):
    """Edit an exact visible tree item, then read committed native parameters."""
    import math
    allowed = {'ElementCountX', 'ElementCountY', 'PolygonPosition_X', 'PolygonPosition_Y',
               'PolygonPosition_Z', 'ArrangementRotation_Z', 'ArrangementObjectName'}
    if not isinstance(parameters, dict) or set(parameters) != {'tree_item_id', 'values'}:
        raise ValueError('Expected tree_item_id and values')
    identity, values = parameters['tree_item_id'], parameters['values']
    if not isinstance(identity, str) or not identity or not isinstance(values, dict) or not values or not set(values) <= allowed:
        raise ValueError('Invalid arrangement identity or parameter keys')
    for key, value in values.items():
        if key == 'ArrangementObjectName':
            if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}', value) or value != value.strip():
                raise ValueError('Arrangement name must be 1 to 80 plain ASCII letters, digits, spaces, dots, underscores or hyphens')
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError('Arrangement values must be finite numbers')
        if key.startswith('ElementCount') and (value != int(value) or not 1 <= value <= 1000):
            raise ValueError('Element counts must be integers from 1 to 1000')
    expected, state = prepare_project(app, main, process, expected_project)
    select_lighting_tool(main, 'ProjectTreeTool')
    candidate = wait_control(main, 'ListItem', identity)
    if not candidate.is_visible():
        raise ValueError('Target tree item is not visible')
    if 'ArrangementObjectName' in values:
        new_name = values['ArrangementObjectName']
        for other in main.descendants(control_type='ListItem'):
            if other.element_info.runtime_id == candidate.element_info.runtime_id:
                continue
            labels = [c.window_text() for c in other.descendants(control_type='Text')
                      if c.element_info.automation_id == '_textBlock']
            if new_name in labels:
                raise ValueError('Requested name already appears in realized project tree')
    # Existing results must be explicitly cleared before changing geometry;
    # otherwise an edit can display a pending value behind a confirmation dialog.
    if state['controls']['DiscardResultsButton']['enabled']:
        unique_control(main, 'Button', 'DiscardResultsButton').click()
        time.sleep(.4)
        if snapshot(app, main, process)['dialogs']:
            raise ValueError('Dialog after clearing results; no parameter edit attempted')
    unique_control(main, 'TabItem', 'ProjectTreeTool').select()
    item = wait_control(main, 'ListItem', identity)
    if not item.is_visible():
        raise ValueError('Target tree item is collapsed or not visible; expand it before editing')
    item.select()
    select_lighting_tool(main, 'LuminaireArrangementTool')
    set_storey_context(main)
    before = {key: wait_control(main, 'Edit', key).get_value() for key in values}
    name = unique_control(main, 'Edit', 'ArrangementObjectName').get_value()
    for key, value in values.items():
        control = unique_control(main, 'Edit', key)
        if key == 'ArrangementObjectName':
            # This native name field commits on each keystroke; fast input lost
            # characters in the live probe. Focus and pace literal safe text.
            control.click_input()
            control.type_keys('^a', pause=.1)
            control.type_keys(value, pause=.2, with_spaces=True)
            control.type_keys('{TAB}', pause=.1)
        else:
            control.set_focus()
            control.iface_value.SetValue(format(value, '.12g'))
            if not math.isclose(float(control.get_value()),value,rel_tol=0,abs_tol=.00051):
                raise ValueError('Arrangement field replacement not observed; partial edit possible')
            control.type_keys('{TAB}', set_foreground=False)
        time.sleep(1)
        edit_state = snapshot(app, main, process)
        if edit_state['dialogs']:
            raise ValueError('Dialog during edit; pending values are not verified: ' + json.dumps(edit_state['dialogs']))
        actual = unique_control(main, 'Edit', key).get_value()
        if (actual != value if key == 'ArrangementObjectName' else not math.isclose(float(actual), value, rel_tol=0, abs_tol=.00051)):
            raise ValueError(f'Parameter {key} did not commit; partial edit possible, inspect before retry')
    after = {key: unique_control(main, 'Edit', key).get_value() for key in values}
    if any((after[key] != value if key == 'ArrangementObjectName' else not math.isclose(float(after[key]), value, rel_tol=0, abs_tol=.00051)) for key, value in values.items()):
        raise ValueError('Final readback differs; dependent parameter adjustment possible')
    return {'operation': 'edit_arrangement', 'path': str(expected), 'tree_item_id': identity,
            'coordinate_frame': 'active_storey',
            'name': after.get('ArrangementObjectName', name), 'previous_name': name,
            'before': before, 'after': after, 'native_project_saved': False,
            'fixture_positions_verified': False, 'uses_codex_computer_use': False,
            'evidence': 'Committed native arrangement parameters read back; individual fixture coordinates and calculation require separate verification.'}


def export_pdf(app, main, process, expected_project, path):
    import pdfplumber
    target = Path(path).resolve()
    if target.suffix.lower() != '.pdf' or target.exists() or not target.parent.is_dir():
        raise ValueError('PDF export requires a new .pdf path in an existing directory')
    expected, state = prepare_project(app, main, process, expected_project)
    if not state['controls']['DiscardResultsButton']['enabled']:
        raise ValueError('No stored calculation results available for report export')
    unique_control(main, 'MenuItem', 'File').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'PrintPreview').iface_invoke.Invoke()
    menu = wait_control(main, 'Menu', 'MenuSaveAs', timeout=20)
    unique_control(menu, 'MenuItem', '').iface_expand_collapse.Expand()
    wait_control(main, 'MenuItem', 'ExportFormatMenuItem_Pdf').iface_invoke.Invoke()
    deadline = time.monotonic() + 10
    dialog = None
    while time.monotonic() < deadline:
        matches = {c.element_info.runtime_id: c for c in main.descendants(control_type='Window')
                   if c.is_visible() and c.window_text() == 'Adobe PDF File - Export Settings'}
        if len(matches) == 1:
            dialog = next(iter(matches.values()))
            break
        time.sleep(.2)
    if dialog is None:
        raise ValueError('PDF export settings not observed')
    wait_control(dialog, 'Group', 'expander').iface_expand_collapse.Expand()
    wait_control(dialog, 'RadioButton', 'radioButtonAll').select()
    open_after = unique_control(dialog, 'CheckBox', 'checkBoxOpenAfterExport')
    if open_after.get_toggle_state():
        open_after.toggle()
    unique_control(dialog, 'Button', 'buttonOk').click()
    submit_file_dialog(main, 'Adobe PDF File', target)
    deadline = time.monotonic() + 30
    previous, stable = None, 0
    while time.monotonic() < deadline:
        if target.exists():
            stat = target.stat()
            signature = (stat.st_size, stat.st_mtime_ns)
            stable = stable + 1 if signature == previous else 0
            previous = signature
            if stat.st_size and stable >= 3:
                with pdfplumber.open(target) as pdf:
                    pages = len(pdf.pages)
                if pages < 1:
                    raise ValueError('Exported PDF contains no pages')
                return {'operation': 'export_pdf', 'status': 'exported', 'path': str(target),
                        'project': str(expected), 'bytes': stat.st_size, 'pages': pages,
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                        'uses_codex_computer_use': False, 'fresh_calculation_verified': False,
                        'evidence': 'Native PDF export of all currently selected documentation pages; new file stabilized and parsed. Stored results are not proof of a fresh calculation.'}
        time.sleep(.3)
    raise ValueError('PDF export submitted but file not verified; inspect before retry')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'save', 'calculate', 'open', 'launch', 'import-stf', 'save-as', 'import-luminaire', 'arrange-space', 'export-pdf', 'edit-arrangement', 'project-tree', 'group-fixtures', 'edit-fixture', 'close-project', 'read-space', 'room-context', 'arrange-room', 'inspect-group', 'read-furniture', 'apply-grid', 'read-arrangement'])
    parser.add_argument('--parameters')
    parser.add_argument('--product-id')
    parser.add_argument('--runtime-temp')
    parser.add_argument('--expected-project')
    parser.add_argument('--recalculate', action='store_true')
    parser.add_argument('--path')
    parser.add_argument('--save-current', action='store_true')
    args = parser.parse_args()
    try:
        if __package__:
            from .desktop_lock import desktop_lease
        else:
            from desktop_lock import desktop_lease
        with desktop_lease():
            app, window, process = launch(args.path, args.runtime_temp) if args.action == 'launch' else connect()
            if args.action in {'save', 'calculate', 'save-as', 'import-luminaire', 'arrange-space', 'export-pdf', 'edit-arrangement', 'project-tree', 'group-fixtures', 'edit-fixture', 'close-project', 'read-space', 'room-context', 'arrange-room', 'inspect-group', 'read-furniture', 'apply-grid', 'read-arrangement'} and not args.expected_project:
                raise ValueError('expected_project is required')
            if args.action in {'status', 'launch'}:
                result = snapshot(app, window, process)
            elif args.action == 'save':
                result = save(app, window, process, args.expected_project)
            elif args.action == 'room-context':
                result = room_context(app, window, process, args.expected_project, json.loads(args.parameters) if args.parameters else None)
            elif args.action == 'read-space':
                result = read_space(app, window, process, args.expected_project, json.loads(args.parameters))
            elif args.action == 'close-project':
                result = close_project(app, window, process, args.expected_project, args.save_current)
            elif args.action == 'open':
                result = open_project(app, window, process, args.path, args.expected_project, args.save_current)
            elif args.action == 'import-stf':
                result = import_stf(app, window, process, args.path)
            elif args.action == 'save-as':
                result = save_as(app, window, process, args.expected_project, args.path)
            elif args.action == 'import-luminaire':
                result = import_luminaire(app, window, process, args.expected_project, args.path, args.product_id)
            elif args.action == 'arrange-room':
                result = arrange_room(app, window, process, args.expected_project, json.loads(args.parameters))
            elif args.action == 'arrange-space':
                result = arrange_space(app, window, process, args.expected_project, args.product_id)
            elif args.action == 'edit-fixture':
                result = edit_fixture(app, window, process, args.expected_project, json.loads(args.parameters))
            elif args.action == 'apply-grid':
                result = apply_grid(app, window, process, args.expected_project, json.loads(args.parameters))
            elif args.action == 'read-arrangement':
                result = read_arrangement(app, window, process, args.expected_project, **json.loads(args.parameters))
            elif args.action == 'read-furniture':
                result = read_furniture(app, window, process, args.expected_project, **json.loads(args.parameters))
            elif args.action == 'inspect-group':
                result = inspect_group(app, window, process, args.expected_project, json.loads(args.parameters))
            elif args.action == 'group-fixtures':
                result = read_group_fixtures(app, window, process, args.expected_project, **json.loads(args.parameters))
            elif args.action == 'project-tree':
                result = project_tree(app, window, process, args.expected_project, json.loads(args.parameters) if args.parameters else None)
            elif args.action == 'edit-arrangement':
                result = edit_arrangement(app, window, process, args.expected_project, json.loads(args.parameters))
            elif args.action == 'export-pdf':
                result = export_pdf(app, window, process, args.expected_project, args.path)
            else:
                result = calculate(app, window, process, args.expected_project, args.recalculate)
            print(json.dumps(result, ensure_ascii=True))
            return 0
    except Exception as exc:
        print(json.dumps({'error': f'{type(exc).__name__}: {exc}'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
