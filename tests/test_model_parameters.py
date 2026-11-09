import hashlib
from types import SimpleNamespace
import pytest
from src.model_parameters import parse_model_parameters, read_model_parameters
from test_results import pages

TEXT='''Reflection factors Ceiling: 72.0 %, Mounting height 3.035 m
Walls: 46.0 %,
Floor: 18.0 % Height Working plane 0.800 m
Maintenance factor 0.76 (fixed) Wall zone Working plane 0.250 m'''


def test_explicit_reported_values():
    result=parse_model_parameters(TEXT)
    assert result=={'ceiling_reflectance_pct':72,'wall_reflectance_pct':46,'floor_reflectance_pct':18,
                    'maintenance_factor':.76,'mounting_height_m':3.035,'wall_zone_m':.25}


@pytest.mark.parametrize('old,new',[
    ('72.0','172.0'),('46.0','-46.0'),('0.76','1.20'),('0.76','0'),
    ('(fixed)','(variable)'),('Floor: 18.0 %',''),('3.035','0'),
    ('Walls: 46.0 %,','Walls: 46.0 %, Walls: 46.0 %,')])
def test_missing_ambiguous_or_invalid_values_rejected(old,new):
    with pytest.raises(ValueError): parse_model_parameters(TEXT.replace(old,new))


def test_reader_binds_exact_scope_and_source_bytes(tmp_path,monkeypatch,pages):
    text=[pages[0]+'\n'+TEXT.replace(' Height Working plane 0.800 m',''),pages[1]]
    class Document:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        pages=[SimpleNamespace(extract_text=lambda value=value:value) for value in text]
    monkeypatch.setattr('src.model_parameters.pdfplumber.open',lambda data:Document())
    path=tmp_path/'synthetic.pdf';path.write_bytes(b'synthetic-parser-fixture')
    identity=hashlib.sha256('Building B · Storey S · Room R (Light scene 2)'.encode()).hexdigest()
    result=read_model_parameters(str(path),identity)
    assert result['parameters']['maintenance_factor']==.76 and result['parameters']['area_m2']==30
    assert result['report_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert not result['per_surface_materials_verified'] and not result['fresh_calculation_verified']
    with pytest.raises(ValueError,match='Exact room/scene'):read_model_parameters(str(path),'wrong-room')
