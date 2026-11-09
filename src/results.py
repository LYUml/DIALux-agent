"""Read one English DIALux room Summary, standalone or within a full report."""
import hashlib
from io import BytesIO
import math
from pathlib import Path
import re

import pdfplumber
from pdfminer.psexceptions import PSException
from pdfplumber.utils.exceptions import PdfminerException

NUMBER = r'(\d+(?:\.\d+)?)'
SUMMARY_HEADER = r'^(Building .+?\s*\(Light scene\s+\d+\))\s*\nSummary\s*$'


def _one(pattern, text):
    matches = re.findall(pattern, text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError('Unsupported or ambiguous DIALux summary field: ' + pattern)
    return matches[0]


def parse_summary_pages(pages: list[str]) -> dict:
    if len(pages) != 2 or any(not text for text in pages):
        raise ValueError('Expected a text-based two-page single-room Summary')
    headers = []
    for text in pages:
        # Match the complete header, including a light-scene number wrapped onto a new line.
        header = _one(SUMMARY_HEADER, text)
        headers.append(' '.join(header.split()))
    if headers[0] != headers[1]:
        raise ValueError('Summary pages refer to different rooms or light scenes')
    a, b = pages
    area = float(_one(r'Ground area\s+' + NUMBER + r'\s+m²', a))
    plane = float(_one(r'Height Working plane\s+' + NUMBER + r'\s+m\b', a))
    height = float(_one(r'Clearance height\s+' + NUMBER + r'\s+m\b', a))
    em, plane_id = _one(r'^Working plane\s+Ēperpendicular\s+' + NUMBER + r'\s+lx\b[^\n]*?\s+(WP\d+)\s*$', b)
    uo, uniformity_id = _one(r'^Uo \(g1\)\s+' + NUMBER + r'\b[^\n]*?\s+(WP\d+)\s*$', b)
    if plane_id != uniformity_id:
        raise ValueError('Illuminance and uniformity refer to different calculation surfaces')
    illuminance, uniformity = float(em), float(uo)
    lpd = float(_one(r'^Space Lighting power density\s+' + NUMBER + r'\s+W/m²\s', b))
    if (not all(math.isfinite(v) for v in (area, plane, height, illuminance, uniformity, lpd))
            or area <= 0 or not 0 <= plane < height or not 0 <= uniformity <= 1):
        raise ValueError('Invalid physical values in summary')
    return {'room_scene_header': headers[0], 'area_m2': area,
            'height_m': height, 'workplane_m': plane,
            'measurements': [
                {'metric': 'average_perpendicular_illuminance', 'value': illuminance,
                 'unit': 'lx', 'calculation_surface': plane_id, 'page': 2},
                {'metric': 'uniformity_u0', 'value': uniformity,
                 'unit': '1', 'calculation_surface': plane_id, 'page': 2},
                {'metric': 'lighting_power_density', 'value': lpd,
                 'unit': 'W/m2', 'calculation_surface': 'space', 'page': 2}]}


def parse_report_pages(pages: list[str]) -> dict:
    """Select exactly one adjacent two-page Summary; reject multi-room ambiguity."""
    selected = [(i, text) for i, text in enumerate(pages)
                if re.search(SUMMARY_HEADER, text, re.MULTILINE)]
    if len(selected) != 2 or selected[1][0] != selected[0][0] + 1:
        raise ValueError('Expected exactly one adjacent two-page room Summary in report')
    result = parse_summary_pages([text for _, text in selected])
    for row in result['measurements']:
        row['page'] = selected[row['page'] - 1][0] + 1
    result['summary_pages'] = [index + 1 for index, _ in selected]
    result['document_pages'] = len(pages)
    return result


def parse_report_summaries(pages: list[str]) -> dict:
    """Keep recognized adjacent room/scene summaries separate; never aggregate them."""
    selected = [(i, text) for i, text in enumerate(pages)
                if re.search(SUMMARY_HEADER, text, re.MULTILINE)]
    if not selected or len(selected) % 2:
        raise ValueError('Expected complete adjacent two-page English room summaries')
    summaries, seen = [], set()
    for offset in range(0, len(selected), 2):
        pair = selected[offset:offset+2]
        if pair[1][0] != pair[0][0] + 1:
            raise ValueError('Summary pages are not adjacent')
        summary = parse_summary_pages([text for _, text in pair])
        header = summary['room_scene_header']
        if header in seen:
            raise ValueError('Duplicate room/scene summary; report identity is ambiguous')
        seen.add(header)
        identity = hashlib.sha256(header.encode('utf-8')).hexdigest()
        summary['summary_id'] = identity
        summary['summary_pages'] = [i+1 for i,_ in pair]
        for row in summary['measurements']:
            row['page'] = pair[row['page']-1][0]+1
            row['summary_id'] = identity
            row['room_scene_header'] = header
        summaries.append(summary)
    return {'summaries': summaries, 'summary_count': len(summaries), 'document_pages': len(pages),
            'complete_project_coverage_verified': False}


def read_report_pdf(path: str) -> dict:
    """Read supported room/scene summary pairs without mixing their measurements.

    Recognized English summary pages only; not proof every room/scene is present.
    Duplicate room/scene headers and incomplete pairs are rejected.
    """
    source = Path(path).resolve(strict=True)
    if source.suffix.lower() != '.pdf':
        raise ValueError('Expected a PDF report')
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            pages = [page.extract_text() or '' for page in pdf.pages]
    except (PSException, PdfminerException) as exc:
        raise ValueError(f'Unreadable or unsupported PDF: {type(exc).__name__}') from exc
    result = parse_report_summaries(pages)
    for summary in result['summaries']:
        for row in summary['measurements']:
            row['evidence'] = f'{source}#page={row["page"]};sha256={digest}'
    result.update(schema='dialux-agent/report-results/v1', source=str(source), sha256=digest,
                  compliance_status='not_evaluated', warnings=[
                      'Only recognized English two-page summaries are parsed; project coverage is unverified.',
                      'Room/scene identities are normalized report headers, not native project object IDs.',
                      'Values are neither authenticated nor a compliance conclusion; no room or scene aggregation performed.'])
    return result


def read_summary_pdf(path: str) -> dict:
    """Extract one tested English room Summary, including inside a full PDF report."""
    source = Path(path).resolve(strict=True)
    if source.suffix.lower() != '.pdf':
        raise ValueError('Expected a PDF report')
    # Parse precisely the bytes whose hash is attached to measurements.
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    try:
        with pdfplumber.open(BytesIO(data)) as pdf:
            pages = [page.extract_text() or '' for page in pdf.pages]
    except (PSException, PdfminerException) as exc:
        raise ValueError(f'Unreadable or unsupported PDF: {type(exc).__name__}') from exc
    result = parse_report_pages(pages)
    for row in result['measurements']:
        row['evidence'] = f'{source}#page={row["page"]};sha256={digest}'
    result.update(schema='dialux-agent/summary-results/v1', source=str(source), sha256=digest,
                  compliance_status='not_evaluated',
                  warnings=['Extracted report values only; no authentication of the report or design compliance.',
                            'Only one adjacent English two-page room Summary is supported; multiple summaries are refused.',
                            'Report targets and DIN energy estimates are not adopted Hong Kong criteria.'])
    return result
