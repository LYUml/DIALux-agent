import json
from pathlib import Path
import pytest
from src import workflow, desktop


@pytest.fixture
def backend(tmp_path, monkeypatch):
    project=tmp_path/'test.evo'
    project.write_bytes(b'fixture')
    calls=[]
    def operation(name):
        def run(*a,**k):
            calls.append(name)
            return {'operation':name}
        return run
    for name in ('calculate','export_pdf','save'):
        monkeypatch.setattr(desktop,'desktop_'+name,operation(name))
    monkeypatch.setattr(workflow,'read_report_pdf',lambda path:{'sha256':'fixture-hash','summaries':[
        {'summary_id':'selected','room_scene_header':'Selected room','measurements':[{'value':12}]},
        {'summary_id':'other','room_scene_header':'Other room','measurements':[{'value':999}]}]})
    return project,calls


@pytest.mark.parametrize('status,decision',[('pass','selected_conditions_met'),('fail','selected_conditions_not_met'),('unverified','evidence_incomplete')])
def test_checkpoint_orders_native_steps_and_scopes_checks(backend,tmp_path,monkeypatch,status,decision):
    project,calls=backend
    def evaluate(profile,measurements,context):
        if measurements: assert measurements==[{'value':12}]
        return {'status':status}
    monkeypatch.setattr(workflow,'evaluate_profile',evaluate)
    result=workflow.calculation_checkpoint(str(project),str(tmp_path/'run'),[{'summary_id':'selected','profile':{}}])
    assert calls==['calculate','export_pdf','save']
    assert result['decision']==decision
    assert not result['whole_project_assessed']
    journal=json.loads(Path(result['journal']).read_text())
    assert journal['state']=='completed'
    assert len(journal['steps'])==4


def test_export_failure_keeps_pending_stage_and_never_saves_or_retries(backend,tmp_path,monkeypatch):
    project,calls=backend
    monkeypatch.setattr(workflow,'evaluate_profile',lambda *a:{'status':'unverified'})
    def fail(*a):
        journal=json.loads((tmp_path/'run'/'journal.json').read_text())
        assert journal['state']=='pending_export'
        raise ValueError('uncertain native export')
    monkeypatch.setattr(desktop,'desktop_export_pdf',fail)
    checks=[{'summary_id':'selected','profile':{}}]
    with pytest.raises(ValueError,match='inspect'):
        workflow.calculation_checkpoint(str(project),str(tmp_path/'run'),checks)
    journal=json.loads((tmp_path/'run'/'journal.json').read_text())
    assert journal['failed_at']=='pending_export'
    assert calls==['calculate']
    with pytest.raises(FileExistsError):
        workflow.calculation_checkpoint(str(project),str(tmp_path/'run'),checks)
    assert calls==['calculate']


def test_unknown_room_cannot_fall_back_to_other_result(backend,tmp_path,monkeypatch):
    project,calls=backend
    monkeypatch.setattr(workflow,'evaluate_profile',lambda *a:{'status':'pass'})
    with pytest.raises(ValueError,match='missing'):
        workflow.calculation_checkpoint(str(project),str(tmp_path/'run'),[{'summary_id':'absent','profile':{}}])
    assert calls==['calculate','export_pdf']

@pytest.mark.parametrize('status,code',[('pass',0),('fail',1),('unverified',3)])
def test_cli_checkpoint_exit_codes_are_decisions(tmp_path,monkeypatch,status,code):
    import sys
    from types import SimpleNamespace
    from src import dialux_agent
    checks=tmp_path/'checks.json'
    checks.write_text('[]')
    monkeypatch.setattr(sys,'argv',['dialux-agent','calculation-checkpoint','--expected-project','test.evo',
        '--evidence-directory',str(tmp_path/'run'),'--checks',str(checks)])
    monkeypatch.setattr(dialux_agent,'_local_module',lambda name:SimpleNamespace(
        calculation_checkpoint=lambda *a:{'state':'completed','status':status}))
    assert dialux_agent.main()==code
