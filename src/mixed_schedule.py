"""Mixed report-backed schedules reusing the single-product spatial linker."""
import math
if __package__:
    from .report_layout import read_report_arrangements
    from .schedule import _build_luminaire_schedule
    from .verification import digest
else:
    from report_layout import read_report_arrangements
    from schedule import _build_luminaire_schedule
    from verification import digest


def build_mixed_luminaire_schedule(groups: list[dict], report_request: dict, alignment: dict) -> dict:
    """Associate explicitly mapped observed groups with native report products.

    Does not authenticate group mapping, native photometry, dimensions or BEC load.
    """
    if not isinstance(groups,list) or not 1<=len(groups)<=100:
        raise ValueError('Expected 1 to 100 explicit observed groups')
    if any(not isinstance(g,dict) or set(g)!={'report_group','layout'} for g in groups):
        raise ValueError('Each group requires report_group and observed layout')
    names=[g['report_group'] for g in groups]
    if any(not isinstance(n,str) or not n.strip() for n in names) or len(set(names))!=len(names):
        raise ValueError('Unique explicit report group names required')
    if not isinstance(report_request,dict) or set(report_request)!={'path','sections','expected_count','expected_header'}:
        raise ValueError('Explicit arrangement report request required')
    report=read_report_arrangements(**report_request)
    products={p['group_name']:p for p in report['products']}
    if set(products)!=set(names):
        raise ValueError('Observed and report group sets differ')
    rows=report['fixtures']
    # A positional association is ambiguous even if duplicate points belong to
    # different supplied groups. Refuse instead of trusting the user's partition.
    for i,row in enumerate(rows):
        if any(max(abs(a-b) for a,b in zip(row['position_m'],other['position_m']))<=.001 for other in rows[i+1:]):
            raise ValueError('Report positions ambiguous across groups')
    schedules=[];drawing_ids=set();source_groups=set()
    for group in groups:
        layout=group['layout'];name=group['report_group']
        if not isinstance(layout,dict): raise ValueError('Observed layout required')
        source=layout.get('source_group_id')
        if not isinstance(source,str) or not source.strip() or source in source_groups:
            raise ValueError('Unique observation source groups required')
        source_groups.add(source)
        section=next(s for s in report_request['sections'] if s['expected_group']==name)
        spec={'path':report['path'],'first_page':section['first_page'],'last_page':section['last_page'],
              'expected_header':report['room_header']}
        selected=[r for r in rows if r['group_name']==name]
        adapted={**report,'fixtures':selected,'fixture_count':len(selected),'product':products[name]}
        schedule=_build_luminaire_schedule(layout,spec,alignment,adapted)
        for fixture in schedule['fixtures']:
            if fixture['fixture_id'] in drawing_ids: raise ValueError('Duplicate drawing ID across groups')
            drawing_ids.add(fixture['fixture_id'])
        schedules.append({'report_group':name,'source_group_id':source,'schedule':schedule})
    fixtures=[{**f,'report_group':g['report_group'],'article_number':g['schedule']['product']['article_number']}
              for g in schedules for f in g['schedule']['fixtures']]
    power=sum(g['schedule']['total_reported_fixture_power_w'] for g in schedules)
    if not math.isfinite(power): raise ValueError('Nonfinite mixed power total')
    return {'schema':'dialux-agent/mixed-luminaire-schedule/v1','groups':schedules,
            'fixtures':fixtures,'quantity':len(fixtures),'total_reported_fixture_power_w':power,
            'report_source':report['path'],'report_sha256':report['sha256'],
            'source_groups_sha256':digest(groups),'alignment':alignment,'units':'m',
            'coordinate_frame':'active_storey','position_correspondence_verified':True,
            'group_mapping_authenticated':False,'photometry_identity_verified':False,
            'manufacturer_dimensions_verified':False,'whole_project_verified':False,
            'warning':'Explicit group mapping and unique spatial correspondence only. Quantity times reported power is not verified BEC fixed-lighting load.'}
