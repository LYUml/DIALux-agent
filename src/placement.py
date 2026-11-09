"""Journalled native application of a validated grid to existing fixtures."""
import json
import math
from pathlib import Path

if __package__:
    from .layout import plan_grid, verify_observed_layout
    from .desktop import desktop_group_fixtures, desktop_edit_fixture
else:
    from layout import plan_grid, verify_observed_layout
    from desktop import desktop_group_fixtures, desktop_edit_fixture


def read_realized_group(project, group_id, expected_count=None, page_sink=None, page_reader=None):
    reader = page_reader or desktop_group_fixtures
    count_options = {'expected_count': expected_count} if expected_count is not None else {}
    first = reader(project, group_id, **count_options)
    if page_sink: page_sink(first)
    fixtures = list(first['fixtures'])
    offset = first.get('next_offset')
    while offset is not None:
        if len(fixtures) >= 2000:
            raise ValueError('Realized group inspection exceeds 2000 fixtures')
        page = reader(project, group_id, offset=offset, inventory_token=first['inventory_token'], **count_options)
        if (page['offset'] != offset or page['inventory_token'] != first['inventory_token']
                or page.get('coordinate_frame') != first.get('coordinate_frame')):
            raise ValueError('Inconsistent inspection continuation')
        if page_sink: page_sink(page)
        fixtures.extend(page['fixtures'])
        new_offset = page.get('next_offset')
        if new_offset is not None and new_offset <= offset:
            raise ValueError('Inspection continuation did not advance')
        offset = new_offset
    if len(fixtures) != first.get('container_node_count', first.get('realized_node_count', first['observed_count'])):
        raise ValueError('Realized group count changed across pages')
    return {**first, 'fixtures': fixtures, 'observed_count': len(fixtures), 'next_offset': None}


def apply_grid_layout(spec: dict, expected_project: str, group_id: str, evidence_directory: str) -> dict:
    """Apply and verify a grid inside one independently locked native worker."""
    if __package__:
        from .desktop import _run
    else:
        from desktop import _run
    return _run('apply-grid',expected_project,parameters={'spec':spec,'group_id':group_id,
                                                       'evidence_directory':evidence_directory})


