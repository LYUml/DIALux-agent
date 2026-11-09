"""Observed mixed-product CAD using the shared renderer and report linker."""
import copy
from shapely.geometry import box
from shapely.affinity import rotate, translate
if __package__:
    from .design_data import observed_layout
    from .mixed_schedule import build_mixed_luminaire_schedule
    from .verification import digest
    from .cad import _write_layout_dxf
else:
    from design_data import observed_layout
    from mixed_schedule import build_mixed_luminaire_schedule
    from verification import digest
    from cad import _write_layout_dxf


def export_mixed_scheduled_layout_dxf(spec: dict, groups: list[dict], report_request: dict,
                                      alignment: dict, output: str) -> dict:
    """Export explicit per-group footprints, observed positions and report tables.

    Synthetic tool-test output; physical dimensions and group mapping are supplied
    assumptions. Real-source files are not modified. Native save/plot are separate.
    """
    if not isinstance(spec,dict) or 'fixture' in spec:
        raise ValueError('Mixed drawing uses common room spec and per-group fixture definitions')
    if not isinstance(groups,list) or not 1<=len(groups)<=100:
        raise ValueError('Expected 1 to 100 product groups')
    required={'report_group','fixture','observed','fixture_ids'}
    if any(not isinstance(g,dict) or set(g)!=required for g in groups):
        raise ValueError('Each group requires report_group, fixture, observed and fixture_ids')
    names=[g['report_group'] for g in groups]
    if any(not isinstance(n,str) or not n.strip() for n in names) or len(set(names))!=len(names):
        raise ValueError('Unique report group names required')
    keys={name:f'DIALUX_AGENT_TYPE_{i:02d}' for i,name in enumerate(sorted(names),1)}
    catalog={};observed_groups=[];fixtures=[];bodies=[]
    for group in groups:
        group_spec=copy.deepcopy(spec);group_spec['fixture']=copy.deepcopy(group['fixture'])
        layout=observed_layout(group_spec,group['observed'],group['fixture_ids'])
        if len(fixtures)+layout['fixture_count']>2000:
            raise ValueError('Mixed drawing exceeds 2000 fixtures')
        name=group['report_group'];key=keys[name];catalog[key]=group_spec['fixture']
        observed_groups.append({'report_group':name,'layout':layout})
        width,depth=(catalog[key][k] for k in ('width_m','depth_m'))
        for fixture in layout['fixtures']:
            x,y=fixture['position_m'][:2]
            body=translate(rotate(box(-width/2,-depth/2,width/2,depth/2),fixture['rotation_deg'],origin=(0,0)),x,y)
            if any(body.intersection(other).area>1e-12 for other in bodies):
                raise ValueError('Mixed fixture footprints overlap across supplied groups')
            bodies.append(body);fixtures.append({**fixture,'symbol_key':key})
    schedule=build_mixed_luminaire_schedule(observed_groups,report_request,alignment)
    for group in schedule['groups']:
        group['symbol_key']=keys[group['report_group']]
    layout={'schema':'dialux-agent/layout/v1','origin':'supplied_native_observations',
            'units':'m','coordinate_frame':'active_storey','fixtures':fixtures,'fixture_count':len(fixtures),
            'input_sha256':digest({'spec':spec,'groups':groups}),
            'observations_sha256':digest([g['observed'] for g in groups]),
            'assumptions':spec.get('assumptions'),'photometry_identity_verified':False,'simulation_verified':False}
    result=_write_layout_dxf(spec,output,layout,schedule=schedule,fixture_catalog=catalog)
    result.update(observed_layout=layout,schedule=schedule,fixture_catalog=catalog,
                  product_symbol_mapping=keys,manufacturer_dimensions_verified=False)
    return result
