"""Standalone desktop operations in a bounded, fresh Windows UIA process."""
import json
from pathlib import Path
import subprocess
import sys


def _run(action, expected_project=None, recalculate=False, target=None, save_current=False, product_id=None, runtime_temp=None, parameters=None):
    if sys.platform != 'win32':
        raise ValueError('DIALux desktop control requires Windows')
    command = [sys.executable, str(Path(__file__).with_name('windows_worker.py')), action]
    if expected_project is not None:
        command += ['--expected-project', str(expected_project)]
    if recalculate:
        command.append('--recalculate')
    if target is not None:
        command += ['--path', str(target)]
    if save_current:
        command.append('--save-current')
    if product_id is not None:
        command += ['--product-id', product_id]
    if runtime_temp is not None:
        command += ['--runtime-temp', str(runtime_temp)]
    if parameters is not None:
        command += ['--parameters', json.dumps(parameters, allow_nan=False)]
    try:
        run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                             timeout=660 if action == 'launch' else 7200 if action in {'apply-grid','apply-array'} else 3600 if action == 'inspect-group' else 120 if action == 'arrange-room' else 75 if action in {'edit-fixture', 'group-fixtures', 'edit-arrangement', 'calculate', 'open', 'import-stf', 'save-as', 'import-luminaire', 'export-pdf'} else 30)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Desktop operation timed out; outcome unknown. Inspect status before any retry.') from exc
    try:
        result = json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError('Desktop worker returned no valid result; outcome unknown') from exc
    if run.returncode:
        raise ValueError(result.get('error', 'Desktop operation failed'))
    return result


def desktop_status() -> dict:
    """Read the unique running DIALux process and current controls using Windows UIA."""
    return _run('status')


def desktop_project_tree(expected_project: str, expand_id: str | None = None) -> dict:
    """Read realized native tree nodes; optionally expand one exact visible node."""
    # The worker shares the JSON argument transport with edit operations.
    return _run('project-tree', expected_project, parameters=expand_id)


def desktop_edit_arrangement(expected_project: str, tree_item_id: str, values: dict) -> dict:
    """Edit an exact visible native arrangement's name, counts, centre XYZ or Z rotation.

    Tree item must already be expanded. Clears cached results before editing.
    ArrangementObjectName accepts 1–80 plain ASCII letters/digits/spaces/._-.
    Renaming changes the tree ID; obtain a fresh tree afterward.
    Does not save or verify individual fixtures.
    Failure may leave a partial edit; inspect before retrying.
    """
    return _run('edit-arrangement', expected_project, parameters={'tree_item_id': tree_item_id, 'values': values})


def desktop_import_luminaire(expected_project: str, path: str, product_id: str) -> dict:
    """Import local photometry and read back the expected active product; does not place luminaires."""
    if not isinstance(product_id, str) or not product_id.strip():
        raise ValueError('product_id must be a nonempty string')
    return _run('import-luminaire', expected_project, target=path, product_id=product_id)


def desktop_arrange_space(expected_project: str, product_id: str) -> dict:
    """Use native automatic placement in the current space of a single-room fixture.

    Requires the expected active luminaire and refuses calculation-ready content
    to reduce duplicate placement. Does not save or guarantee a lighting target.
    """
    if not isinstance(product_id, str) or not product_id.strip():
        raise ValueError('product_id must be a nonempty string')
    return _run('arrange-space', expected_project, product_id=product_id)


def desktop_launch(executable: str = 'C:/Program Files/DIAL GmbH/DIALux/DIALux_x64.exe', runtime_temp: str | None = None) -> dict:
    """Launch with a process-local ASCII temp directory (default checkout/local/tmp).

    Reusing an existing process cannot change its inherited TEMP/TMP.
    """
    return _run('launch', target=executable, runtime_temp=runtime_temp)


def desktop_import_stf(path: str) -> dict:
    """Import a parsed STF into an empty DIALux workspace. Native project is not yet saved."""
    return _run('import-stf', target=path)


def desktop_save_as(expected_project: str, path: str) -> dict:
    """Save an imported or existing project to a new native .evo path; never accept overwrite prompts."""
    return _run('save-as', expected_project, target=path)


def desktop_read_arrangement(expected_project: str, tree_item_id: str) -> dict:
    """Read exposed native array parameters without changing geometry or results."""
    return _run('read-arrangement', expected_project, parameters={'tree_item_id':tree_item_id})


def desktop_save(expected_project: str) -> dict:
    """Save only the specified currently open native project; reject dialogs and mismatches."""
    return _run('save', expected_project)


