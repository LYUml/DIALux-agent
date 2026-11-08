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


def save(app, main, process, expected_project):
    expected = Path(expected_project).resolve(strict=True)
    if expected.suffix.lower() != '.evo':
        raise ValueError('Expected an existing native .evo project')
    state = snapshot(app, main, process)
    if state['dialogs']:
        raise ValueError('A DIALux secondary window/dialog is open; inspect before saving')
    prefix, separator, version = state['title'].rpartition(' - DIALux evo ')
    if not separator or Path(prefix.rstrip('* ')).resolve() != expected:
        raise ValueError('Active project does not match expected_project')
    # WPF commands can report disabled while DIALux is inactive. Activation is
    # explicit and affects foreground focus, though Invoke does not move the mouse.
    main.set_focus()
    time.sleep(.3)
    state = snapshot(app, main, process)
    if state['dialogs']:
        raise ValueError('A dialog appeared after activation; save was not invoked')
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['status', 'save'])
    parser.add_argument('--expected-project')
    args = parser.parse_args()
    try:
        app, window, process = connect()
        if args.action == 'save' and not args.expected_project:
            raise ValueError('expected_project is required for saving')
        result = snapshot(app, window, process) if args.action == 'status' else save(app, window, process, args.expected_project)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    except Exception as exc:
        print(json.dumps({'error': f'{type(exc).__name__}: {exc}'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
