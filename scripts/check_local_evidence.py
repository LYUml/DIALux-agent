"""Read-only local checkpoint verification; does not run DIALux or certify a design."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def check(root=ROOT):
    live = json.loads((root/'docs/acceptance-artifacts.json').read_text())['artifacts']
    sources = json.loads((root/'profiles/hk-sources.snapshot.json').read_text())
    if not live or not sources:
        raise ValueError('Evidence manifests must not be empty')
    rows = []
    for item in [*live, *sources]:
        path = (root/item['path']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Evidence path escapes checkout')
        row = {'path': item['path'], 'expected_sha256': item['sha256']}
        if not path.is_file():
            row['status'] = 'missing'
        else:
            row['actual_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            row['status'] = 'match' if row['actual_sha256'] == item['sha256'] else 'changed'
        rows.append(row)
    status = 'changed' if any(r['status'] == 'changed' for r in rows) else (
        'missing' if any(r['status'] == 'missing' for r in rows) else 'match')
    return {'artifact_integrity': status, 'files': rows, 'live_ui_replayed': False,
            'compliance_status': 'not_evaluated',
            'scope': 'Recorded local artifacts and cached official sources only; originals use the separate input manifest.'}


if __name__ == '__main__':
    try:
        result = check()
        print(json.dumps(result, indent=2))
        sys.exit({'match': 0, 'changed': 1, 'missing': 3}[result['artifact_integrity']])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}))
        sys.exit(2)
