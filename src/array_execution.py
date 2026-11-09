"""Journalled rigid-array execution using independent native callbacks."""
import hashlib
import json
from pathlib import Path
if __package__:
    from .array_transform import plan_array_transform
    from .layout import plan_grid
    from .inspection import verify_group_checkpoint
else:
    from array_transform import plan_array_transform
    from layout import plan_grid
    from inspection import verify_group_checkpoint


def _apply_array_transform(expected_project, spec, group_id, evidence_directory,
                           inspector, array_reader, array_editor):
    project=Path(expected_project).resolve(strict=True)
    if project.suffix.lower()!='.evo' or not isinstance(group_id,str) or group_id.count('_Luminaires_')!=1:
        raise ValueError('Explicit native project and arrangement identity required')
    target=plan_grid(spec);count=target['fixture_count']
    if not 1<=count<=2000: raise ValueError('Expected 1 to 2000 target fixtures')
    root=Path(evidence_directory).resolve();root.mkdir(parents=True,exist_ok=False)
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    original=sha(project)
    journal={'schema':'dialux-agent/array-execution/v1','project':str(project),'group_id':group_id,
             'state':'preparing','source_file_sha256':original,'field_events':[],
             'native_project_saved':False,'whole_project_verified':False}
    def persist():
        tmp=root/'journal.tmp';tmp.write_text(json.dumps(journal,indent=2,allow_nan=False),encoding='utf-8');tmp.replace(root/'journal.json')
    def stage(name): journal['state']=name;persist()
    def event(value): journal['field_events'].append(value);persist()
    def inspect(name):
        folder=root/name
        inspector(str(project),group_id,count,str(folder))
        return json.loads((folder/'observed.json').read_text(encoding='utf-8'))
    persist()
    try:
        (root/'request.json').write_text(json.dumps({'spec':spec,'group_id':group_id},indent=2,allow_nan=False),encoding='utf-8')
        journal['request_sha256']=sha(root/'request.json');stage('reading_before')
        before=inspect('before');arrangement=array_reader(str(project),group_id)
        plan=plan_array_transform(spec,before,arrangement)
        baseline={'schema':'dialux-agent/layout/v1','units':'m','coordinate_frame':'active_storey','fixture_count':count,
                  'fixtures':[{'id':str(i),'position_m':f['position_m'],'rotation_deg':f['rotation_deg'][2]} for i,f in enumerate(before['fixtures'])]}
        journal['before_integrity']=verify_group_checkpoint(str(root/'before'),baseline)
        (root/'preflight.json').write_text(json.dumps(plan,indent=2,allow_nan=False),encoding='utf-8')
        journal['preflight_sha256']=sha(root/'preflight.json')
        if sha(project)!=original: raise ValueError('Saved project changed before mutation')
        stage('pending_mutation')
        journal['commit']=array_editor(str(project),arrangement,plan['requested_values'],event)
        stage('reading_after');after=inspect('after')
        journal['after_verification']=verify_group_checkpoint(str(root/'after'),target)
        identities=lambda records:{tuple(f['runtime_id']):f.get('name') for f in records['fixtures']}
        if identities(before)!=identities(after): raise ValueError('Fixture identities or names changed during transform')
        if sha(project)!=original: raise ValueError('Saved project changed during unsaved transform')
        journal.update(state='geometry_verified_unsaved',source_file_unchanged=True,
                       full_group_geometry_verified=True,calculation_verified=False,persistence_verified=False)
        persist();return {**journal,'journal':str(root/'journal.json')}
    except Exception as exc:
        journal.update(failed_at=journal['state'],state='failed',error=str(exc),native_outcome_verified=False)
        persist();raise ValueError(f'Array outcome requires inspection at {root}: {exc}') from exc
