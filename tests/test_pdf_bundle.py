from contextlib import closing
import hashlib
import json
import pytest
import pypdfium2 as pdfium
from src.pdf_bundle import build_pdf_bundle, verify_pdf_bundle


def fixture_pdf(path, form=False):
    # Small explicit synthetic fixture: distinct visible page labels and sizes.
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 300] /Resources << /Font << /F1 5 0 R >> >> /Contents 7 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    for label in (b'SYNTHETIC TOOL TEST - ONE',b'SYNTHETIC TOOL TEST - TWO'):
        stream = b'BT /F1 10 Tf 15 100 Td ('+label+b') Tj ET'
        objects.append(b'<< /Length '+str(len(stream)).encode()+b' >>\nstream\n'+stream+b'\nendstream')
    if form:
        objects[0]=b'<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [8 0 R] >> >>'
        objects[2]=objects[2][:-2]+b' /Annots [8 0 R] >>'
        objects.append(b'<< /Type /Annot /Subtype /Widget /FT /Tx /T (TestField) /V (test) /Rect [10 10 100 30] /P 3 0 R >>')
    data=b'%PDF-1.4\n'; offsets=[0]
    for index,obj in enumerate(objects,1):
        offsets.append(len(data));data+=f'{index} 0 obj\n'.encode()+obj+b'\nendobj\n'
    start=len(data);data+=f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode()
    data+=b''.join(f'{n:010d} 00000 n \n'.encode() for n in offsets[1:])
    data+=f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    path.write_bytes(data);return hashlib.sha256(data).hexdigest()


@pytest.fixture
def bundle_request(tmp_path):
    source=tmp_path/'source.pdf';sha=fixture_pdf(source)
    return dict(sections=[dict(path=str(source),sha256=sha,pages=[2],role='main'),
                          dict(path=str(source),sha256=sha,pages=[1],role='appendix')],
                output_directory=str(tmp_path/'bundle'),max_main_pages=1,max_bytes=1_000_000)


def test_bundle_preserves_order_sizes_text_pixels_and_sources(bundle_request):
    result=build_pdf_bundle(**bundle_request)
    assert result['page_count']==2 and result['main_page_count']==1
    assert result['rendering_72dpi_verified'] and not result['engineering_content_verified']
    with pdfium.PdfDocument(result['output']) as doc:
        with closing(doc[0]) as page:
            assert page.get_size()==(200,300)
            with closing(page.get_textpage()) as text: assert 'TWO' in text.get_text_range()
        with closing(doc[1]) as page:
            with closing(page.get_textpage()) as text: assert 'ONE' in text.get_text_range()
    assert hashlib.sha256(open(bundle_request['sections'][0]['path'],'rb').read()).hexdigest()==bundle_request['sections'][0]['sha256']


@pytest.mark.parametrize('bad',['hash','range','duplicate','main_limit','size','order','bool','existing'])
def test_rejects_invalid_bundle_without_publishing(bundle_request,bad):
    from pathlib import Path
    out=Path(bundle_request['output_directory'])
    if bad=='hash': bundle_request['sections'][0]['sha256']='0'*64
    if bad=='range': bundle_request['sections'][0]['pages']=[3]
    if bad=='duplicate': bundle_request['sections'][1]['pages']=[2]
    if bad=='main_limit': bundle_request['sections'][1]['role']='main'
    if bad=='size': bundle_request['max_bytes']=1
    if bad=='order': bundle_request['sections'].reverse()
    if bad=='bool': bundle_request['sections'][0]['pages']=[True]
    if bad=='existing': out.mkdir();(out/'keep.txt').write_text('preserve')
    with pytest.raises(ValueError): build_pdf_bundle(**bundle_request)
    assert not (out/'bundle.pdf').exists()
    if bad=='existing': assert (out/'keep.txt').read_text()=='preserve'


def test_real_form_is_rejected_before_publishing(bundle_request):
    from pathlib import Path
    source=Path(bundle_request['sections'][0]['path'])
    digest=fixture_pdf(source,form=True)
    for section in bundle_request['sections']: section['sha256']=digest
    with pytest.raises(ValueError,match='Forms and signed'):
        build_pdf_bundle(**bundle_request)
    assert not Path(bundle_request['output_directory']).exists()


def test_source_change_during_assembly_is_rejected(bundle_request,monkeypatch):
    from pathlib import Path
    original=pdfium.PdfDocument.save
    source=Path(bundle_request['sections'][0]['path'])
    def changed_after_save(document,*args,**kwargs):
        result=original(document,*args,**kwargs)
        source.write_bytes(source.read_bytes()+b'\n% external change\n')
        return result
    monkeypatch.setattr(pdfium.PdfDocument,'save',changed_after_save)
    with pytest.raises(ValueError,match='Source changed during assembly'):
        build_pdf_bundle(**bundle_request)
    assert not Path(bundle_request['output_directory']).exists()


def test_wrong_imported_page_is_detected_on_reopen(bundle_request,monkeypatch):
    from pathlib import Path
    original=pdfium.PdfDocument.import_pages
    def wrong_page(document,source,pages):
        return original(document,source,[0]*len(pages))
    monkeypatch.setattr(pdfium.PdfDocument,'import_pages',wrong_page)
    with pytest.raises(ValueError,match='rendering/text/size differs'):
        build_pdf_bundle(**bundle_request)
    assert not Path(bundle_request['output_directory']).exists()


def test_module_command_returns_machine_readable_rejection(tmp_path):
    import subprocess,sys
    request_file=tmp_path/'request.json';request_file.write_text('{invalid')
    completed=subprocess.run([sys.executable,'-m','src.pdf_bundle','--request',str(request_file)],capture_output=True,text=True)
    assert completed.returncode==2
    assert json.loads(completed.stdout)['state']=='rejected'
    assert 'Traceback' not in completed.stderr


def test_independent_bundle_replay(bundle_request):
    build_pdf_bundle(**bundle_request)
    result=verify_pdf_bundle(bundle_request['output_directory'])
    assert result['page_count']==2 and result['sources_checked']==1
    assert result['rendering_72dpi_verified'] and not result['source_authenticity_verified']


@pytest.mark.parametrize('corruption',['output','source','mapping','evidence','count','limit','order'])
def test_independent_replay_rejects_changed_artifacts(bundle_request,corruption):
    from pathlib import Path
    build_pdf_bundle(**bundle_request)
    root=Path(bundle_request['output_directory']);path=root/'manifest.json'
    manifest=json.loads(path.read_bytes())
    if corruption=='output':
        pdf=root/'bundle.pdf';pdf.write_bytes(pdf.read_bytes()+b'\n% changed')
    if corruption=='source':
        source=Path(bundle_request['sections'][0]['path']);source.write_bytes(source.read_bytes()+b'\n% changed')
    if corruption=='mapping': manifest['pages'][0]['source_page']=1
    if corruption=='evidence': manifest['pages'][0]['evidence']['text_sha256']='0'*64
    if corruption=='count': manifest['main_page_count']=2
    if corruption=='limit': manifest['max_bytes']=1
    if corruption=='order': manifest['pages'].reverse()
    path.write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError): verify_pdf_bundle(str(root))
