"""Read-only source inventory: first building block, not a DIALux simulator."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def inventory(source):
    root = Path(source).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Source must be a directory')
    records = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in {'.pdf', '.dwg'}:
            record = {'name': path.name, 'bytes': path.stat().st_size,
                      'sha256': fingerprint(path)}
            if path.suffix.lower() == '.dwg':
                with path.open('rb') as stream:
                    record['header'] = stream.read(6).decode('ascii', errors='replace')
                record['geometry_validated'] = False
            records.append(record)
    if not records:
        raise ValueError('No PDF or DWG inputs found')
    return {'schema': 'dialux-agent/input-manifest/v1', 'source': str(root), 'files': records}


def verify(manifest):
    if manifest.get('schema') != 'dialux-agent/input-manifest/v1':
        raise ValueError('Unsupported manifest schema')
    root = Path(manifest['source']).resolve(strict=True)
    failures = []
    if not manifest['files']:
        raise ValueError('Manifest contains no inputs')
    for record in manifest['files']:
        path = (root / record['name']).resolve()
        if path.parent != root:
            raise ValueError('Input path escapes source directory')
        if not path.is_file() or fingerprint(path) != record['sha256']:
            failures.append(record['name'])
    return {'ok': not failures, 'changed_or_missing': failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inventory').add_argument('--source', required=True)
    commands.add_parser('verify').add_argument('--manifest', required=True)
    room = commands.add_parser('room-create')
    room.add_argument('--spec', required=True)
    room.add_argument('--output', required=True)
    commands.add_parser('stf-inspect').add_argument('--path', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'room-create':
            from backend import create_room
            result = create_room(json.loads(Path(args.spec).read_text(encoding='utf-8-sig')), args.output)
        elif args.command == 'stf-inspect':
            from backend import inspect_stf
            result = inspect_stf(args.path)
        else:
            result = inventory(args.source) if args.command == 'inventory' else verify(
                json.loads(Path(args.manifest).read_text(encoding='utf-8-sig')))
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result.get('ok', True) else 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
