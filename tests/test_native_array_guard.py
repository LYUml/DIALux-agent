import copy
import pytest
from src import windows_worker as w

@pytest.mark.parametrize('change',['runtime','field'])
def test_guarded_native_array_refuses_stale_snapshot_before_result_clear(monkeypatch,change):
 values={'ElementCountX':'3','ElementCountY':'2','PolygonPosition_X':'3','PolygonPosition_Y':'2',
         'PolygonPosition_Z':'3.035','ArrangementRotation_Z':'0','ArrangementObjectName':'Array'}
 arrangement={'runtime_id':[7,1],'tree_item_id':'Root_Luminaires_Array','display_values':values}
 current=copy.deepcopy(arrangement)
 if change=='runtime': current['runtime_id']=[7,2]
 if change=='field': current['display_values']['ElementCountY']='3'
 monkeypatch.setattr(w,'read_arrangement',lambda *a,**kw:current)
 monkeypatch.setattr(w,'prepare_project',lambda *a:pytest.fail('results preparation attempted'))
 with pytest.raises(ValueError):
  w.guarded_array_edit(None,None,None,'test.evo',arrangement,
    dict(PolygonPosition_X=3.1,PolygonPosition_Y=2,PolygonPosition_Z=3.035,ArrangementRotation_Z=0),
    lambda *a:pytest.fail('intent recorded'))

def test_array_runtime_required_before_ui(monkeypatch):
 monkeypatch.setattr(w,'read_arrangement',lambda *a:pytest.fail('UI accessed'))
 with pytest.raises(ValueError,match='runtime'):
  w.guarded_array_edit(None,None,None,'test.evo',{}, {},None)


def test_guarded_array_reuses_selected_node_when_tree_panel_is_hidden(monkeypatch):
 from types import SimpleNamespace
 values={'ElementCountX':'3','ElementCountY':'2','PolygonPosition_X':'3','PolygonPosition_Y':'2',
         'PolygonPosition_Z':'3.035','ArrangementRotation_Z':'0','ArrangementObjectName':'Array'}
 arrangement={'runtime_id':[7,1],'tree_item_id':'Root_Luminaires_Array','display_values':values}
 item=SimpleNamespace(element_info=SimpleNamespace(runtime_id=[7,1]),is_selected=lambda:True)
 def reader(*a,**kw):
  kw['_selection']['item']=item
  return copy.deepcopy(arrangement)
 monkeypatch.setattr(w,'read_arrangement',reader)
 monkeypatch.setattr(w,'prepare_project',lambda *a:(None,{'controls':{'DiscardResultsButton':{'enabled':False}}}))
 monkeypatch.setattr(w,'wait_control',lambda *a:pytest.fail('Hidden tree queried'))
 monkeypatch.setattr(w,'read_edit_values',lambda *a:dict(values))
 result=w.guarded_array_edit(None,None,None,'test.evo',arrangement,
   dict(PolygonPosition_X=3,PolygonPosition_Y=2,PolygonPosition_Z=3.035,ArrangementRotation_Z=0),lambda *a:None)
 assert result['completed_fields']==[] and not result['fixture_geometry_verified']
