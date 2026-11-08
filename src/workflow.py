"""Connect exported evidence to a replaceable criteria profile."""
if __package__:
    from .results import read_summary_pdf
    from .regulations import evaluate_profile
else:
    from results import read_summary_pdf
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
