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


def read_realized_group(project, group_id):
    first = desktop_group_fixtures(project, group_id)
    fixtures = list(first['fixtures'])
    offset = first.get('next_offset')
    while offset is not None:
        if len(fixtures) >= 2000:
            raise ValueError('Realized group inspection exceeds 2000 fixtures')
        page = desktop_group_fixtures(project, group_id, offset=offset, inventory_token=first['inventory_token'])
        if page['offset'] != offset or page['inventory_token'] != first['inventory_token']:
            raise ValueError('Inconsistent inspection continuation')
        fixtures.extend(page['fixtures'])
        new_offset = page.get('next_offset')
        if new_offset is not None and new_offset <= offset:
            raise ValueError('Inspection continuation did not advance')
        offset = new_offset
    if len(fixtures) != first.get('realized_node_count', first['observed_count']):
        raise ValueError('Realized group count changed across pages')
    return {**first, 'fixtures': fixtures, 'observed_count': len(fixtures), 'next_offset': None}


def apply_grid_layout(spec: dict, expected_project: str, group_id: str, evidence_directory: str) -> dict:
    """Move an existing equal-count group onto a zero-rotation validated grid.

    Runs real desktop operations and clears cached results. Does not create/delete
    fixtures, change photometry, save or calculate. Failure leaves a journal and
    possibly partial movement; inspect the project before starting another run.
    """
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
        before = read_realized_group(str(project), group_id)
        journal['before'] = before
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
            step['result'] = desktop_edit_fixture(str(project), source['runtime_id'], source['position_m'], target['position_m'])
            step['state'] = 'committed'
            record()
        journal['state'] = 'verifying'
        record()
        after = read_realized_group(str(project), group_id)
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
