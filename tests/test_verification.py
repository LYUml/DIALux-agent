from copy import deepcopy
import pytest
from src.verification import verify_room_addition


def observation(group='new', x=2, y=2):
    return {'operation':'read_group_fixtures','coordinate_frame':'active_storey',
            'group_id':group,'observed_count':1,'offset':0,'next_offset':None,
            'fixtures':[{'position_m':[x,y,3],'rotation_deg':[0,0,0]}]}


@pytest.fixture
def spec():
    return {'units':'m','coordinate_frame':'active_storey','room_polygon':[[0,0],[4,0],[4,4],[0,4]],
            'fixture_width_m':1,'fixture_depth_m':1,'mounting_height_m':3,'clearance_m':0}


def test_checks_envelopes_and_preserves_scoped_groups(spec):
    old=observation('old',8,2)
    result=verify_room_addition(spec,observation(),[old],[deepcopy(old)])
    assert result['added_count']==1
    assert result['preserved_groups'][0]['comparison']['matched_count']==1
    assert not result['whole_project_verified']
    assert not result['native_boundary_verified']
    assert len(result['evidence_sha256']['spec'])==64


@pytest.mark.parametrize('kind',['edge','rotation','exclusion','height','clearance','tilt','partial','nan'])
def test_bad_new_placement_cannot_pass(spec,kind):
    new=observation()
    if kind=='edge': new['fixtures'][0]['position_m'][0]=.1
    if kind=='rotation':
        new['fixtures'][0]['position_m'][0]=.6
        new['fixtures'][0]['rotation_deg'][2]=45
    if kind=='exclusion': spec['exclusions']=[[[1.9,1.9],[2.1,1.9],[2.1,2.1],[1.9,2.1]]]
    if kind=='height': new['fixtures'][0]['position_m'][2]=2.9
    if kind=='clearance': spec['clearance_m']=2
    if kind=='tilt': new['fixtures'][0]['rotation_deg'][0]=20
    if kind=='partial': new['next_offset']=4
    if kind=='nan': new['fixtures'][0]['position_m'][0]=float('nan')
    with pytest.raises(ValueError): verify_room_addition(spec,new,[],[])


@pytest.mark.parametrize('kind',['movement','rotation','removed_group','duplicate','new_in_old'])
def test_unexpected_previous_group_change_cannot_pass(spec,kind):
    before=[observation('old',8,2)]
    after=deepcopy(before)
    if kind=='movement': after[0]['fixtures'][0]['position_m'][0]+=.01
    if kind=='rotation': after[0]['fixtures'][0]['rotation_deg'][2]=90
    if kind=='removed_group': after=[]
    if kind=='duplicate': before+=deepcopy(before)
    if kind=='new_in_old': before[0]['group_id']='new'
    with pytest.raises(ValueError): verify_room_addition(spec,observation(),before,after)


def test_duplicate_added_fixtures_are_not_valid_placement(spec):
    new=observation()
    new['fixtures']*=2
    new['observed_count']=2
    with pytest.raises(ValueError,match='overlap'):
        verify_room_addition(spec,new,[],[])
