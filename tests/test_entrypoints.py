"""Exercise actual entrypoints so test sys.path changes cannot hide import errors."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('entry', [['src/dialux_agent.py'], ['-m', 'src.dialux_agent']])
@pytest.mark.parametrize('command', ['report-read', 'stf-inspect'])
def test_entrypoints_return_json_for_missing_input(entry, command, tmp_path):
    run = subprocess.run([sys.executable, *entry, command, '--path', str(tmp_path/'absent.pdf')],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 2, run.stderr
    assert json.loads(run.stdout)['ok'] is False
    assert not run.stderr


def test_package_server_import():
    run = subprocess.run([sys.executable, '-c', 'import src.server'], cwd=ROOT,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
