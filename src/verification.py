"""Compare supplied room-placement evidence; never authenticate a native project."""
import hashlib
import json
if __package__:
    from .layout import number, polygon, verify_observed_layout
else:
    from layout import number, polygon, verify_observed_layout
from shapely.geometry import box
from shapely import affinity
from shapely.strtree import STRtree


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


def validate_observation(observed):
    if (not isinstance(observed,dict) or observed.get('operation')!='read_group_fixtures'
            or observed.get('coordinate_frame')!='active_storey'
            or observed.get('offset',0)!=0 or observed.get('next_offset') is not None):
        raise ValueError('Expected fully paged active-storey fixture observations')
    fixtures=observed.get('fixtures')
    if not isinstance(fixtures,list) or not 1<=len(fixtures)<=2000 or observed.get('observed_count')!=len(fixtures):
        raise ValueError('Invalid observed fixture count')
    if not isinstance(observed.get('group_id'),str) or not observed['group_id']:
        raise ValueError('Expected explicit group identity')
    for fixture in fixtures:
        for key in ('position_m','rotation_deg'):
            if not isinstance(fixture.get(key),list) or len(fixture[key])!=3:
                raise ValueError('Expected three-component fixture geometry')
            for value in fixture[key]: number(value,key)
        if any(abs((v+180)%360-180)>.05 for v in fixture['rotation_deg'][:2]):
            raise ValueError('Only horizontal fixture envelopes are supported')
    return fixtures


def verify_room_addition(spec: dict, added: dict, before: list[dict], after: list[dict]) -> dict:
    """Check new fixture envelopes and preserve supplied previous-group geometry.

    Spec requires explicit metre units, active_storey frame, room_polygon,
    fixture_width_m, fixture_depth_m, mounting_height_m and clearance_m.
    Optional exclusions are XY polygons. Dimensions/boundaries are supplied
    assumptions, not native measurements. All previous groups must be supplied.
    Does not prove a complete project inventory or photometry identity.
    """
    if not isinstance(spec,dict) or spec.get('units')!='m' or spec.get('coordinate_frame')!='active_storey':
        raise ValueError('Explicit metre units and active_storey frame required')
    room=polygon(spec.get('room_polygon'),'room_polygon')
    width=number(spec.get('fixture_width_m'),'fixture_width_m')
    depth=number(spec.get('fixture_depth_m'),'fixture_depth_m')
    height=number(spec.get('mounting_height_m'),'mounting_height_m')
    clearance=number(spec.get('clearance_m'),'clearance_m')
    if min(width,depth)<=0 or height<0 or clearance<0:
        raise ValueError('Invalid fixture dimensions, mounting height or clearance')
    exclusions=spec.get('exclusions',[])
    if not isinstance(exclusions,list): raise ValueError('exclusions must be a list')
    obstacles=[polygon(p,'exclusion') for p in exclusions]
    fixtures=validate_observation(added)
    usable=room.buffer(-clearance) if clearance else room
    if usable.is_empty: raise ValueError('Clearance removes usable room')
    footprints=[]
    for index,fixture in enumerate(fixtures):
        x,y,z=fixture['position_m']
        if abs(z-height)>.001: raise ValueError(f'Unexpected mounting height at fixture {index}')
        footprint=affinity.rotate(box(-width/2,-depth/2,width/2,depth/2),fixture['rotation_deg'][2],origin=(0,0))
        footprint=affinity.translate(footprint,xoff=x,yoff=y)
        if not usable.covers(footprint) or any(footprint.intersects(o.buffer(clearance)) for o in obstacles):
            raise ValueError(f'Fixture {index} envelope violates room boundary or exclusion')
        footprints.append(footprint)
    index_tree=STRtree(footprints)
    for i, footprint in enumerate(footprints):
        for j in index_tree.query(footprint):
            if j>i and footprint.intersection(footprints[j]).area>1e-12:
                raise ValueError(f'Added fixture envelopes overlap: {i}, {j}')
    def groups(records):
        if not isinstance(records,list): raise ValueError('Previous group evidence must be a list')
        result={}
        for record in records:
            validate_observation(record)
            identity=record['group_id']
            if identity in result or identity==added['group_id']:
                raise ValueError('Duplicate or new group in preserved-group evidence')
            result[identity]=record
        return result
    old,new=groups(before),groups(after)
    if set(old)!=set(new): raise ValueError('Before/after group identities differ')
    preserved=[]
    for identity,record in old.items():
        plan={'schema':'dialux-agent/layout/v1','units':'m','coordinate_frame':'active_storey',
              'fixture_count':len(record['fixtures']), 'fixtures':[
                  {'id':str(i),'position_m':f['position_m'],'rotation_deg':f['rotation_deg'][2]}
                  for i,f in enumerate(record['fixtures'])]}
        comparison=verify_observed_layout(plan,new[identity])
        preserved.append({'group_id':identity,'comparison':comparison})
    return {'schema':'dialux-agent/room-addition-check/v1','added_count':len(fixtures),
            'supplied_room_envelopes_fit':True,'supplied_previous_groups_match':True,
            'preserved_groups':preserved,'whole_project_verified':False,
            'native_boundary_verified':False,'photometry_identity_verified':False,
            'evidence_sha256':{k:digest(v) for k,v in [('spec',spec),('added',added),('before',before),('after',after)]},
            'warning':'Checks supplied rounded observations and assumed dimensions only; no origin authentication, completeness or compliance claim.'}
