"""Connect exported evidence to a replaceable criteria profile."""
if __package__:
    from .results import read_summary_pdf, read_report_pdf
    from .regulations import evaluate_profile
else:
    from results import read_summary_pdf, read_report_pdf
    from regulations import evaluate_profile


def check_report(path: str, profile: dict, context: dict | None = None) -> dict:
    """Read a supported DIALux PDF and check only supplied criteria and context.

    Applicability remains caller-evidenced; report targets are never substituted
    for profile limits. No DIALux calculation is launched by this operation.
    """
    report = read_summary_pdf(path)
    assessment = evaluate_profile(profile, report['measurements'], context)
    return {'schema': 'dialux-agent/report-assessment/v1',
            'status': assessment['status'], 'report': report,
            'assessment': assessment}


def check_report_summary(path: str, summary_id: str, profile: dict, context: dict | None = None) -> dict:
    """Check precisely one selected room/scene; context must apply to that summary."""
    if not isinstance(summary_id, str) or not summary_id:
        raise ValueError('Explicit summary_id from report reader is required')
    report = read_report_pdf(path)
    matches = [s for s in report['summaries'] if s['summary_id'] == summary_id]
    if len(matches) != 1:
        raise ValueError('Summary ID not found or ambiguous; read the current report again')
    selected = matches[0]
    assessment = evaluate_profile(profile, selected['measurements'], context)
    return {'schema': 'dialux-agent/scoped-report-assessment/v1', 'status': assessment['status'],
            'source': report['source'], 'sha256': report['sha256'], 'summary': selected,
            'assessment': assessment, 'whole_project_assessed': False,
            'warning': 'Assessment applies only to this report room/scene and caller-supplied applicability context.'}


def calculation_checkpoint(expected_project: str, evidence_directory: str, checks: list[dict],
                           recalculate: bool = False) -> dict:
    """Calculate, export scoped evidence, evaluate explicit checks and save the native project.

    This mutates calculation state and saves the expected project. Use a test copy.
    A new directory is required; failures retain their stage and are not retried.
    Checks contain summary_id, profile and optional context. No layout edits or
    implicit criteria selection occur. Passing checks are not whole-project approval.
    """
    import json
    from pathlib import Path
    if __package__:
        from .desktop import desktop_calculate, desktop_export_pdf, desktop_save
    else:
        from desktop import desktop_calculate, desktop_export_pdf, desktop_save
    project=Path(expected_project).resolve(strict=True)
    if project.suffix.lower()!='.evo' or type(recalculate) is not bool:
        raise ValueError('Expected native project and boolean recalculate')
    if not isinstance(checks,list) or not 1<=len(checks)<=100:
        raise ValueError('Provide 1 to 100 explicit scoped checks')
    ids=[]
    for check in checks:
        if not isinstance(check,dict) or not {'summary_id','profile'}<=set(check) or not set(check)<={'summary_id','profile','context'}:
            raise ValueError('Each check requires summary_id, profile and optional context')
        if not isinstance(check['summary_id'],str) or not check['summary_id']:
            raise ValueError('Explicit summary_id required')
        ids.append(check['summary_id'])
        evaluate_profile(check['profile'],[],check.get('context'))
    if len(set(ids))!=len(ids): raise ValueError('Use one combined profile per selected summary')
    # Validate serializability before making any native change.
    json.dumps(checks,allow_nan=False)
    directory=Path(evidence_directory).resolve()
    directory.mkdir(parents=True,exist_ok=False)
    journal={'schema':'dialux-agent/calculation-checkpoint/v1','project':str(project),
             'checks':checks,'recalculate':recalculate,'state':'prepared','steps':[],
             'whole_project_assessed':False}
    def record():
        temp=directory/'journal.tmp'
        temp.write_text(json.dumps(journal,indent=2,allow_nan=False),encoding='utf-8')
        temp.replace(directory/'journal.json')
    def step(name,call):
        journal['state']='pending_'+name
        record()
        result=call()
        journal['steps'].append({'operation':name,'result':result})
        record()
        return result
    record()
    try:
        step('calculate',lambda:desktop_calculate(str(project),recalculate=recalculate))
        report_path=directory/'report.pdf'
        step('export',lambda:desktop_export_pdf(str(project),str(report_path)))
        report=step('read_report',lambda:read_report_pdf(str(report_path)))
        journal['state']='assessing'
        record()
        assessments=[]
        for check in checks:
            matches=[s for s in report['summaries'] if s['summary_id']==check['summary_id']]
            if len(matches)!=1: raise ValueError('Requested room/scene missing or ambiguous in fresh report')
            assessments.append({'summary_id':check['summary_id'],
                'room_scene_header':matches[0]['room_scene_header'],
                'assessment':evaluate_profile(check['profile'],matches[0]['measurements'],check.get('context'))})
        statuses=[a['assessment']['status'] for a in assessments]
        status='unverified' if 'unverified' in statuses else ('fail' if 'fail' in statuses else 'pass')
        journal.update(assessments=assessments,status=status,
            decision={'pass':'selected_conditions_met','fail':'selected_conditions_not_met','unverified':'evidence_incomplete'}[status])
        step('save',lambda:desktop_save(str(project)))
        journal['state']='completed'
        record()
        return {'state':'completed','status':status,'decision':journal['decision'],
                'journal':str(directory/'journal.json'),'report':str(report_path),
                'report_sha256':report['sha256'],'assessments':assessments,
                'whole_project_assessed':False,'geometry_changed_by_workflow':False,
                'warning':'Only selected report checks evaluated. Native project saved; no geometry optimization or automatic retry. External UI changes are not excluded.'}
    except Exception as exc:
        journal['failed_at']=journal['state']
        journal.update(state='failed',error=str(exc))
        record()
        raise ValueError(f'Checkpoint failed; inspect {directory / "journal.json"} before retry: {exc}') from exc
