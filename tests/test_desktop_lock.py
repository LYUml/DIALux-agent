"""Real Windows kernel mutex regression without touching the GUI."""
import subprocess
import sys
import uuid
import pytest
from src.desktop_lock import desktop_lease

pytestmark=pytest.mark.skipif(sys.platform!='win32',reason='Windows kernel mutex')


def test_other_process_is_refused_and_release_allows_next_owner():
    name='Local\\DIALuxAgent.Test.'+uuid.uuid4().hex
    code="from src.desktop_lock import desktop_lease; import sys\nwith desktop_lease(sys.argv[1]):\n print('owned',flush=True)\n input()\n"
    child=subprocess.Popen([sys.executable,'-c',code,name],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert child.stdout.readline().strip()=='owned'
        assert child.poll() is None
        with pytest.raises(ValueError,match='desktop busy'):
            with desktop_lease(name): pytest.fail('Overlapping owner admitted')
        child.communicate('\n',timeout=10)
        assert child.returncode==0
        with desktop_lease(name): pass
    finally:
        if child.poll() is None: child.kill();child.communicate(timeout=10)


def test_exception_releases_ownership():
    name='Local\\DIALuxAgent.Test.'+uuid.uuid4().hex
    with pytest.raises(RuntimeError):
        with desktop_lease(name): raise RuntimeError('operation failed')
    code="from src.desktop_lock import desktop_lease; import sys\nwith desktop_lease(sys.argv[1]): print('acquired')\n"
    result=subprocess.run([sys.executable,'-c',code,name],capture_output=True,text=True,timeout=10)
    assert result.returncode==0 and result.stdout.strip()=='acquired'

def test_worker_refuses_busy_lease_before_connecting(monkeypatch,capsys):
    from contextlib import contextmanager
    from src import windows_worker,desktop_lock
    @contextmanager
    def busy():
        raise ValueError('DIALux desktop busy')
        yield
    monkeypatch.setattr(desktop_lock,'desktop_lease',busy)
    monkeypatch.setattr(windows_worker,'connect',lambda:pytest.fail('Connected despite busy desktop'))
    monkeypatch.setattr(sys,'argv',['worker','status'])
    assert windows_worker.main()==2
    assert 'desktop busy' in capsys.readouterr().out
