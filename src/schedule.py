"""Position-linked luminaire schedules from native observations and PDF evidence."""
import math
import re
if __package__:
    from .layout import number
    from .verification import digest
    from .report_layout import read_report_layout
else:
    from layout import number
    from verification import digest
    from report_layout import read_report_layout


def build_luminaire_schedule(layout: dict, report_spec: dict, alignment: dict) -> dict:
    """Link observed drawing IDs to one complete report product section spatially.

    Alignment is explicitly supplied, not inferred. Report product association
    does not authenticate the live project or prove manufacturer dimensions.
    """
    if (layout.get('schema')!='dialux-agent/layout/v1' or layout.get('origin')!='supplied_native_observations'
            or layout.get('units')!='m' or layout.get('coordinate_frame')!='active_storey'):
        raise ValueError('Expected an observed active-storey metre layout')
    fixtures=layout.get('fixtures')
    if not isinstance(fixtures,list) or not 1<=len(fixtures)<=2000 or layout.get('fixture_count')!=len(fixtures):
        raise ValueError('Invalid observed fixture count')
    ids=[f.get('id') for f in fixtures]
    if any(not isinstance(i,str) or not re.fullmatch(r'L\d{1,12}',i) for i in ids) or len(set(ids))!=len(ids):
        raise ValueError('Unique drawing fixture IDs required')
    if not isinstance(layout.get('observations_sha256'),str) or not re.fullmatch(r'[0-9a-f]{64}',layout['observations_sha256']):
        raise ValueError('Observed snapshot hash required')
    if not isinstance(report_spec,dict) or set(report_spec)!={'path','first_page','last_page','expected_header'}:
        raise ValueError('Explicit report path, page range and room header required')
    if not isinstance(alignment,dict) or set(alignment)!={'translation_m','rotation_deg','evidence'}:
        raise ValueError('Explicit report-to-storey alignment required')
    if not isinstance(alignment['evidence'],str) or not alignment['evidence'].strip():
        raise ValueError('Document the coordinate correspondence evidence/assumption')
    def vector(v):
        if not isinstance(v,list) or len(v)!=3: raise ValueError('Expected XYZ vector')
        return [number(x,'coordinate') for x in v]
    translation=vector(alignment['translation_m'])
    angle=math.radians(number(alignment['rotation_deg'],'alignment rotation'))
    c,s=math.cos(angle),math.sin(angle)
    positions=[vector(f.get('position_m')) for f in fixtures]
    for f in fixtures: number(f.get('rotation_deg'),'observed rotation')
    report=read_report_layout(**report_spec,expected_count=len(fixtures))
    transformed=[]
    for row in report['fixtures']:
        x,y,z=vector(row['position_m'])
        transformed.append([c*x-s*y+translation[0],s*x+c*y+translation[1],z+translation[2]])
    used=set();records=[]
    for fixture,position in zip(fixtures,positions):
        matches=[i for i,point in enumerate(transformed) if max(abs(a-b) for a,b in zip(position,point))<=.001]
        if len(matches)!=1 or matches[0] in used:
            raise ValueError('Report position unmatched or ambiguous for '+fixture['id'])
        index=matches[0];used.add(index);row=report['fixtures'][index]
        records.append({'fixture_id':fixture['id'],'position_m':fixture['position_m'],
            'rotation_deg':fixture['rotation_deg'],'observed_runtime_id':fixture.get('observed_runtime_id'),
            'report_luminaire_number':row['report_luminaire_number'],'report_page':row['page']})
    product=report['product']
    power=product['power_w']*len(records)
    if not math.isfinite(power): raise ValueError('Invalid total reported fixture power')
    return {'schema':'dialux-agent/luminaire-schedule/v1','quantity':len(records),'product':product,
            'total_reported_fixture_power_w':power,'power_basis':'quantity times reported per-luminaire power; not verified BEC fixed-lighting power',
            'fixtures':records,'coordinate_frame':'active_storey','units':'m','alignment':alignment,
            'source_layout_sha256':digest(layout),'observations_sha256':layout['observations_sha256'],
            'report_source':report['path'],'report_sha256':report['sha256'],'report_room_header':report['room_header'],
            'position_correspondence_verified':True,'alignment_independently_verified':False,
            'photometry_identity_verified':False,'manufacturer_dimensions_verified':False,
            'warning':'One report product section linked to supplied observations by unique positions under the stated transform. Not authenticated live product identity, task compliance or a complete electrical load schedule.'}
