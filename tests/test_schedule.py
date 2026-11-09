import copy
import pytest
from src import schedule


@pytest.fixture
def case(monkeypatch):
    layout={'schema':'dialux-agent/layout/v1','origin':'supplied_native_observations','units':'m','coordinate_frame':'active_storey',
            'observations_sha256':'a'*64,'fixture_count':2,'fixtures':[
                {'id':'L002','position_m':[8,24,7],'rotation_deg':0},
                {'id':'L001','position_m':[8,21,7],'rotation_deg':30}]}
    report={'fixtures':[{'report_luminaire_number':1,'position_m':[1,2,3],'page':17},
                        {'report_luminaire_number':2,'position_m':[4,2,3],'page':17}],
            'product':{'power_w':26,'quantity':2,'article_number':'test'},'path':'report.pdf','sha256':'b'*64,'room_header':'Room'}
    monkeypatch.setattr(schedule,'read_report_layout',lambda **k:copy.deepcopy(report))
    descriptor={'path':'report.pdf','first_page':17,'last_page':17,'expected_header':'Room'}
    alignment={'translation_m':[10,20,4],'rotation_deg':90,'evidence':'Explicit synthetic transform fixture'}
    return layout,descriptor,alignment,report


def test_schedule_matches_positions_not_row_order_with_explicit_transform(case):
    layout,descriptor,alignment,_=case
    r=schedule.build_luminaire_schedule(layout,descriptor,alignment)
    assert [f['report_luminaire_number'] for f in r['fixtures']]==[2,1]
    assert r['total_reported_fixture_power_w']==52
    assert r['fixtures'][1]['rotation_deg']==30
    assert not r['photometry_identity_verified'] and not r['alignment_independently_verified']


@pytest.mark.parametrize('change',['duplicate_id','wrong_position','wrong_frame','planned','missing_evidence','nan','count','hash'])
def test_schedule_refuses_inconsistent_or_unexplained_correspondence(case,change):
    layout,descriptor,alignment,_=case
    if change=='duplicate_id': layout['fixtures'][1]['id']='L002'
    if change=='wrong_position': layout['fixtures'][1]['position_m'][0]=9
    if change=='wrong_frame': layout['coordinate_frame']='room_local'
    if change=='planned': layout['origin']='planned'
    if change=='missing_evidence': alignment['evidence']=''
    if change=='nan': alignment['translation_m'][0]=float('nan')
    if change=='count': layout['fixture_count']=3
    if change=='hash': layout.pop('observations_sha256')
    with pytest.raises(ValueError): schedule.build_luminaire_schedule(layout,descriptor,alignment)
