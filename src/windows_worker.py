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
            children = window.children()
            # Arrangement selection exposes dimension labels as native popups.
            # Only an exact, noninteractive one-text metric label is exempt.
            if (window.class_name() == 'Popup' and not window.window_text()
                    and len(children) == 1 and children[0].element_info.control_type == 'Text'
                    and re.fullmatch(r'-?\d+(?:\.\d+)? m', children[0].window_text())
                    and not children[0].children()):
                continue
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


def prepare_project(app, main, process, expected_project, must_exist=True):
    expected = Path(expected_project).resolve(strict=must_exist)
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
    import psutil
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
                'path': str(expected), 'arrangement': values,
                'native_project_saved': False, 'uses_codex_computer_use': False,
                'evidence': 'Native automatic arrangement invoked in current space; selected arrangement parameters read back. No illuminance target guarantee.'}
    raise ValueError('Arrangement was invoked but readback failed; inspect before retry')


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
    parser.add_argument('action', choices=['status', 'save', 'calculate', 'open', 'launch', 'import-stf', 'save-as', 'import-luminaire', 'arrange-space', 'export-pdf'])
    parser.add_argument('--product-id')
    parser.add_argument('--runtime-temp')
    parser.add_argument('--expected-project')
    parser.add_argument('--recalculate', action='store_true')
    parser.add_argument('--path')
    parser.add_argument('--save-current', action='store_true')
    args = parser.parse_args()
    try:
        app, window, process = launch(args.path, args.runtime_temp) if args.action == 'launch' else connect()
        if args.action in {'save', 'calculate', 'save-as', 'import-luminaire', 'arrange-space', 'export-pdf'} and not args.expected_project:
            raise ValueError('expected_project is required')
        if args.action in {'status', 'launch'}:
            result = snapshot(app, window, process)
        elif args.action == 'save':
            result = save(app, window, process, args.expected_project)
        elif args.action == 'open':
            result = open_project(app, window, process, args.path, args.expected_project, args.save_current)
        elif args.action == 'import-stf':
            result = import_stf(app, window, process, args.path)
        elif args.action == 'save-as':
            result = save_as(app, window, process, args.expected_project, args.path)
        elif args.action == 'import-luminaire':
            result = import_luminaire(app, window, process, args.expected_project, args.path, args.product_id)
        elif args.action == 'arrange-space':
            result = arrange_space(app, window, process, args.expected_project, args.product_id)
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
