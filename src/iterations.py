"""Bounded, explicitly supplied layout candidates using actual native checkpoints."""
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .desktop import desktop_save_as
    from .placement import apply_grid_layout
    from .layout import plan_grid
    from .workflow import calculation_checkpoint
    from .results import read_report_pdf
    from .regulations import evaluate_profile
else:
    from desktop import desktop_save_as
    from placement import apply_grid_layout
    from layout import plan_grid
    from workflow import calculation_checkpoint
    from results import read_report_pdf
    from regulations import evaluate_profile


def run_layout_candidates(expected_project: str, group_id: str, candidates: list[dict],
                          checks: list[dict], objective: dict, policy: dict,
                          evidence_directory: str) -> dict:
    """Run explicit same-count grids on new native copies; never auto-install a winner.

    Every candidate uses real movement, calculation, PDF evidence and native save.
    No automatic candidate generation, solver approximation, resume or rollback.
    The current session must already contain the expected project and group.
    """
    source = Path(expected_project).resolve(strict=True)
    if source.suffix.lower() != '.evo' or not isinstance(group_id, str) or not group_id:
        raise ValueError('Expected native source project and explicit group')
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 20:
        raise ValueError('Provide 1 to 20 explicit candidate grid specifications')
    plans = [plan_grid(spec) for spec in candidates]
    baseline = {k: v for k, v in candidates[0].items() if k != 'grid'}
    if any({k: v for k, v in spec.items() if k != 'grid'} != baseline for spec in candidates):
        raise ValueError('Candidates may vary only grid parameters; room and product remain fixed')
    if not plans[0]['fixture_count'] or any(p['fixture_count'] != plans[0]['fixture_count'] for p in plans):
        raise ValueError('Candidates must have the same nonzero fixture count')
    if any(f['rotation_deg'] != 0 for p in plans for f in p['fixtures']):
        raise ValueError('Native candidate movement currently requires zero rotation')
    if not isinstance(checks, list) or not 1 <= len(checks) <= 100:
        raise ValueError('Explicit scoped checks required')
    ids = []
    for check in checks:
        if not isinstance(check, dict) or not {'summary_id', 'profile'} <= set(check) <= {'summary_id', 'profile', 'context'}:
            raise ValueError('Invalid scoped check')
        if not isinstance(check['summary_id'], str) or not check['summary_id']:
            raise ValueError('Explicit summary identity required')
        ids.append(check['summary_id'])
        evaluate_profile(check['profile'], [], check.get('context'))
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate summary checks')
    if not isinstance(objective, dict) or set(objective) != {'summary_id', 'metric', 'unit', 'calculation_surface', 'direction'}:
        raise ValueError('Objective requires exact summary, metric, unit, surface and direction')
    if any(not isinstance(v, str) or not v for v in objective.values()) or objective['direction'] not in ('minimize', 'maximize'):
        raise ValueError('Invalid objective')
    if objective['summary_id'] not in ids:
        raise ValueError('Objective summary must have a scoped check')
    if not isinstance(policy, dict) or set(policy) != {'max_iterations', 'no_improvement_limit', 'minimum_improvement', 'stop_on_pass'}:
        raise ValueError('Explicit iteration budget, no-improvement limit, minimum improvement and stop_on_pass required')
    for key in ('max_iterations', 'no_improvement_limit'):
        if type(policy[key]) is not int or not 1 <= policy[key] <= 20:
            raise ValueError('Iteration limits must be integers from 1 to 20')
    delta = policy['minimum_improvement']
    if type(delta) not in (int, float) or not math.isfinite(delta) or delta < 0 or type(policy['stop_on_pass']) is not bool:
        raise ValueError('Invalid stopping policy')
    json.dumps([candidates, checks, objective, policy], allow_nan=False)
    directory = Path(evidence_directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    journal = {'schema': 'dialux-agent/candidate-run/v1', 'source': str(source),
               'source_sha256': digest, 'candidates': candidates, 'checks': checks,
               'objective': objective, 'policy': policy, 'iterations': [],
               'state': 'prepared', 'best_candidate': None, 'best_feasible_candidate': None,
               'whole_project_assessed': False, 'winner_installed': False}
    def record():
        temporary = directory/'journal.tmp'
        temporary.write_text(json.dumps(journal, indent=2, allow_nan=False), encoding='utf-8')
        temporary.replace(directory/'journal.json')
    def unchanged():
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError('Source project changed during candidate run')
    def better(value, prior):
        difference = value-prior if objective['direction'] == 'maximize' else prior-value
        return difference > delta
    record()
    current, best, feasible, stale = str(source), None, None, 0
    try:
        budget = min(len(candidates), policy['max_iterations'])
        for index in range(budget):
            unchanged()
            item = {'index': index, 'state': 'pending_copy'}
            journal['iterations'].append(item)
            journal['state'] = 'running'
            record()
            project = directory/f'candidate-{index:03}.evo'
            item['copy'] = desktop_save_as(current, str(project))
            current = str(project)
            item.update(project=current, state='pending_layout')
            record()
            item['layout'] = apply_grid_layout(candidates[index], current, group_id, str(directory/f'layout-{index:03}'))
            if item['layout'].get('state') != 'verified':
                raise ValueError('Candidate geometry did not verify')
            item['state'] = 'pending_calculation'
            record()
            checkpoint = calculation_checkpoint(current, str(directory/f'calculation-{index:03}'), checks, recalculate=True)
            item['checkpoint'] = checkpoint
            if checkpoint.get('state') != 'completed' or checkpoint.get('status') not in ('pass', 'fail', 'unverified'):
                raise ValueError('Calculation checkpoint did not complete')
            report = read_report_pdf(checkpoint['report'])
            if report['sha256'] != checkpoint['report_sha256']:
                raise ValueError('Checkpoint report changed before comparison')
            summaries = [s for s in report['summaries'] if s['summary_id'] == objective['summary_id']]
            values = [m['value'] for s in summaries for m in s['measurements']
                      if all(m.get(k) == objective[k] for k in ('metric', 'unit', 'calculation_surface'))]
            if len(summaries) != 1 or len(values) != 1 or type(values[0]) not in (int, float) or not math.isfinite(values[0]):
                raise ValueError('Objective measurement missing, ambiguous or nonfinite')
            value = values[0]
            item.update(state='completed', objective_value=value)
            if best is None or better(value, best):
                best, stale = value, 0
                journal['best_candidate'] = index
            else:
                stale += 1
            if checkpoint['status'] == 'pass' and (feasible is None or better(value, feasible)):
                feasible = value
                journal['best_feasible_candidate'] = index
            unchanged()
            record()
            reason = ('evidence_incomplete' if checkpoint['status'] == 'unverified' else
                      'selected_conditions_met' if checkpoint['status'] == 'pass' and policy['stop_on_pass'] else
                      'no_improvement' if stale >= policy['no_improvement_limit'] else None)
            if reason:
                break
        else:
            reason = 'candidate_list_exhausted' if budget == len(candidates) else 'iteration_budget'
        journal.update(state='completed', stop_reason=reason, source_unchanged=True,
                       active_project=current, journal=str(directory/'journal.json'))
        record()
        return journal
    except Exception as exc:
        journal.update(state='failed', error=str(exc), active_project=current)
        record()
        raise ValueError(f'Candidate run failed; inspect {directory / "journal.json"} before further actions: {exc}') from exc
