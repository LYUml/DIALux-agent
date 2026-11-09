"""Explicit, source-bound CAD polygon extraction; no room inference."""
import hashlib
import math
from pathlib import Path
import ezdxf
if __package__:
    from .layout import number, polygon
else:
    from layout import number, polygon


def drawing_extract_boundary(path: str, handle: str, expected_sha256: str,
                             storey_origin_m: list[float], storey_rotation_deg: float) -> dict:
    """Extract one explicitly selected closed straight modelspace LWPOLYLINE.

    Requires the current DXF byte hash and an explicit drawing-WCS to storey
    transform. Origin is XY in drawing WCS metres; rotation is the storey's
    counterclockwise axis orientation relative to drawing WCS. Curves, widths,
    non-default extrusion, open paths and block/paperspace entities are rejected.
    Entity selection does not prove it represents the actual room boundary.
    """
    source=Path(path).resolve(strict=True)
    if source.suffix.lower()!='.dxf': raise ValueError('Convert DWG to DXF before boundary extraction')
    data=source.read_bytes()
    digest=hashlib.sha256(data).hexdigest()
    if not isinstance(expected_sha256,str) or expected_sha256!=digest:
        raise ValueError('DXF hash differs from explicitly selected source')
    if not isinstance(handle,str) or not handle or any(c not in '0123456789abcdefABCDEF' for c in handle):
        raise ValueError('Expected an explicit hexadecimal entity handle')
    if not isinstance(storey_origin_m,list) or len(storey_origin_m)!=2:
        raise ValueError('Explicit XY storey origin in drawing WCS metres required')
    ox,oy=[number(x,'storey_origin_m') for x in storey_origin_m]
    angle=number(storey_rotation_deg,'storey_rotation_deg')
    doc=ezdxf.readfile(source)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=digest:
        raise ValueError('Source changed during extraction')
    # Supported INSUNITS values: inch, foot, millimetre, centimetre, metre.
    scales={1:.0254,2:.3048,4:.001,5:.01,6:1.0}
    unit=int(doc.units)
    if unit not in scales: raise ValueError('Unsupported or unspecified INSUNITS; no unit inference permitted')
    scale=scales[unit]
    matches=[e for e in doc.modelspace() if e.dxf.handle.upper()==handle.upper()]
    if len(matches)!=1 or matches[0].dxftype()!='LWPOLYLINE':
        raise ValueError('Expected one modelspace LWPOLYLINE at the selected handle')
    entity=matches[0]
    if not entity.closed: raise ValueError('Selected polyline is not closed')
    if tuple(entity.dxf.extrusion)!=(0,0,1): raise ValueError('Non-default OCS extrusion is not supported')
    if entity.dxf.get('const_width',0)!=0: raise ValueError('Wide polyline has ambiguous boundary edges')
    raw=list(entity.get_points('xyseb'))
    if len(raw)>10000: raise ValueError('Selected boundary exceeds 10000 vertices')
    for row in raw:
        for value in row: number(value,'polyline coordinate')
        if row[2] or row[3]: raise ValueError('Variable-width polyline has ambiguous boundary edges')
        if row[4]: raise ValueError('Curved bulge segments require an explicit curve extraction policy')
    elevation=number(entity.dxf.elevation,'elevation')*scale
    points=[[float(row[0])*scale,float(row[1])*scale] for row in raw]
    world=polygon(points,'selected boundary')
    cosine,sine=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    contour=[[(x-ox)*cosine+(y-oy)*sine,-(x-ox)*sine+(y-oy)*cosine] for x,y in points]
    transformed=polygon(contour,'transformed boundary')
    if not all(math.isfinite(v) for v in (world.area,world.length,transformed.area,transformed.length)):
        raise ValueError('Boundary area or perimeter exceeds finite numeric range')
    return {'schema':'dialux-agent/cad-boundary/v1','source':str(source),'sha256':digest,
            'entity_handle':entity.dxf.handle,'layer':entity.dxf.layer,'entity_type':'LWPOLYLINE',
            'insunits':unit,'source_to_metre_scale':scale,'units':'m','coordinate_frame':'active_storey',
            'transform':{'storey_origin_m':[ox,oy],'storey_rotation_deg':angle,
                         'definition':'storey_xy = rotation(-angle) * (drawing_wcs_metres - origin)'},
            'contour':contour,'drawing_wcs_contour_m':points,'drawing_wcs_elevation_m':elevation,
            'area_m2':transformed.area,'perimeter_m':transformed.length,'vertex_count':len(contour),
            'selected_entity_geometry_extracted':True,'semantic_room_boundary_verified':False,
            'native_dialux_geometry_verified':False,
            'warning':'Caller selected this entity and coordinate transform. No boundary inference, curve approximation, hole discovery or native room audit performed.'}
