"""Windows-only worker. No Codex, sky client, coordinate clicks or remote server."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


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


def snapshot(app, main, process):
    controls = {}
    for control_id in ('Save', 'CalculationButtonStart', 'DiscardResultsButton'):
        matches = [c for c in main.descendants(control_type='Button') if c.element_info.automation_id == control_id]
        controls[control_id] = {'count': len(matches), 'enabled': len(matches) == 1 and matches[0].is_enabled()}
    dialogs = []
    for window in app.windows():
        if window.handle != main.handle and window.is_visible():
            dialogs.append({'title': window.window_text(), 'automation_id': window.element_info.automation_id})
    for window in main.descendants(control_type='Window'):
        if window.is_visible():
            button_ids = {c.element_info.automation_id for c in window.descendants(control_type='Button')}
            # Observed non-modal energy overlay; no other secondary UI is allowed.
            if not window.window_text() and button_ids == {
                'CloseEnergyTachometerButton', 'ShowEnergyTachometerMenuButton',
                'EnergyTachometerChangeToEnergyPerformanceToolButton'}:
                continue
            dialogs.append({'title': window.window_text(), 'automation_id': window.element_info.automation_id})
    return {'backend': 'pywinauto-uia', 'pid': process['pid'], 'executable': process['exe'],
            'title': main.window_text(), 'controls': controls, 'dialogs': dialogs,
            'uses_codex_computer_use': False}


def prepare_project(app, main, process, expected_project):
    expected = Path(expected_project).resolve(strict=True)
    if expected.suffix.lower() != '.evo':
        raise ValueError('Expected an existing native .evo project')
    state = snapshot(app, main, process)
    if state['dialogs']:
        raise ValueError('A DIALux secondary window/dialog is open; inspect before acting')
    prefix, separator, version = state['title'].rpartition(' - DIALux evo ')
    if not separator or Path(prefix.rstrip('* ')).resolve() != expected:
        raise ValueError('Active project does not match expected_project')
    # WPF commands can report disabled while DIALux is inactive. Activation is
    # explicit and affects foreground focus, though Invoke does not move the mouse.
    main.set_focus()
    time.sleep(.3)
    state = snapshot(app, main, process)
    if state['dialogs']:
        raise ValueError('A dialog appeared after activation; operation was not invoked')
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
    expected, state = prepare_project(app, main, process, expected_project)
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'save', 'calculate', 'open'])
    parser.add_argument('--expected-project')
    parser.add_argument('--recalculate', action='store_true')
    parser.add_argument('--path')
    parser.add_argument('--save-current', action='store_true')
    args = parser.parse_args()
    try:
        app, window, process = connect()
        if args.action in {'save', 'calculate'} and not args.expected_project:
            raise ValueError('expected_project is required')
        if args.action == 'status':
            result = snapshot(app, window, process)
        elif args.action == 'save':
            result = save(app, window, process, args.expected_project)
        elif args.action == 'open':
            result = open_project(app, window, process, args.path, args.expected_project, args.save_current)
        else:
            result = calculate(app, window, process, args.expected_project, args.recalculate)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except Exception as exc:
        print(json.dumps({'error': f'{type(exc).__name__}: {exc}'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
