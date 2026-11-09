import copy
import json
from pathlib import Path
import pytest

from src.candidate_search import generate_offset_candidates
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
