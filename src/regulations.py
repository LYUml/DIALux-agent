"""Region-independent, source-backed criteria evaluation.

Profiles supply thresholds; the evaluator never supplies regulatory defaults.
Missing evidence is NOT a pass.
"""
import math
import operator

OPS = {'>=': operator.ge, '<=': operator.le, '>': operator.gt, '<': operator.lt, '==': operator.eq}
SOURCE_FIELDS = ('document_title', 'edition', 'clause_or_table', 'page',
                 'source_path_or_url', 'applicability', 'verified_by', 'verified_date')


def applicability(conditions, context):
    """Conservative conjunction: incomplete evidence stays unknown, never exempt."""
    if not isinstance(conditions, list):
        raise ValueError('applicable_when must be a list')
    checks = []
    for condition in conditions:
        if not isinstance(condition, dict) or not isinstance(condition.get('fact'), str) or not condition['fact'].strip():
            raise ValueError('Applicability condition requires a fact name')
        op, expected = condition.get('operator'), condition.get('value')
        numeric = isinstance(expected, (int, float)) and not isinstance(expected, bool)
        if op not in OPS or not isinstance(expected, (str, bool, int, float)) or (numeric and not math.isfinite(expected)) or (op != '==' and not numeric):
            raise ValueError('Invalid applicability operator or value')
        if numeric and (not isinstance(condition.get('unit'), str) or not condition['unit'].strip()):
            raise ValueError('Numeric applicability condition requires a unit')
        fact = context.get(condition['fact'])
        check = {'condition': condition, 'status': 'unknown'}
        checks.append(check)
        if not isinstance(fact, dict) or not isinstance(fact.get('evidence'), str) or not fact['evidence'].strip():
            continue
        actual = fact.get('value')
        if numeric:
            if isinstance(actual, bool) or not isinstance(actual, (int, float)) or not math.isfinite(actual) or fact.get('unit') != condition['unit']:
                continue
        elif type(actual) is not type(expected):
            continue
        check.update(status='met' if OPS[op](actual, expected) else 'not_met', evidence=fact['evidence'], value=actual)
    if any(c['status'] == 'unknown' for c in checks):
        return 'unknown', checks
    return ('not_applicable' if any(c['status'] == 'not_met' for c in checks) else 'applicable'), checks


def evaluate_profile(profile: dict, measurements: list[dict], context: dict | None = None) -> dict:
    if not isinstance(profile, dict) or not isinstance(measurements, list) or any(not isinstance(m, dict) for m in measurements):
        raise ValueError('Expected a profile object and a list of measurement objects')
    if profile.get('schema') != 'dialux-agent/criteria-profile/v1':
        raise ValueError('Unsupported criteria profile')
    if not isinstance(profile.get('criteria'), list) or any(not isinstance(c, dict) for c in profile['criteria']):
        raise ValueError('Expected a list of criterion objects')
    if context is None:
        context = {}
    if not isinstance(context, dict):
        raise ValueError('Context must be an object of evidenced facts')
    rows = []
    seen = set()
    for criterion in profile.get('criteria', []):
        for key in ('id', 'metric', 'unit', 'calculation_surface'):
            if not isinstance(criterion.get(key), str) or not criterion[key].strip():
                raise ValueError(f'Missing criterion {key}')
        if criterion['id'] in seen:
            raise ValueError('Duplicate criterion id')
        seen.add(criterion['id'])
        row = {'id': criterion.get('id'), 'metric': criterion.get('metric'),
               'status': 'unverified', 'source': criterion.get('source')}
        rows.append(row)
        source = criterion.get('source', {})
        if profile.get('status') != 'verified' or not isinstance(source, dict) or not all(isinstance(source.get(k), (str, int)) and not isinstance(source.get(k), bool) and str(source[k]).strip() for k in SOURCE_FIELDS):
            row['reason'] = 'Profile or source not verified'
            continue
        op = criterion.get('operator')
        threshold = criterion.get('threshold')
        if op not in OPS or isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold):
            raise ValueError('Invalid criterion operator or threshold')
        applies, checks = applicability(criterion.get('applicable_when', []), context)
        row['applicability_checks'] = checks
        if applies != 'applicable':
            row['status'] = 'unverified' if applies == 'unknown' else 'not_applicable'
            row['reason'] = 'Applicability evidence incomplete' if applies == 'unknown' else 'Supplied applicability conditions not met'
            continue
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
    active = [r for r in rows if r['status'] != 'not_applicable']
    overall = 'unverified' if not active or any(r['status'] == 'unverified' for r in active) else ('fail' if any(r['status'] == 'fail' for r in active) else 'pass')
    return {'jurisdiction': profile.get('jurisdiction'), 'status': overall, 'criteria': rows,
            'scope': 'Only supplied criteria and measurements; not whole-project certification.'}
