"""Standalone desktop operations in a bounded, fresh Windows UIA process."""
import json
from pathlib import Path
import subprocess
import sys


def _run(action, expected_project=None):
    if sys.platform != 'win32':
        raise ValueError('DIALux desktop control requires Windows')
    command = [sys.executable, str(Path(__file__).with_name('windows_worker.py')), action]
    if expected_project is not None:
        command += ['--expected-project', str(expected_project)]
    try:
        run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', timeout=30)
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


def desktop_save(expected_project: str) -> dict:
    """Save only the specified currently open native project; reject dialogs and mismatches."""
    return _run('save', expected_project)
