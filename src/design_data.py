"""Shared drawing layout derived from explicit native observation evidence."""
import re
if __package__:
    from .verification import verify_room_addition, digest
else:
    from verification import verify_room_addition, digest


def observed_layout(spec: dict, observed: dict, fixture_ids: list[str]) -> dict:
    """Bind caller-assigned drawing IDs to supplied rounded native coordinates.

    IDs correspond exactly to observation order, not a persistent native identity.
    The explicit specimen boundary, product and physical dimensions are supplied
    assumptions. No coordinate snapping or grid regeneration is performed.
    """
    if not isinstance(spec,dict) or spec.get('units')!='m' or spec.get('coordinate_frame')!='active_storey':
        raise ValueError('Explicit metre-unit active-storey drawing specification required')
    fixture=spec.get('fixture')
    if not isinstance(fixture,dict) or not isinstance(fixture.get('product_id'),str) or not fixture['product_id'].strip():
        raise ValueError('Explicit supplied product identifier required')
    assumptions=spec.get('assumptions')
    if not isinstance(assumptions,list) or not assumptions or any(not isinstance(a,str) or not a.strip() for a in assumptions):
        raise ValueError('Document source/dimension assumptions')
    if not isinstance(fixture_ids,list) or not fixture_ids or any(not isinstance(i,str) or not re.fullmatch(r'L[0-9]{1,12}',i) for i in fixture_ids) or len(set(fixture_ids))!=len(fixture_ids):
        raise ValueError('Drawing fixture IDs must be unique L-prefixed numeric identifiers')
    check=verify_room_addition({'units':'m','coordinate_frame':'active_storey',
        'room_polygon':spec.get('contour'),'exclusions':spec.get('exclusions',[]),
        'fixture_width_m':fixture.get('width_m'),'fixture_depth_m':fixture.get('depth_m'),
        'mounting_height_m':fixture.get('mounting_height_m'),'clearance_m':spec.get('clearance_m')},observed,[],[])
    if len(fixture_ids)!=len(observed['fixtures']): raise ValueError('One drawing ID per observed fixture required')
    records=[]
    for index,(identity,source) in enumerate(zip(fixture_ids,observed['fixtures'])):
        records.append({'id':identity,'position_m':list(source['position_m']),
            'rotation_deg':source['rotation_deg'][2], 'observed_index':index,
            'observed_runtime_id':source.get('runtime_id'), 'observed_name':source.get('name')})
    return {'schema':'dialux-agent/layout/v1','units':'m','coordinate_frame':'active_storey',
            'origin':'supplied_native_observations','fixtures':records,'fixture_count':len(records),
            'input_sha256':digest(spec),'observations_sha256':digest(observed),
            'source_group_id':observed['group_id'],'assumptions':assumptions,'geometry_check':check,
            'photometry_identity_verified':False,'simulation_verified':False,
            'warning':'Drawing IDs are explicitly assigned to this observation snapshot. Coordinates are not authenticated; source dimensions/product and boundary remain supplied assumptions.'}
