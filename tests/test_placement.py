import copy
import json
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import placement


def test_group_collection_consumes_all_identity_checked_pages(monkeypatch):
    first = {'fixtures':[{'id':1}], 'observed_count':1, 'realized_node_count':2,
             'next_offset':1, 'inventory_token':'same', 'offset':0}
    second = {**first, 'fixtures':[{'id':2}], 'next_offset':None, 'offset':1}
    def read(project, group, **kwargs):
        if not kwargs: return first
        assert kwargs == {'offset':1, 'inventory_token':'same'}
        return second
    monkeypatch.setattr(placement, 'desktop_group_fixtures', read)
    result = placement.read_realized_group('test.evo','group')
    assert result['observed_count'] == 2
    assert [f['id'] for f in result['fixtures']] == [1,2]
    assert result['next_offset'] is None


def setup_run(tmp_path, monkeypatch):
    spec = json.loads((Path(__file__).resolve().parents[1] / 'examples/synthetic-apply-grid.json').read_text())
    plan = placement.plan_grid(spec)
    after = {'operation':'read_group_fixtures', 'coordinate_frame':'active_storey', 'observed_count':4, 'fixtures':[
        {'runtime_id':[7,1,i], 'position_m':f['position_m'], 'rotation_deg':[0,0,0]}
        for i,f in enumerate(plan['fixtures'])]}
    before = copy.deepcopy(after)
    for fixture in before['fixtures']: fixture['position_m'][0] += .2
    observations = iter([before, after])
    monkeypatch.setattr(placement, 'desktop_group_fixtures', lambda *a: next(observations))
    project = tmp_path / 'test.evo'; project.write_bytes(b'native fixture placeholder')
    directory = tmp_path / 'run'
    return spec, project, directory, before


def test_journal_intent_precedes_each_mutation_and_verifies_all(tmp_path, monkeypatch):
    spec, project, directory, _ = setup_run(tmp_path, monkeypatch)
    calls = []
    def edit(*args):
        journal = json.loads((directory/'journal.json').read_text())
        assert journal['steps'][-1]['state'] == 'pending'
        assert len(journal['steps']) == len(calls)+1
        calls.append(args)
        return {'after_position_m': args[-1]}
    monkeypatch.setattr(placement, 'desktop_edit_fixture', edit)
    result = placement._apply_grid_layout(spec, str(project), 'group', str(directory))
    assert result['state'] == 'verified' and len(calls) == 4
    assert calls[0][-1] == pytest.approx([1.5, 1.0, 3.035])
    assert not result['whole_project_verified']
    journal = json.loads((directory/'journal.json').read_text())
    assert all(s['state'] == 'committed' for s in journal['steps'])


@pytest.mark.parametrize('change_after', [False, True])
def test_already_matching_positions_skip_writes_but_require_final_read(tmp_path,monkeypatch,change_after):
    spec, project, directory, before = setup_run(tmp_path,monkeypatch)
    for fixture in before['fixtures']: fixture['position_m'][0] -= .2
    after = copy.deepcopy(before)
    if change_after: after['fixtures'][0]['position_m'][0] += .1
    observed = iter([before,after])
    reads = []
    def read(*args):
        reads.append(True)
        return next(observed)
    monkeypatch.setattr(placement,'desktop_group_fixtures',read)
    monkeypatch.setattr(placement,'desktop_edit_fixture',lambda *a:pytest.fail('Unnecessary native write'))
    if change_after:
        with pytest.raises(ValueError):
            placement._apply_grid_layout(spec,str(project),'group',str(directory))
    else:
        assert placement._apply_grid_layout(spec,str(project),'group',str(directory))['state']=='verified'
    assert len(reads)==2
    journal=json.loads((directory/'journal.json').read_text())
    assert all(s['state']=='no_write_required' for s in journal['steps'])


def test_partial_failure_is_preserved_without_retry_or_rollback(tmp_path, monkeypatch):
    spec, project, directory, _ = setup_run(tmp_path, monkeypatch)
    calls = []
    def edit(*args):
        calls.append(args)
        if len(calls) == 2: raise ValueError('native dialog')
        return {'ok':True}
    monkeypatch.setattr(placement, 'desktop_edit_fixture', edit)
    with pytest.raises(ValueError, match='native dialog'):
        placement._apply_grid_layout(spec, str(project), 'group', str(directory))
    journal = json.loads((directory/'journal.json').read_text())
    assert journal['state'] == 'failed'
    assert [s['state'] for s in journal['steps']] == ['committed','pending']
    assert len(calls) == 2
    with pytest.raises(FileExistsError):
        placement._apply_grid_layout(spec, str(project), 'group', str(directory))


def test_count_mismatch_stops_before_mutation(tmp_path, monkeypatch):
    spec, project, directory, before = setup_run(tmp_path, monkeypatch)
    before['fixtures'].pop()
    monkeypatch.setattr(placement, 'desktop_group_fixtures', lambda *a: before)
    monkeypatch.setattr(placement, 'desktop_edit_fixture', lambda *a: pytest.fail('Mutation attempted'))
    with pytest.raises(ValueError, match='count'):
        placement._apply_grid_layout(spec, str(project), 'group', str(directory))


def test_successful_field_edits_do_not_override_wrong_final_geometry(tmp_path, monkeypatch):
    spec, project, directory, before = setup_run(tmp_path, monkeypatch)
    monkeypatch.setattr(placement, 'desktop_group_fixtures', lambda *a: copy.deepcopy(before))
    monkeypatch.setattr(placement, 'desktop_edit_fixture', lambda *a: {'ok':True})
    with pytest.raises(ValueError, match='Unmatched'):
        placement._apply_grid_layout(spec, str(project), 'group', str(directory))
    journal = json.loads((directory/'journal.json').read_text())
    assert journal['state'] == 'failed'
    assert len(journal['steps']) == 4
    assert all(s['state'] == 'committed' for s in journal['steps'])
    assert 'verification' not in journal


def test_public_apply_uses_one_worker(monkeypatch):
    import desktop
    calls=[]
    monkeypatch.setattr(desktop,'_run',lambda *a,**k:calls.append((a,k)) or {'state':'verified'})
    assert placement.apply_grid_layout({'test':1},'x.evo','group','evidence')['state']=='verified'
    assert calls==[(('apply-grid','x.evo'),{'parameters':{'spec':{'test':1},'group_id':'group','evidence_directory':'evidence'}})]


def test_native_read_pages_are_persisted_before_first_move(tmp_path,monkeypatch):
    spec,project,directory,_=setup_run(tmp_path,monkeypatch)
    def edit(*args):
        journal=json.loads((directory/'journal.json').read_text())
        assert journal['inspection_pages'][0]['phase']=='before'
        assert (directory/'before-page-0000.json').exists()
        assert journal['steps'][-1]['started_utc']
        return {}
    result=placement._apply_grid_layout(spec,str(project),'group',str(directory),fixture_editor=edit)
    journal=json.loads(Path(result['journal']).read_text())
    assert [p['phase'] for p in journal['inspection_pages']]==['before','after']
    assert all(s['finished_utc'] for s in journal['steps'])
    assert journal['finished_utc']>=journal['started_utc']
