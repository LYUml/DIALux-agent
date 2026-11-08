import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import desktop


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
