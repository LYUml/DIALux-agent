import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
import desktop
import windows_worker


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
