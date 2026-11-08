"""Cache official source PDFs and record byte-level provenance; never activate rules."""
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads((ROOT / 'profiles/hk-sources.json').read_text(encoding='utf-8'))
    target = ROOT / 'local/references/official'
    target.mkdir(parents=True, exist_ok=True)
    records = []
    for source in catalog['sources']:
        path = target / (source['id'] + '.pdf')
        record = {'id': source['id'], 'url': source['url']}
        try:
            if path.exists():
                data = path.read_bytes()
                record['cache'] = 'existing'
            else:
                with urlopen(source['url'], timeout=45) as response:
                    data = response.read()
                    record['resolved_url'] = response.url
                if not data.startswith(b'%PDF-'):
                    raise ValueError('Response is not a PDF')
                path.write_bytes(data)
                record['cache'] = 'downloaded'
            if not data.startswith(b'%PDF-'):
                raise ValueError('Cached file is not a PDF')
            record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                          path=path.relative_to(ROOT).as_posix())
        except (OSError, ValueError) as exc:
            record['error'] = str(exc)
        records.append(record)
        print(json.dumps(record), flush=True)
    (target / 'manifest.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    return int(any('error' in row for row in records))


if __name__ == '__main__':
    raise SystemExit(main())
