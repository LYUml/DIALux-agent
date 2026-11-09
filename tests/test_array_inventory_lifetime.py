import gc
import weakref
import pytest
from src import windows_worker as worker
from src import placement, array_execution


@pytest.mark.parametrize('fail',[False,True])
def test_array_retains_distinct_native_scan_contexts_until_exit(monkeypatch,fail):
    class NativeHandle:pass
    references=[];context_ids=[]
    def read(*args,**kwargs):
        context=kwargs['_context'];context_ids.append(id(context))
        handle=NativeHandle();references.append(weakref.ref(handle))
        context['elements']=[handle]
        return {'read':True}
    monkeypatch.setattr(worker,'read_group_fixtures',read)
    def checkpoint(project,page_reader,**parameters):
        return page_reader(project,parameters['group_id'])
    monkeypatch.setattr(placement,'_inspect_group_checkpoint',checkpoint)
    def execute(project,**options):
        options['inspector'](project,'group',168,'before')
        gc.collect();assert references[0]() is not None
        if fail:raise ValueError('Synthetic interrupted execution')
        options['inspector'](project,'group',168,'after')
        gc.collect();assert all(reference() is not None for reference in references)
        assert context_ids[0]!=context_ids[1]
        return {'state':'test-only'}
    monkeypatch.setattr(array_execution,'_apply_array_transform',execute)
    parameters={'spec':{},'group_id':'group','evidence_directory':'unused'}
    if fail:
        with pytest.raises(ValueError,match='Synthetic interrupted'):
            worker.apply_array_transform(None,None,None,'project.evo',parameters)
    else:
        assert worker.apply_array_transform(None,None,None,'project.evo',parameters)=={'state':'test-only'}
    gc.collect();assert all(reference() is None for reference in references)
