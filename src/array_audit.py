"""Offline replay of completed guarded-array evidence; no desktop access."""
import hashlib
import json
import math
from pathlib import Path
if __package__:
    from .array_transform import plan_array_transform
    from .array_commit import MOTION_FIELDS, _display_values
    from .inspection import verify_group_checkpoint
else:
    from array_transform import plan_array_transform
    from array_commit import MOTION_FIELDS, _display_values
    from inspection import verify_group_checkpoint


def verify_array_execution(evidence_directory: str) -> dict:
    """Reconstruct preflight and all geometry checks from hash-bound artifacts.

    Hash consistency is not authentication or proof of a live native operation.
    Saved project persistence and simulation require separate evidence.
    """
    root=Path(evidence_directory).resolve(strict=True)
    raw=(root/'journal.json').read_bytes();journal=json.loads(raw)
    if journal.get('schema')!='dialux-agent/array-execution/v1' or journal.get('state')!='geometry_verified_unsaved':
        raise ValueError('Completed guarded-array geometry evidence required')
    def artifact(name,hash_key):
        data=(root/name).read_bytes()
        if hashlib.sha256(data).hexdigest()!=journal.get(hash_key):
            raise ValueError('Array artifact hash mismatch: '+name)
        return json.loads(data)
    request=artifact('request.json','request_sha256')
    arrangement=artifact('arrangement.json','arrangement_sha256')
    preflight=artifact('preflight.json','preflight_sha256')
    before=json.loads((root/'before/observed.json').read_bytes())
    after=json.loads((root/'after/observed.json').read_bytes())
    if request.get('group_id')!=journal.get('group_id') or arrangement.get('path')!=journal.get('project'):
        raise ValueError('Array request/project identity differs')
    reconstructed=plan_array_transform(request['spec'],before,arrangement)
    if reconstructed!=preflight: raise ValueError('Stored preflight differs from independent replay')
    baseline={'schema':'dialux-agent/layout/v1','units':'m','coordinate_frame':'active_storey','fixture_count':len(before['fixtures']),
              'fixtures':[{'id':str(i),'position_m':f['position_m'],'rotation_deg':f['rotation_deg'][2]} for i,f in enumerate(before['fixtures'])]}
    checked_before=verify_group_checkpoint(str(root/'before'),baseline)
    checked_after=verify_group_checkpoint(str(root/'after'),reconstructed['layout'])
    for label in ('before','after'):
        scan=json.loads((root/label/'journal.json').read_bytes())
        if scan.get('project')!=journal['project'] or scan.get('group_id')!=journal['group_id'] or scan.get('source_file_sha256')!=journal.get('source_file_sha256'):
            raise ValueError('Inspection source identity differs')
    identities=lambda observed:{tuple(f['runtime_id']):f.get('name') for f in observed['fixtures']}
    if identities(before)!=identities(after): raise ValueError('Array fixture identities or names changed')
    old=_display_values(arrangement['display_values']);target=reconstructed['requested_values']
    changed=[k for k in MOTION_FIELDS if not math.isclose(old[k],target[k],rel_tol=0,abs_tol=1e-10)]
    expected_events=[];completed=[]
    for key in changed:
        expected_events.append({'state':'pending_field','field':key,'target':target[key],'completed_fields':list(completed)})
        completed.append(key)
        expected_events.append({'state':'field_verified','field':key,'completed_fields':list(completed)})
    events=journal.get('field_events')
    if not isinstance(events,list): raise ValueError('Field journal missing')
    if events[:1]==[{'state':'pending_results_clear'}]: events=events[1:]
    if events!=expected_events: raise ValueError('Field intent/commit sequence differs from replay')
    commit=journal.get('commit',{})
    wanted={**old,**target}
    if commit.get('before')!=arrangement['display_values'] or commit.get('completed_fields')!=changed or set(commit.get('after',{}))!=set(wanted):
        raise ValueError('Commit snapshot differs')
    for key,value in wanted.items():
        actual=commit['after'][key]
        if (actual!=value if isinstance(value,str) else type(actual) not in (int,float) or not math.isfinite(actual) or not math.isclose(actual,value,rel_tol=0,abs_tol=.00051)):
            raise ValueError('Committed field differs: '+key)
    return {'schema':'dialux-agent/array-evidence-verification/v1','state':'verified',
            'journal_sha256':hashlib.sha256(raw).hexdigest(),'fixture_count':len(after['fixtures']),
            'before':checked_before,'after':checked_after,'preflight_replayed':True,
            'field_sequence_verified':True,'source_authenticity_verified':False,
            'live_state_verified':False,'persistence_verified':False,'simulation_verified':False,
            'warning':'Offline consistency and geometry only; not authentication, live-state proof or whole-project acceptance.'}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-directory',required=True)
    args=parser.parse_args()
    try:
        print(json.dumps(verify_array_execution(args.evidence_directory),indent=2,allow_nan=False))
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(json.dumps({'state':'rejected','error':str(exc)}))
        raise SystemExit(2)
