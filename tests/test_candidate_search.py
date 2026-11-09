import copy
import json
from pathlib import Path
import pytest

from src.candidate_search import generate_offset_candidates
from src.candidate_search import run_offset_search
from src.layout import plan_grid


def spec():
    return json.loads((Path(__file__).parents[1]/'examples/synthetic-apply-grid.json').read_text())


def test_geometry_search_deduplicates_periodic_grids_and_keeps_input():
    source=spec(); original=copy.deepcopy(source)
    result=generate_offset_candidates(source,[0,.1,source['grid']['spacing_x_m']],[0])
    assert source==original
    assert result['decisions'][-1]['status']=='duplicate_physical_grid'
    assert len(result['candidates'])==2
    assert all(plan_grid(c)['fixture_count']==4 for c in result['candidates'])
    assert not result['simulation_verified'] and not result['optimality_verified']


def test_budget_is_reported_without_implying_complete_search():
    result=generate_offset_candidates(spec(),[0,.1,.2],[0],max_candidates=1)
    assert len(result['candidates'])==1
    assert not result['all_distinct_same_count_candidates_included']
    assert any(d['status']=='excluded_candidate_budget' for d in result['decisions'])


@pytest.mark.parametrize('offsets',[[],[True],[float('nan')],[0,0],[0]*21])
def test_invalid_domain_is_rejected(offsets):
    with pytest.raises(ValueError): generate_offset_candidates(spec(),offsets,[0])


def test_count_changing_offsets_are_excluded():
    source=spec()
    result=generate_offset_candidates(source,[0],[0, .8])
    assert any(d['status']=='excluded_count_change' for d in result['decisions'])


@pytest.mark.parametrize('fail',[False,True])
def test_search_plan_is_preserved_before_native_call(tmp_path,monkeypatch,fail):
    from src import iterations
    project=tmp_path/'source.evo';project.write_bytes(b'fixture')
    directory=tmp_path/'search'
    def run(source,group,candidates,checks,objective,policy,evidence):
        plan=json.loads((directory/'generation.json').read_text())
        request=json.loads((directory/'request.json').read_text())
        assert request['group_id']==group
        assert request['expected_project']==source
        assert request['x_offsets_m']==[0,.1]
        assert request['policy']==policy and request['objective']==objective
        assert candidates==plan['candidates']
        assert Path(evidence)==directory/'native'
        assert len(candidates)==2
        if fail: raise ValueError('Native test failure')
        return {'state':'completed','stop_reason':'candidate_list_exhausted'}
    monkeypatch.setattr(iterations,'run_layout_candidates',run)
    args=(str(project),'group',spec(),[0,.1],[0],[],{},{},str(directory))
    if fail:
        with pytest.raises(ValueError,match='Native test failure'):run_offset_search(*args)
        assert not (directory/'result.json').exists()
    else:
        result=run_offset_search(*args)
        import hashlib
        assert hashlib.sha256((directory/'generation.json').read_bytes()).hexdigest()==result['generation_sha256']
        assert hashlib.sha256((directory/'request.json').read_bytes()).hexdigest()==result['request_sha256']
        assert not result['optimality_verified']
    assert (directory/'generation.json').is_file()
    assert (directory/'request.json').is_file()
