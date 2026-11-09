"""Explicit native working-plane extrema, without deriving minima from ratios."""
import hashlib
from io import BytesIO
import math
from pathlib import Path
import re
import pdfplumber

NUMBER=r'\d+(?:\.\d+)?'


def parse_workplane_page(text: str, expected_header: str, expected_surface: str) -> dict:
    if not isinstance(expected_header,str) or not expected_header.strip() or not isinstance(expected_surface,str) or not re.fullmatch(r'WP\d+',expected_surface):
        raise ValueError('Exact room/scene header and WP surface ID required')
    lines=text.splitlines()
    headings=[i for i,line in enumerate(lines) if line=='Calculation objects' or re.fullmatch(r'Working plane \(.+\)',line)]
    if len(headings)!=1 or ' '.join(lines[1:headings[0]])!=expected_header:
        raise ValueError('Working-plane page room/scene identity differs')
    if 'Properties \u0112 Emin Emax Uo (g1) g2 Index' not in lines:
        raise ValueError('Unsupported working-plane table columns')
    row_pattern=(r'^Working plane \(([^\n]+)\) ('+NUMBER+r') lx ('+NUMBER+r') lx ('+NUMBER+
                 r') lx ('+NUMBER+r'|-) ('+NUMBER+r'|-) ('+re.escape(expected_surface)+r')$')
    rows=re.findall(row_pattern,text,re.MULTILINE)
    if len(rows)!=1: raise ValueError('Missing or ambiguous selected working-plane row')
    basis=re.findall(r'^Perpendicular illuminance \(adaptive\)(?: .*)?$',text,re.MULTILINE)
    heights=re.findall(r'^Height: ('+NUMBER+r') m, Wall zone: ('+NUMBER+r') m$',text,re.MULTILINE)
    if len(basis)!=1 or len(heights)!=1: raise ValueError('Missing or ambiguous plane type/height evidence')
    name,average,minimum,maximum,u0,g2,surface=rows[0]
    average,minimum,maximum=map(float,(average,minimum,maximum))
    height,margin=map(float,heights[0])
    values=[average,minimum,maximum,height,margin]+[float(v) for v in (u0,g2) if v!='-']
    if not all(math.isfinite(v) for v in values) or not 0<=minimum<=average<=maximum:
        raise ValueError('Invalid reported working-plane extrema')
    if any(v!='-' and not 0<=float(v)<=1 for v in (u0,g2)):
        raise ValueError('Invalid reported working-plane uniformity')
    measures=[{'metric':metric,'value':value,'unit':'lx','calculation_surface':surface}
              for metric,value in [('average_perpendicular_illuminance',average),('minimum_illuminance',minimum),('maximum_illuminance',maximum)]]
    if u0!='-': measures.append({'metric':'uniformity_u0','value':float(u0),'unit':'1','calculation_surface':surface})
    return {'room_scene_header':expected_header,'working_plane_name':name,'calculation_surface':surface,
            'height_m':height,'wall_zone_m':margin,'measurement_basis':'perpendicular_illuminance_adaptive',
            'measurements':measures,'unavailable_uniformity':u0=='-',
            'source_row':rows[0],'minimum_is_direct_report_value':True,
            'task_surface_applicability_verified':False}


def read_workplane_pdf(path: str, page: int, expected_header: str, expected_surface: str) -> dict:
    """Read one explicitly selected native English working-plane table page.

    Retains direct Emin/Emax and source scope. Does not adopt any task criteria,
    authenticate the report or infer that a working plane is a desk-work surface.
    """
    if type(page) is not int or page<1: raise ValueError('Positive one-based page number required')
    source=Path(path).resolve(strict=True)
    if source.suffix.lower()!='.pdf': raise ValueError('Expected PDF report')
    data=source.read_bytes();digest=hashlib.sha256(data).hexdigest()
    with pdfplumber.open(BytesIO(data)) as doc:
        if page>len(doc.pages): raise ValueError('Selected page exceeds report')
        result=parse_workplane_page(doc.pages[page-1].extract_text() or '',expected_header,expected_surface)
    for measure in result['measurements']:
        measure.update(page=page,evidence=f'{source}#page={page};sha256={digest}')
    return {**result,'schema':'dialux-agent/workplane-results/v1','source':str(source),'sha256':digest,
            'page':page,'compliance_status':'not_evaluated','fresh_simulation_verified':False,
            'warning':'Direct reported extrema on the selected surface. Task applicability, surface orientation and operating conditions need separate evidence.'}
