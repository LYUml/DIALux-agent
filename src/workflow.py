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