def desktop_calculate(expected_project: str, recalculate: bool = False) -> dict:
    """Invoke real DIALux calculation. Optional recalculate discards cached results first.

    Does not save the native project. Returns observed result controls, not a
    compliance judgment. Large calculations may exceed the bounded worker time.
    """
    if not isinstance(recalculate, bool):
        raise ValueError('recalculate must be a boolean')
    return _run('calculate', expected_project, recalculate)


def desktop_open(path: str, expected_current_project: str | None = None, save_current: bool = False) -> dict:
    """Open a native project, preserving modified current work unless saving is explicitly requested."""
    if not isinstance(save_current, bool):
        raise ValueError('save_current must be a boolean')
    return _run('open', expected_current_project, target=path, save_current=save_current)


def desktop_export_pdf(expected_project: str, path: str) -> dict:
    """Export selected documentation to a new PDF using stored results, without recalculation."""
    return _run('export-pdf', expected_project, target=path)


def desktop_group_fixtures(expected_project: str, group_id: str, offset: int = 0, limit: int = 4, inventory_token: str | None = None, expected_count: int | None = None) -> dict:
    """Read individual position/rotation fields through the native item container.

    Returns at most four fixtures per call. Follow next_offset with inventory_token.
    The token guards node identity/order, not unchanged geometry between calls.
    Optional expected_count refuses a count mismatch before reading. Virtualized rows
    are realized and scrolled into view using native UIA patterns.
    Does not claim a complete inventory; runtime IDs are valid only in this session.
    """
    return _run('group-fixtures', expected_project, parameters={'group_id': group_id, 'offset': offset,
                'limit': limit, 'inventory_token': inventory_token, 'expected_count': expected_count})


def desktop_edit_fixture(expected_project: str, runtime_id: list[int], expected_position_m: list[float], position_m: list[float]) -> dict:
    """Move one inspected native fixture. Requires current session ID and prior XYZ.

    Clears cached results. Failure may leave partial movement; inspect before retry.
    Does not save, verify other fixtures, or guarantee boundary containment.
    """
    return _run('edit-fixture', expected_project, parameters={'runtime_id': runtime_id,
                'expected_position_m': expected_position_m, 'position_m': position_m})


def desktop_close_project(expected_project: str, save_current: bool = False) -> dict:
    """Close only the expected project, refusing unsaved changes unless saving is requested."""
    if not isinstance(save_current, bool):
        raise ValueError('save_current must be a boolean')
    return _run('close-project', expected_project, save_current=save_current)


def desktop_read_space(expected_project: str, tree_item_id: str) -> dict:
    """Read native space height, workplane and maintenance displays for an exact visible node."""
    if not isinstance(tree_item_id, str) or not tree_item_id:
        raise ValueError('Explicit space tree_item_id is required')
    return _run('read-space', expected_project, parameters=tree_item_id)


def desktop_room_context(expected_project: str, room_name: str | None = None) -> dict:
    """List room context labels or invoke an exact unique label; active context remains unverified."""
    return _run('room-context', expected_project, parameters=room_name)


def desktop_arrange_room(expected_project: str, room_name: str, group_name: str,
                         product_id: str, parent_id: str, expected_groups: list[str],
                         evidence_directory: str) -> dict:
    """Create one named group in a selected room, with durable intent before mutation.

    Existing realized group IDs must match expected_groups. Requires a new evidence
    directory; never automatically retries. Result is created_unverified: inspect
    new and existing fixture geometry separately, then save/calculate. Native room
    menu selection alone does not prove spatial scope. Does not import photometry.
    """
    return _run('arrange-room', expected_project, parameters={
        'room_name':room_name, 'group_name':group_name, 'product_id':product_id,
        'parent_id':parent_id, 'expected_groups':expected_groups,
        'evidence_directory':evidence_directory})


def desktop_read_furniture(expected_project: str, tree_item_id: str) -> dict:
    """Read exact native furniture identity, reference position and dimensions."""
    return _run('read-furniture', expected_project, parameters={'tree_item_id':tree_item_id})


def apply_array_transform(expected_project: str, spec: dict, group_id: str, evidence_directory: str) -> dict:
    """Journal a rigid array transform with full before/after group inspection.

    Leaves the verified geometry unsaved; calculation and persistence are separate.
    Failure may leave partial edits. Inspect evidence and live state; never retry blindly.
    """
    return _run('apply-array', expected_project, parameters={'spec':spec,'group_id':group_id,'evidence_directory':evidence_directory})
