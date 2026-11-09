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
                             timeout=75 if action in {'group-fixtures', 'edit-arrangement', 'calculate', 'open', 'launch', 'import-stf', 'save-as', 'import-luminaire', 'export-pdf'} else 30)
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
    """Edit an exact visible native arrangement's counts, centre XYZ or Z rotation.

    Tree item must already be expanded. Clears cached results before editing.
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


def desktop_group_fixtures(expected_project: str, group_id: str) -> dict:
    """Read individual position/rotation fields from realized children of an exact group.

    Does not claim a complete inventory; runtime IDs are valid only in this session.
    """
    return _run('group-fixtures', expected_project, parameters=group_id)
