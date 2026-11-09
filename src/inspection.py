"""Offline integrity and geometry checks for a completed inspection checkpoint."""
import hashlib
import json
from pathlib import Path

if __package__:
    from .layout import verify_observed_layout
else:
    from layout import verify_observed_layout


def verify_group_checkpoint(evidence_directory: str, layout: dict) -> dict:
    """Recheck page bytes, complete assembly and all supplied planned coordinates.

    Hash consistency is not authentication. Does not access the live desktop,
    establish an atomic snapshot or prove native product/simulation identity.
    """
    root = Path(evidence_directory).resolve(strict=True)
    journal_bytes = (root/'journal.json').read_bytes()
    journal = json.loads(journal_bytes)
    if journal.get('schema') != 'dialux-agent/inspection-checkpoint/v1' or journal.get('state') != 'collected':
        raise ValueError('A completed inspection checkpoint is required')
    count = journal.get('expected_count')
    if type(count) is not int or not 1 <= count <= 2000 or journal.get('read_count') != count or journal.get('pending_offset') is not None:
        raise ValueError('Invalid completed checkpoint counts or continuation')
    pages = journal.get('pages')
    if not isinstance(pages,list) or not pages or len(pages)>count:
        raise ValueError('Missing or invalid inspection pages')
    def read_bound(path, expected_name, expected_hash):
        target=Path(path).resolve(strict=True)
        if target.parent != root or target.name != expected_name:
            raise ValueError('Evidence path differs from expected checkpoint file')
        data=target.read_bytes()
        if hashlib.sha256(data).hexdigest()!=expected_hash:
            raise ValueError('Checkpoint evidence hash mismatch')
        return json.loads(data)
    fixtures=[]
    first=None
    identities=set()
    for entry in pages:
        offset=len(fixtures)
        if entry.get('offset')!=offset: raise ValueError('Inspection page offsets are not contiguous')
        page=read_bound(entry['path'],f'page-{offset:04d}.json',entry['sha256'])
        rows=page.get('fixtures')
        if not isinstance(rows,list) or not 1<=len(rows)<=4 or page.get('observed_count')!=len(rows):
            raise ValueError('Invalid inspection page records')
        if (page.get('operation')!='read_group_fixtures' or page.get('offset')!=offset
                or page.get('group_id')!=journal.get('group_id') or page.get('path')!=journal.get('project')
                or page.get('coordinate_frame')!='active_storey'
                or not page.get('inventory_token') or page.get('inventory_token')!=journal.get('inventory_token')
                or page.get('container_node_count',page.get('realized_node_count'))!=count):
            raise ValueError('Inconsistent inspection page identity or inventory')
        for row in rows:
            identity=row.get('runtime_id')
            if not isinstance(identity,list) or not identity or any(type(v) is not int for v in identity) or tuple(identity) in identities:
                raise ValueError('Invalid or duplicate inspection fixture identity')
            identities.add(tuple(identity))
        fixtures.extend(rows)
        if len(fixtures)>count or page.get('next_offset')!=(len(fixtures) if len(fixtures)<count else None):
            raise ValueError('Inspection page continuation differs')
        if first is None: first=page
    if len(fixtures)!=count: raise ValueError('Incomplete inspection page coverage')
    observed=read_bound(journal['observed_path'],'observed.json',journal['observed_sha256'])
    assembled={**first,'fixtures':fixtures,'observed_count':count,'next_offset':None}
    if observed!=assembled: raise ValueError('Combined observation differs from accepted pages')
    geometry=verify_observed_layout(layout,observed)
    return {'schema':'dialux-agent/inspection-verification/v1','state':'verified',
            'journal_sha256':hashlib.sha256(journal_bytes).hexdigest(),
            'observed_file_sha256':journal['observed_sha256'],'page_count':len(pages),
            'geometry':geometry,'evidence_hashes_consistent':True,
            'source_authenticity_verified':False,'atomic_snapshot_verified':False,
            'whole_project_verified':False,
            'warning':'Checks saved evidence consistency and supplied geometry only; hashes are not signatures and no live project was inspected.'}
