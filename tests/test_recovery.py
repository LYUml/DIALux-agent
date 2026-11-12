import hashlib
import json
from pathlib import Path

import pytest
from src.recovery import recover_saved_project


def prepare(tmp_path, monkeypatch):
    source = tmp_path/'saved.evo'
    source.write_bytes(b'saved checkpoint')
    monkeypatch.setattr('src.recovery.evaluate_profile', lambda *args: {})
    monkeypatch.setattr('src.recovery.desktop_open', lambda *args, **kw: {'status': 'opened'})
    monkeypatch.setattr('src.recovery.calculation_checkpoint', lambda *args, **kw: {'state': 'completed'})
    return dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                output_directory=str(tmp_path/'recovery'),checks=[{'summary_id':'room','profile':{}}])


def test_saved_source_preserved_and_output_is_exclusive(tmp_path, monkeypatch):
    args = prepare(tmp_path, monkeypatch)
    result = recover_saved_project(**args)
    assert result['source_unchanged'] and result['state'] == 'completed'
    assert Path(result['project']).read_bytes() == b'saved checkpoint'
    with pytest.raises(FileExistsError): recover_saved_project(**args)


def test_stale_source_rejected_before_output_creation(tmp_path, monkeypatch):
    args = prepare(tmp_path, monkeypatch)
    args['source_sha256'] = '0'*64
    with pytest.raises(ValueError, match='hash'): recover_saved_project(**args)
    assert not Path(args['output_directory']).exists()


def test_failed_open_is_retained_and_never_calculated(tmp_path, monkeypatch):
    args = prepare(tmp_path, monkeypatch)
    def fail(*args, **kw): raise ValueError('Unsaved work')
    monkeypatch.setattr('src.recovery.desktop_open', fail)
    monkeypatch.setattr('src.recovery.calculation_checkpoint', lambda *args, **kw: pytest.fail('Unexpected calculation'))
    with pytest.raises(ValueError, match='Unsaved work'): recover_saved_project(**args)
    journal = json.loads((Path(args['output_directory'])/'journal.json').read_text())
    assert journal['state'] == 'failed' and journal['failed_at'] == 'opening_copy'


def test_partial_calculation_is_preserved(tmp_path, monkeypatch):
    args = prepare(tmp_path, monkeypatch)
    def fail(*args, **kw): raise ValueError('Native calculation interrupted')
    monkeypatch.setattr('src.recovery.calculation_checkpoint', fail)
    with pytest.raises(ValueError): recover_saved_project(**args)
    journal = json.loads((Path(args['output_directory'])/'journal.json').read_text())
    assert journal['failed_at'] == 'recalculating' and Path(journal['project']).exists()
