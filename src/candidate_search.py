"""Bounded lattice-offset candidates; optical ranking belongs to native runs."""
import copy
import math
import hashlib
import json
from pathlib import Path

if __package__:
    from .layout import plan_grid
else:
    from layout import plan_grid


def generate_offset_candidates(spec: dict, x_offsets_m: list[float], y_offsets_m: list[float],
                               max_candidates: int = 20) -> dict:
    """Enumerate an explicit offset domain, preserving product, count and geometry.

    Uses the existing full-envelope/exclusion planner. Deduplicates equivalent
    physical grids and preserves caller order (X outer, Y inner). Does not infer
    search bounds, standards or photometric performance.
    """
    base = plan_grid(spec)
    if not 1 <= base['fixture_count'] <= 2000 or any(f['rotation_deg'] != 0 for f in base['fixtures']):
        raise ValueError('Native offset search requires 1 to 2000 zero-rotation fixtures')
    for offsets in (x_offsets_m, y_offsets_m):
        if not isinstance(offsets,list) or not 1 <= len(offsets) <= 20 or any(
            type(v) not in (int,float) or not math.isfinite(v) for v in offsets):
            raise ValueError('Each offset axis requires 1 to 20 finite metre offsets')
        if len(set(offsets)) != len(offsets):
            raise ValueError('Duplicate offsets on an axis')
    if type(max_candidates) is not int or not 1 <= max_candidates <= 20:
        raise ValueError('max_candidates must be an integer from 1 to 20')
    selected, decisions, seen = [], [], set()
    for dx in x_offsets_m:
        for dy in y_offsets_m:
            candidate = copy.deepcopy(spec)
            candidate['grid']['origin_m'] = [spec['grid']['origin_m'][0]+dx, spec['grid']['origin_m'][1]+dy]
            if not all(math.isfinite(v) for v in candidate['grid']['origin_m']):
                raise ValueError('Offset origin overflow')
            plan = plan_grid(candidate)
            decision = {'offset_m':[dx,dy], 'fixture_count':plan['fixture_count']}
            decisions.append(decision)
            if plan['fixture_count'] != base['fixture_count']:
                decision['status'] = 'excluded_count_change'
                continue
            key = tuple(sorted(tuple(round(v,9) for v in f['position_m']) for f in plan['fixtures']))
            if key in seen:
                decision['status'] = 'duplicate_physical_grid'
                continue
            seen.add(key)
            if len(selected) >= max_candidates:
                decision['status'] = 'excluded_candidate_budget'
                continue
            decision.update(status='selected', candidate_index=len(selected), plan_sha256=plan['input_sha256'])
            selected.append(candidate)
    if not selected:
        raise ValueError('No same-count candidates in the supplied offset domain')
    return {'schema':'dialux-agent/offset-candidates/v1', 'candidates':selected,
            'baseline_spec_sha256':base['input_sha256'],
            'baseline_fixture_count':base['fixture_count'], 'decisions':decisions,
            'max_candidates':max_candidates, 'domain_evaluated':True,
            'all_distinct_same_count_candidates_included':not any(d['status']=='excluded_candidate_budget' for d in decisions),
            'simulation_verified':False,'optimality_verified':False,
            'warning':'Geometry-only candidates from explicit bounds. Run actual native calculations before comparing lighting performance; no fixture-count or product search.'}


def run_offset_search(expected_project: str, group_id: str, spec: dict,
                      x_offsets_m: list[float], y_offsets_m: list[float], checks: list[dict],
                      objective: dict, policy: dict, evidence_directory: str,
                      max_candidates: int = 20) -> dict:
    """Persist a bounded geometry search plan, then run its actual native candidates.

    Reuses the candidate runner. Operational failures preserve the plan and its
    native journals; no retries, extrapolated performance or global optimum claim.
    """
    if __package__:
        from .iterations import run_layout_candidates
    else:
        from iterations import run_layout_candidates
    source = Path(expected_project).resolve(strict=True)
    if source.suffix.lower() != '.evo':
        raise ValueError('Expected a native source project')
    generated = generate_offset_candidates(spec,x_offsets_m,y_offsets_m,max_candidates)
    request = dict(expected_project=str(source), group_id=group_id, spec=spec,
                   x_offsets_m=x_offsets_m, y_offsets_m=y_offsets_m, checks=checks,
                   objective=objective, policy=policy, max_candidates=max_candidates)
    request_payload = (json.dumps(request,indent=2,allow_nan=False)+'\n').encode('utf-8')
    directory = Path(evidence_directory).resolve()
    directory.mkdir(parents=True,exist_ok=False)
    request_path = directory/'request.json'
    request_path.write_bytes(request_payload)
    path = directory/'generation.json'
    payload = (json.dumps(generated,indent=2,allow_nan=False)+'\n').encode('utf-8')
    path.write_bytes(payload)
    result = run_layout_candidates(str(source),group_id,generated['candidates'],checks,
                                   objective,policy,str(directory/'native'))
    response = {'schema':'dialux-agent/offset-search-run/v1', 'generation':str(path),
                'request':str(request_path),
                'request_sha256':hashlib.sha256(request_payload).hexdigest(),
                'generation_sha256':hashlib.sha256(payload).hexdigest(),
                'run':result,'optimality_verified':False,'whole_project_assessed':False}
    (directory/'result.json').write_text(json.dumps(response,indent=2,allow_nan=False),encoding='utf-8')
    return response
