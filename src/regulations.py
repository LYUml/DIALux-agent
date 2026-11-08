"""Region-independent, source-backed criteria evaluation.

Profiles supply thresholds; the evaluator never supplies regulatory defaults.
Missing evidence is NOT a pass.
"""
import math
import operator

OPS = {'>=': operator.ge, '<=': operator.le, '>': operator.gt, '<': operator.lt, '==': operator.eq}
SOURCE_FIELDS = ('document_title', 'edition', 'clause_or_table', 'page',
                 'source_path_or_url', 'applicability', 'verified_by', 'verified_date')


def evaluate_profile(profile: dict, measurements: list[dict]) -> dict:
    if profile.get('schema') != 'dialux-agent/criteria-profile/v1':
        raise ValueError('Unsupported criteria profile')
    rows = []
    for criterion in profile.get('criteria', []):
        row = {'id': criterion.get('id'), 'metric': criterion.get('metric'),
               'status': 'unverified', 'source': criterion.get('source')}
        rows.append(row)
        source = criterion.get('source', {})
        if profile.get('status') != 'verified' or not all(source.get(k) is not None and source.get(k) != '' for k in SOURCE_FIELDS):
            row['reason'] = 'Profile or source not verified'
            continue
        op = criterion.get('operator')
        threshold = criterion.get('threshold')
        if op not in OPS or isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold):
            raise ValueError('Invalid criterion operator or threshold')
        matches = [m for m in measurements if m.get('metric') == criterion.get('metric')
                   and m.get('unit') == criterion.get('unit')
                   and m.get('calculation_surface') == criterion.get('calculation_surface')]
        if len(matches) != 1:
            row['reason'] = 'Missing or ambiguous measurement with matching unit and surface'
            continue
        measured = matches[0]
        value = measured.get('value')
        if not measured.get('evidence') or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            row['reason'] = 'Missing evidence or invalid measurement'
            continue
        row.update(value=value, threshold=threshold, unit=criterion['unit'],
                   evidence=measured['evidence'], status='pass' if OPS[op](value, threshold) else 'fail')
    overall = 'unverified' if not rows or any(r['status'] == 'unverified' for r in rows) else ('fail' if any(r['status'] == 'fail' for r in rows) else 'pass')
    return {'jurisdiction': profile.get('jurisdiction'), 'status': overall, 'criteria': rows,
            'scope': 'Only supplied criteria and measurements; not whole-project certification.'}
