"""Geometry preflight for rigid movement of a fully observed native array."""
from shapely.affinity import rotate
from shapely.geometry import Point

if __package__:
    from .layout import number, plan_grid, verify_observed_layout
    from .verification import digest, validate_observation
else:
    from layout import number, plan_grid, verify_observed_layout
    from verification import digest, validate_observation


def plan_array_transform(spec: dict, observed: dict, arrangement: dict) -> dict:
    """Prove a supplied full-array observation fits a rigid target transform.

    No desktop action. Rejects count/spacing changes and independently displaced
    fixtures. Inputs are supplied evidence, not an authenticated live snapshot.
    """
    if not isinstance(observed,dict) or not isinstance(arrangement,dict):
        raise ValueError('Native observations must be objects')
    target = plan_grid(spec)
    count = target['fixture_count']
    if not 1 <= count <= 2000:
        raise ValueError('Rigid array planning requires 1 to 2000 target fixtures')
    if (arrangement.get('operation') != 'read_arrangement'
            or arrangement.get('coordinate_frame') != 'active_storey'
            or observed.get('operation') != 'read_group_fixtures'
            or observed.get('coordinate_frame') != 'active_storey'):
        raise ValueError('Expected active-storey native array and fixture observations')
    group = arrangement.get('tree_item_id')
    project = arrangement.get('path')
    if (not isinstance(group,str) or not group or not isinstance(project,str) or not project
            or observed.get('path') != project or observed.get('group_id') != group):
        raise ValueError('Array and fixture project/group identities differ')
    fixtures = observed.get('fixtures')
    if (not isinstance(fixtures,list) or any(not isinstance(f,dict) for f in fixtures)
            or len(fixtures) != count or type(observed.get('observed_count')) is not int
            or type(observed.get('container_node_count')) is not int or type(observed.get('offset')) is not int
            or observed.get('observed_count') != count
            or observed.get('container_node_count') != count or observed.get('offset') != 0
            or observed.get('next_offset') is not None or not isinstance(observed.get('inventory_token'),str)
            or not observed['inventory_token'].strip()):
        raise ValueError('A complete same-count group observation is required')
    identities = [f.get('runtime_id') for f in fixtures]
    if (any(not isinstance(i,list) or not i or any(type(v) is not int for v in i) for i in identities)
            or len({tuple(i) for i in identities}) != count):
        raise ValueError('Unique native fixture runtime identities required')
    validate_observation(observed)
    values = arrangement.get('display_values')
    keys = ('ElementCountX','ElementCountY','PolygonPosition_X','PolygonPosition_Y',
            'PolygonPosition_Z','ArrangementRotation_Z')
    if not isinstance(values,dict) or not set(keys) <= values.keys():
        raise ValueError('Native array count, centre and rotation fields are required')
    parsed = {}
    for key in keys:
        value = values[key]
        if not isinstance(value,str):
            raise ValueError('Expected native numeric display strings')
        try:
            parsed[key] = number(float(value),key)
        except (ValueError,OverflowError) as exc:
            raise ValueError('Invalid native array field: '+key) from exc
    nx,ny = parsed['ElementCountX'],parsed['ElementCountY']
    if nx != int(nx) or ny != int(ny) or nx < 1 or ny < 1 or nx*ny != count:
        raise ValueError('Only complete rectangular arrays with unchanged counts are supported')
    centre = [parsed['PolygonPosition_'+axis] for axis in 'XYZ']
    old_angle = parsed['ArrangementRotation_Z']
    new_angle = target['fixtures'][0]['rotation_deg']
    delta = (new_angle-old_angle+180)%360-180
    positions = [list(f['position_m']) for f in fixtures]
    for fixture in fixtures:
        if any(abs((a-b+180)%360-180)>.05 for a,b in zip(fixture['rotation_deg'],[0,0,old_angle])):
            raise ValueError('Individual fixture rotation differs from the native array')
    centroid = [sum(p[axis] for p in positions)/count for axis in range(3)]
    if any(abs(a-b)>.001 for a,b in zip(centre,centroid)):
        raise ValueError('Native centre differs from full fixture centroid')
    new_centre = [sum(f['position_m'][axis] for f in target['fixtures'])/count for axis in range(3)]
    predicted = []
    for fixture,position in zip(fixtures,positions):
        point = rotate(Point(*position[:2]),delta,origin=centre[:2])
        predicted.append({**fixture,'position_m':[
            point.x+new_centre[0]-centre[0], point.y+new_centre[1]-centre[1],
            position[2]+new_centre[2]-centre[2]],'rotation_deg':[0,0,new_angle]})
    match = verify_observed_layout(target,{**observed,'fixtures':predicted})
    return {'schema':'dialux-agent/array-transform-plan/v1','project':project,'group_id':group,
            'layout':target,'before_display_values':dict(values),
            'requested_values':dict(zip(('PolygonPosition_X','PolygonPosition_Y','PolygonPosition_Z',
                                         'ArrangementRotation_Z'),[*new_centre,new_angle])),
            'rotation_delta_deg':delta,'predicted_geometry':match,
            'observations_sha256':digest(observed),'arrangement_sha256':digest(arrangement),
            'native_mutation_verified':False,'source_authenticity_verified':False,
            'warning':'Geometry-only rigid-transform preflight. Recheck native fields before editing, then independently read every fixture and verify calculation/persistence.'}