def _apply_grid_layout(spec: dict, expected_project: str, group_id: str, evidence_directory: str,
                       page_reader=None, fixture_editor=None) -> dict:
    """Move an existing equal-count group onto a zero-rotation validated grid.

    Runs real desktop operations and clears cached results. Does not create/delete
    fixtures, change photometry, save or calculate. Failure leaves a journal and
    possibly partial movement; inspect the project before starting another run.
    """
    editor = fixture_editor or desktop_edit_fixture
    plan = plan_grid(spec)
    if not plan['fixtures'] or any(abs(f['rotation_deg'] % 360) > 1e-9 for f in plan['fixtures']):
        raise ValueError('Application currently requires a nonempty zero-rotation grid')
    project = Path(expected_project).resolve(strict=True)
    if project.suffix.lower() != '.evo' or not isinstance(group_id, str) or not group_id.strip():
        raise ValueError('Expected native project and explicit group ID')
    directory = Path(evidence_directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    journal = {'schema': 'dialux-agent/placement-run/v1', 'project': str(project), 'group_id': group_id,
               'state': 'inspecting', 'plan': plan, 'steps': [], 'native_project_saved': False}
    def record():
        temporary = directory / 'journal.tmp'
        temporary.write_text(json.dumps(journal, indent=2, allow_nan=False) + '\n', encoding='utf-8')
        temporary.replace(directory / 'journal.json')
    record()
    try:
        before = read_realized_group(str(project), group_id, page_reader=page_reader)
        journal['before'] = before
        if before.get('coordinate_frame') != 'active_storey':
            raise ValueError('Native observation coordinate frame is not active_storey; no movement attempted')
        if before.get('next_offset') is not None or before.get('offset', 0) != 0:
            raise ValueError('Paged group requires a complete inspection workflow before application; no movement attempted')
        current = before['fixtures']
        if len(current) != len(plan['fixtures']) or before['observed_count'] != len(current):
            raise ValueError('Existing realized fixture count must equal planned count; no creation/deletion attempted')
        identities = [tuple(f['runtime_id']) for f in current]
        if len(set(identities)) != len(identities):
            raise ValueError('Duplicate native runtime identities')
        for fixture in current:
            for key in ('position_m', 'rotation_deg'):
                values = fixture[key]
                if len(values) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
                    raise ValueError('Invalid native coordinate evidence')
            if any(abs((a+180) % 360-180) > .05 for a in fixture['rotation_deg']):
                raise ValueError('Existing fixtures must have zero rotation; no rotation edits supported')
        # Stable spatial ordering is an explicit assignment, not a claimed product
        # identity match. Photometry remains unchanged and unverified against spec.
        # Ignore sub-nanometre centroid arithmetic noise when ordering rows;
        # keep the actual target coordinates unrounded for movement/verification.
        spatial_key = lambda f: tuple(round(f['position_m'][i], 9) for i in (1, 0, 2))
        current = sorted(current, key=spatial_key)
        targets = sorted(plan['fixtures'], key=spatial_key)
        journal['state'] = 'moving'
        record()
        for source, target in zip(current, targets):
            step = {'fixture_id': target['id'], 'runtime_id': source['runtime_id'],
                    'before_position_m': source['position_m'], 'target_position_m': target['position_m'],
                    'state': 'pending'}
            journal['steps'].append(step)
            record()  # Persist intent before a potentially partial native mutation.
            step['result'] = editor(str(project), source['runtime_id'], source['position_m'], target['position_m'])
            step['state'] = 'committed'
            record()
        journal['state'] = 'verifying'
        record()
        after = read_realized_group(str(project), group_id, page_reader=page_reader)
        if after.get('next_offset') is not None or after.get('offset', 0) != 0:
            raise ValueError('Final inspection is partial; cannot verify placement')
        journal['after'] = after
        journal['verification'] = verify_observed_layout(plan, after)
        journal['state'] = 'verified'
        journal['whole_project_verified'] = False
        journal['photometry_identity_verified'] = False
        record()
        return {'state': 'verified', 'journal': str(directory / 'journal.json'),
                'matched_count': journal['verification']['matched_count'], 'native_project_saved': False,
                'whole_project_verified': False, 'photometry_identity_verified': False,
                'warning': 'Only the supplied realized group geometry was checked. Save/reopen and calculate separately. No automatic rollback or resume.'}
    except Exception as exc:
        journal['state'] = 'failed'
        journal['error'] = str(exc)
        record()
        raise ValueError(f'Placement failed; inspect {directory / "journal.json"} and native project before retry: {exc}') from exc



def inspect_group_checkpoint(expected_project: str, group_id: str, expected_count: int,
                             evidence_directory: str) -> dict:
    """Read a complete group in one native worker, retaining UIA references."""
    if __package__:
        from .desktop import _run
    else:
        from desktop import _run
    return _run('inspect-group', expected_project, parameters={
        'group_id': group_id, 'expected_count': expected_count,
        'evidence_directory': evidence_directory})


def _inspect_group_checkpoint(expected_project: str, group_id: str, expected_count: int,
                              evidence_directory: str, page_reader=None) -> dict:
    """Collect all pages of one expected group, persisting evidence after each page.

    Uses the existing native paginated reader. May take minutes for large groups.
    Does not edit geometry, save, retry or resume. Failure retains partial evidence;
    never treat a progress file alone as proof of an active/successful process.
    """
    import hashlib
    from datetime import datetime, timezone
    project=Path(expected_project).resolve(strict=True)
    if project.suffix.lower()!='.evo' or not isinstance(group_id,str) or not group_id.strip():
        raise ValueError('Expected native project and explicit group ID')
    if type(expected_count) is not int or not 1<=expected_count<=2000:
        raise ValueError('expected_count must be 1 to 2000')
    directory=Path(evidence_directory).resolve()
    directory.mkdir(parents=True,exist_ok=False)
    before_hash=hashlib.sha256(project.read_bytes()).hexdigest()
    journal={'schema':'dialux-agent/inspection-checkpoint/v1','project':str(project),'group_id':group_id,
             'expected_count':expected_count,'state':'reading','pages':[],'read_count':0,
             'source_file_sha256':before_hash,'started_utc':datetime.now(timezone.utc).isoformat(),
             'whole_project_verified':False,'atomic_snapshot_verified':False}
    identities=set()
    token=None
    def record():
        temporary=directory/'journal.tmp'
        temporary.write_text(json.dumps(journal,indent=2,allow_nan=False),encoding='utf-8')
        temporary.replace(directory/'journal.json')
    def accept(page):
        nonlocal token
        if page.get('group_id')!=group_id or Path(page.get('path','')).resolve()!=project:
            raise ValueError('Inspection page belongs to another project or group')
        if page.get('coordinate_frame')!='active_storey' or page.get('offset')!=journal['read_count']:
            raise ValueError('Inspection page frame or offset differs')
        fixtures=page.get('fixtures')
        if not isinstance(fixtures,list) or not 1<=len(fixtures)<=4 or page.get('observed_count')!=len(fixtures):
            raise ValueError('Invalid inspection page fixture count')
        if page.get('container_node_count',page.get('realized_node_count'))!=expected_count:
            raise ValueError('Inspection inventory count differs from expected count')
        current_token=page.get('inventory_token')
        if not isinstance(current_token,str) or not current_token or (token is not None and current_token!=token):
            raise ValueError('Inspection inventory token changed')
        token=current_token
        count=journal['read_count']+len(fixtures)
        if count>expected_count or page.get('next_offset')!=(count if count<expected_count else None):
            raise ValueError('Inspection continuation skips or truncates fixtures')
        for fixture in fixtures:
            runtime=fixture.get('runtime_id')
            if not isinstance(runtime,list) or not runtime or any(type(v) is not int for v in runtime):
                raise ValueError('Invalid native runtime identity')
            if tuple(runtime) in identities: raise ValueError('Duplicate fixture identity across pages')
            identities.add(tuple(runtime))
            for key in ('position_m','rotation_deg'):
                vector=fixture.get(key)
                if not isinstance(vector,list) or len(vector)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in vector):
                    raise ValueError('Invalid native fixture geometry')
        data=(json.dumps(page,indent=2,allow_nan=False)+'\n').encode('utf-8')
        target=directory/f"page-{page['offset']:04d}.json"
        with target.open('xb') as stream: stream.write(data)
        journal['pages'].append({'offset':page['offset'],'path':str(target),'sha256':hashlib.sha256(data).hexdigest()})
        journal.update(read_count=count,inventory_token=token,pending_offset=page.get('next_offset'))
        record()
    record()
    try:
        observed=read_realized_group(str(project),group_id,expected_count=expected_count,page_sink=accept,page_reader=page_reader)
        if len(observed['fixtures'])!=expected_count or len(identities)!=expected_count:
            raise ValueError('Final inspection count mismatch')
        if hashlib.sha256(project.read_bytes()).hexdigest()!=before_hash:
            raise ValueError('Saved native source changed during inspection')
        data=(json.dumps(observed,indent=2,allow_nan=False)+'\n').encode('utf-8')
        output=directory/'observed.json'
        with output.open('xb') as stream: stream.write(data)
        journal.update(state='collected',observed_path=str(output),observed_sha256=hashlib.sha256(data).hexdigest(),
                       finished_utc=datetime.now(timezone.utc).isoformat())
        record()
        return {'state':'collected','observed_count':expected_count,'observed_path':str(output),
                'observed_sha256':journal['observed_sha256'],'journal':str(directory/'journal.json'),
                'whole_project_verified':False,'atomic_snapshot_verified':False,
                'warning':'All expected group records collected across time. Does not prove planned geometry, product identity, hidden project content or absence of external unsaved edits.'}
    except Exception as exc:
        journal.update(state='failed',error=str(exc),finished_utc=datetime.now(timezone.utc).isoformat())
        record()
        raise ValueError(f'Inspection failed; partial evidence retained at {directory}: {exc}') from exc
