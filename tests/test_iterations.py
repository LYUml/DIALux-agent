import copy
import json
from pathlib import Path

import pytest
from src import iterations as module


@pytest.fixture
def harness(tmp_path, monkeypatch):
    project = tmp_path/'source.evo'
    project.write_bytes(b'original')
    spec = json.loads((Path(__file__).parents[1]/'resources/examples/synthetic-grid-layout.json').read_text())
    request = dict(expected_project=str(project), group_id='group', candidates=[copy.deepcopy(spec) for _ in range(4)],
                   checks=[{'summary_id':'room', 'profile':{}}],
                   objective={'summary_id':'room','metric':'uniformity_u0','unit':'1','calculation_surface':'WP1','direction':'maximize'},
                   policy={'max_iterations':4,'no_improvement_limit':2,'minimum_improvement':.01,'stop_on_pass':False},
                   evidence_directory=str(tmp_path/'evidence'))
    values, statuses, actions = [.5,.6,.6,.6], ['fail']*4, []
    monkeypatch.setattr(module,'evaluate_profile',lambda *a: {})
    def save_as(current, target):
        actions.append('copy')
        Path(target).write_bytes(Path(current).read_bytes())
        return {'path':target}
    monkeypatch.setattr(module,'desktop_save_as',save_as)
    def layout(*args):
        actions.append('layout')
        return {'state':'verified'}
    monkeypatch.setattr(module,'apply_grid_layout',layout)
    def checkpoint(*args, **kwargs):
        index = actions.count('calculate')
        actions.append('calculate')
        return {'state':'completed','status':statuses[index],'report':str(index),'report_sha256':str(index)}
    monkeypatch.setattr(module,'calculation_checkpoint',checkpoint)
    monkeypatch.setattr(module,'read_report_pdf',lambda path:{'sha256':path,'summaries':[
        {'summary_id':'room','measurements':[{'metric':'uniformity_u0','unit':'1','calculation_surface':'WP1','value':values[int(path)]}]}]})
    return request, values, statuses, actions


def test_no_improvement_preserves_all_experiments_and_source(harness):
    request, values, statuses, actions = harness
    result = module.run_layout_candidates(**request)
    assert result['stop_reason'] == 'no_improvement'
    assert result['best_candidate'] == 1
    assert result['best_feasible_candidate'] is None
    assert actions == ['copy','layout','calculate']*4
    assert Path(request['expected_project']).read_bytes() == b'original'
    assert not result['winner_installed']
    assert result['group_id'] == request['group_id']


@pytest.mark.parametrize('status,reason', [('pass','selected_conditions_met'),('unverified','evidence_incomplete')])
def test_stop_before_another_candidate(harness,status,reason):
    request, values, statuses, actions = harness
    statuses[0] = status
    request['policy']['stop_on_pass'] = True
    result = module.run_layout_candidates(**request)
    assert result['stop_reason'] == reason
    assert len(result['iterations']) == 1


def test_budget_and_minimizing_objective(harness):
    request, values, statuses, actions = harness
    request['objective']['direction'] = 'minimize'
    request['policy']['max_iterations'] = 2
    statuses[0] = 'pass'
    result = module.run_layout_candidates(**request)
    assert result['stop_reason'] == 'iteration_budget'
    assert result['best_candidate'] == result['best_feasible_candidate'] == 0


def test_small_improvement_still_ranks_actual_best(harness):
    request, values, statuses, actions = harness
    values[:] = [.5, .505, .506, .7]
    statuses[:] = ['pass']*4
    result = module.run_layout_candidates(**request)
    assert result['stop_reason'] == 'no_improvement'
    assert len(result['iterations']) == 3
    assert result['best_candidate'] == result['best_feasible_candidate'] == 2


def test_changed_room_rejected_before_native_work(harness):
    request, values, statuses, actions = harness
    request['candidates'][1]['fixture']['product_id'] = 'different'
    with pytest.raises(ValueError, match='only grid'):
        module.run_layout_candidates(**request)
    assert not actions


def test_missing_objective_keeps_failed_journal_and_never_retries(harness,monkeypatch):
    request, values, statuses, actions = harness
    monkeypatch.setattr(module,'read_report_pdf',lambda path:{'sha256':path,'summaries':[]})
    with pytest.raises(ValueError, match='measurement missing'):
        module.run_layout_candidates(**request)
    journal = json.loads((Path(request['evidence_directory'])/'journal.json').read_text())
    assert journal['state'] == 'failed'
    assert actions == ['copy','layout','calculate']
    assert journal['failed_at'] == 'pending_report_comparison'
    assert journal['active_project'] is None


@pytest.mark.parametrize('stage,expected,action_count', [
    ('copy','pending_copy',0), ('layout','pending_layout',1),
    ('calculate','pending_calculation',2), ('hash','pending_report_comparison',3)])
def test_failure_stops_before_next_candidate_and_records_stage(harness,monkeypatch,stage,expected,action_count):
    request, values, statuses, actions = harness
    def fail(*args, **kwargs):
        raise ValueError('Injected native failure')
    if stage == 'copy': monkeypatch.setattr(module,'desktop_save_as',fail)
    if stage == 'layout': monkeypatch.setattr(module,'apply_grid_layout',lambda *a:{'state':'failed'})
    if stage == 'calculate': monkeypatch.setattr(module,'calculation_checkpoint',lambda *a,**k:{'state':'failed'})
    if stage == 'hash': monkeypatch.setattr(module,'read_report_pdf',lambda *a:{'sha256':'replaced'})
    with pytest.raises(ValueError, match='Candidate run failed'):
        module.run_layout_candidates(**request)
    journal = json.loads((Path(request['evidence_directory'])/'journal.json').read_text())
    assert len(journal['iterations']) == 1
    assert len(actions) == action_count
    assert journal['failed_at'] == expected
    assert journal['active_project'] is None
    assert not journal['native_outcome_verified']


def test_source_modification_prevents_next_candidate(harness,monkeypatch):
    request, values, statuses, actions = harness
    original = module.read_report_pdf
    def read(path):
        Path(request['expected_project']).write_bytes(b'external modification')
        return original(path)
    monkeypatch.setattr(module,'read_report_pdf',read)
    with pytest.raises(ValueError, match='Source project changed'):
        module.run_layout_candidates(**request)
    assert actions == ['copy','layout','calculate']
