"""Restart calculation from an explicitly selected saved native checkpoint."""
import hashlib
import json
from pathlib import Path

if __package__:
    from .desktop import desktop_open
    from .workflow import calculation_checkpoint
    from .regulations import evaluate_profile
else:
    from desktop import desktop_open
    from workflow import calculation_checkpoint
    from regulations import evaluate_profile


def recover_saved_project(source: str, source_sha256: str, output_directory: str,
                          checks: list[dict], expected_current_project: str | None = None) -> dict:
    """Copy a pinned .evo checkpoint, open it and recalculate with explicit checks.

    Each invocation creates a new recovery directory. Partial mutation journals
    remain available to inspect before choosing the saved checkpoint to restore.
    """
    original = Path(source).resolve(strict=True)
    if original.suffix.lower() != '.evo':
        raise ValueError('Expected an existing .evo checkpoint')
    data = original.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != source_sha256:
        raise ValueError('Saved checkpoint hash differs from source_sha256')
    if not isinstance(checks, list) or not 1 <= len(checks) <= 100:
        raise ValueError('Provide explicit scoped report checks')
    identities = []
    for check in checks:
        if not isinstance(check, dict) or not {'summary_id', 'profile'} <= set(check) or set(check)-{'summary_id', 'profile', 'context'}:
            raise ValueError('Invalid scoped report check')
        if not isinstance(check['summary_id'], str) or not check['summary_id']:
            raise ValueError('Explicit summary_id required')
        identities.append(check['summary_id'])
        evaluate_profile(check['profile'], [], check.get('context'))
    if len(set(identities)) != len(identities):
        raise ValueError('Duplicate report scopes')
    json.dumps(checks, allow_nan=False)
    root = Path(output_directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    copy = root/'recovered.evo'
    journal = {'schema': 'dialux-agent/recovery/v1', 'state': 'prepared',
               'source': str(original), 'source_sha256': digest, 'project': str(copy),
               'checks': checks, 'steps': []}
    def persist():
        temporary = root/'journal.tmp'
        temporary.write_text(json.dumps(journal, indent=2), encoding='utf-8')
        temporary.replace(root/'journal.json')
    persist()
    try:
        copy.write_bytes(data)
        journal['state'] = 'opening_copy'
        persist()
        opened = desktop_open(str(copy), expected_current_project=expected_current_project)
        journal['steps'].append({'operation': 'open', 'result': opened})
        journal['state'] = 'recalculating'
        persist()
        result = calculation_checkpoint(str(copy), str(root/'calculation'), checks, recalculate=True)
        journal['steps'].append({'operation': 'calculation_checkpoint', 'result': result})
        if hashlib.sha256(original.read_bytes()).hexdigest() != digest:
            raise ValueError('Source checkpoint changed during recovery')
        journal.update(state='completed', source_unchanged=True, result=result,
                       native_sha256=hashlib.sha256(copy.read_bytes()).hexdigest())
        persist()
        return journal
    except Exception as exc:
        journal.update(failed_at=journal['state'], state='failed', error=str(exc))
        persist()
        raise ValueError(f'Recovery interrupted; inspect {root / "journal.json"}: {exc}') from exc
