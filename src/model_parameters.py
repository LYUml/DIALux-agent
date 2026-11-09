"""Read explicitly scoped model parameters from supported English summaries."""
import hashlib
from io import BytesIO
import math
from pathlib import Path
import pdfplumber

if __package__:
    from .results import parse_report_summaries, _one, NUMBER
else:
    from results import parse_report_summaries, _one, NUMBER


def parse_model_parameters(text: str) -> dict:
    patterns={
        'ceiling_reflectance_pct':r'Reflection factors Ceiling:\s*'+NUMBER+r'\s*%',
        'wall_reflectance_pct':r'Walls:\s*'+NUMBER+r'\s*%',
        'floor_reflectance_pct':r'Floor:\s*'+NUMBER+r'\s*%',
        'maintenance_factor':r'Maintenance factor\s+'+NUMBER+r'\s+\(fixed\)',
        'mounting_height_m':r'Mounting height\s+'+NUMBER+r'\s+m\b',
        'wall_zone_m':r'Wall zone Working plane\s+'+NUMBER+r'\s+m\b',
    }
    values={key:float(_one(pattern,text)) for key,pattern in patterns.items()}
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError('Nonfinite reported model parameter')
    if any(not 0<=values[key]<=100 for key in patterns if key.endswith('_pct')):
        raise ValueError('Reported reflectance outside 0 to 100 percent')
    if not 0<values['maintenance_factor']<=1 or values['mounting_height_m']<=0 or values['wall_zone_m']<0:
        raise ValueError('Invalid reported maintenance factor or height/zone')
    return values


def read_model_parameters(path: str, summary_id: str) -> dict:
    """Read one exact summary ID; no inference of per-surface or live settings.

    Supports numeric reflection factors and explicitly fixed maintenance factor.
    Use read_report_pdf to discover IDs. Does not establish fresh calculation.
    """
    if not isinstance(summary_id,str) or not summary_id:
        raise ValueError('Explicit room/scene summary_id required')
    source=Path(path).resolve(strict=True);data=source.read_bytes()
    if source.suffix.lower()!='.pdf': raise ValueError('Expected PDF report')
    try:
        with pdfplumber.open(BytesIO(data)) as document:
            pages=[page.extract_text() or '' for page in document.pages]
    except Exception as exc:
        raise ValueError('Unreadable model-parameter PDF') from exc
    summaries=parse_report_summaries(pages)['summaries']
    matches=[s for s in summaries if s['summary_id']==summary_id]
    if len(matches)!=1: raise ValueError('Exact room/scene summary not found')
    summary=matches[0];page=summary['summary_pages'][0]
    values=parse_model_parameters(pages[page-1])
    values.update({key:summary[key] for key in ('area_m2','height_m','workplane_m')})
    return {'schema':'dialux-agent/reported-model-parameters/v1','report':str(source),
            'report_sha256':hashlib.sha256(data).hexdigest(),'summary_id':summary_id,
            'room_scene_header':summary['room_scene_header'],'page':page,'parameters':values,
            'maintenance_mode':'fixed','per_surface_materials_verified':False,
            'live_model_verified':False,'fresh_calculation_verified':False,
            'warning':'Reported rounded summary values only; not individual surface materials or current native settings.'}
