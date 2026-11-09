import copy
import json
from pathlib import Path

import pytest
from src import iterations as module


@pytest.fixture
def harness(tmp_path, monkeypatch):
    project = tmp_path/'source.evo'
    project.write_bytes(b'original')
    spec = json.loads((Path(__file__).parents[1]/'examples/synthetic-grid-layout.json').read_text())
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
