from types import SimpleNamespace
import sys

from src.windows_worker import desktop_state


def install_fakes(monkeypatch, processes, main_exists=False):
    monkeypatch.setitem(sys.modules, 'psutil', SimpleNamespace(
        process_iter=lambda fields: [SimpleNamespace(info=p) for p in processes]))
    monkeypatch.setitem(sys.modules, 'win32gui', SimpleNamespace(EnumWindows=lambda callback, arg: None))
    monkeypatch.setitem(sys.modules, 'win32process', SimpleNamespace())
    main = SimpleNamespace(exists=lambda timeout: main_exists, wrapper_object=lambda: 'main')
    app = SimpleNamespace(connect=lambda **kwargs: app, window=lambda **kwargs: main)
    monkeypatch.setitem(sys.modules, 'pywinauto', SimpleNamespace(Application=lambda **kwargs: app))


def test_no_process_is_reported_without_error(monkeypatch):
    install_fakes(monkeypatch, [])
    assert desktop_state()['state'] == 'not_running'


def test_multiple_processes_are_reported_without_selecting_one(monkeypatch):
    install_fakes(monkeypatch, [dict(pid=n, name='DIALux_x64.exe', exe='dialux') for n in (1,2)])
    assert desktop_state()['state'] == 'multiple_processes'


def test_splash_is_reported_as_starting(monkeypatch):
    install_fakes(monkeypatch, [dict(pid=1, name='DIALux_x64.exe', exe='dialux')])
    assert desktop_state()['state'] == 'starting'


def test_modal_is_reported_as_blocked(monkeypatch):
    install_fakes(monkeypatch, [dict(pid=1, name='DIALux_x64.exe', exe='dialux')], True)
    monkeypatch.setattr('src.windows_worker.snapshot', lambda *args: {'dialogs': [{'title': 'Confirm'}]})
    assert desktop_state()['state'] == 'blocked'


def test_nonblocking_launch_does_not_wait_for_idle_or_main_window(tmp_path, monkeypatch):
    from src import windows_worker
    executable = tmp_path/'DIALux_x64.exe'
    executable.write_bytes(b'synthetic executable')
    install_fakes(monkeypatch, [])
    calls = []
    def start(command, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(window=lambda **kwargs: (_ for _ in ()).throw(AssertionError('Unexpected window wait')))
    monkeypatch.setitem(sys.modules, 'pywinauto', SimpleNamespace(
        Application=lambda **kwargs: SimpleNamespace(start=start)))
    monkeypatch.setattr(windows_worker, 'desktop_state', lambda: {'state':'starting'})
    import tempfile
    with tempfile.TemporaryDirectory(prefix='dx-') as scratch:
        result = windows_worker.launch(executable, scratch, wait_for_ready=False)
    assert result['state'] == 'starting'
    assert calls == [{'timeout':20, 'wait_for_idle':False}]
