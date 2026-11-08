import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from regulations import evaluate_profile, SOURCE_FIELDS

@pytest.fixture
def data():
    # Arbitrary unit-test threshold, not a regulation.
    rule = {'id':'test', 'metric':'test_metric', 'unit':'test_unit', 'operator':'>=',
            'threshold':10, 'calculation_surface':'test_surface',
            'source':{k:'synthetic test source' for k in SOURCE_FIELDS}}
    profile = {'schema':'dialux-agent/criteria-profile/v1', 'jurisdiction':'TEST',
               'status':'verified', 'criteria':[rule]}
    measurement = {'metric':'test_metric', 'unit':'test_unit', 'value':10,
                   'calculation_surface':'test_surface', 'evidence':'synthetic fixture'}
    return profile, measurement

def test_boundary_and_failure(data):
    p,m=data
    assert evaluate_profile(p,[m])['status']=='pass'
    m['value']=9
    assert evaluate_profile(p,[m])['status']=='fail'

@pytest.mark.parametrize('field,value', [('unit','wrong'), ('calculation_surface','other'),
    ('evidence',''), ('value',float('nan')), ('value',True)])
def test_missing_or_incompatible_result(data,field,value):
    p,m=data;m[field]=value
    assert evaluate_profile(p,[m])['status']=='unverified'

def test_duplicates_and_empty(data):
    p,m=data
    assert evaluate_profile(p,[m,m])['status']=='unverified'
    p['criteria']=[]
    assert evaluate_profile(p,[m])['status']=='unverified'

def test_unverified_source(data):
    p,m=data;p['criteria'][0]['source']['edition']=''
    assert evaluate_profile(p,[m])['status']=='unverified'

def test_missing_surface_is_not_wildcard(data):
    p,m=data;del p['criteria'][0]['calculation_surface'];del m['calculation_surface']
    with pytest.raises(ValueError):evaluate_profile(p,[m])
