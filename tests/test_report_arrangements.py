from types import SimpleNamespace
import pytest
from src import report_layout as reader


class ArrangementPage:
    width=600; height=840
    def __init__(self, number, group, article, arrangement, ids):
        self.number=number; self.ids=ids
        self.words=[{'text':t,'x0':250+i*60,'top':400} for i,t in enumerate(['X','Y','Mounting','Luminaire'])]
        self.text=('Project\nBuilding . Storey . Room\nLuminaire layout plan\n'
            f'Manufacturer Example P 26.0 W\nArticle No. {article} \u03a6Luminaire 3602 lm\n'
            f'Article name Wrapped\nPanel label\nFitting LED\n{group}\n'
            'Type Field Arrangement X Y Mounting Luminaire\n')
        self.field=f'X-direction {len(ids)} pcs., Centre -\nY-direction 1 pcs., Centre -\nArrangement {arrangement}'
    def extract_text(self): return self.text
    def extract_words(self): return self.words
    def crop(self,bbox):
        if bbox[0]==0:
            assert bbox==(0,399,249,840)
            return SimpleNamespace(extract_text=lambda:self.field)
        assert bbox==(249.5,399,600,840)
        return SimpleNamespace(extract_text=lambda:'X Y Mounting Luminaire\nheight\n'+
            '\n'.join(f'{i}.000 m 1.000 m 3.035 m {i}' for i in self.ids)+'\n'+str(self.number))


@pytest.fixture
def report(tmp_path,monkeypatch):
    path=tmp_path/'synthetic.pdf';path.write_bytes(b'explicit synthetic fixture')
    pages=[ArrangementPage(1,'Second','B','A2',[3]),ArrangementPage(2,'First','A','A1',[1,2])]
    class Document:
        def __enter__(self): return SimpleNamespace(pages=pages)
        def __exit__(self,*args): pass
    monkeypatch.setattr(reader.pdfplumber,'open',lambda *a:Document())
    request=dict(path=str(path),expected_count=3,expected_header='Building . Storey . Room',sections=[
        dict(first_page=1,last_page=1,expected_count=1,expected_group='Second',expected_article_number='B'),
        dict(first_page=2,last_page=2,expected_count=2,expected_group='First',expected_article_number='A')])
    return request,pages


def test_products_remain_associated_with_global_ids_despite_page_order(report):
    request,pages=report
    result=reader.read_report_arrangements(**request)
    assert [r['report_luminaire_number'] for r in result['fixtures']]==[3,1,2]
    assert [r['article_number'] for r in result['fixtures']]==['B','A','A']
    assert result['products'][0]['reported_label']=='Wrapped Panel label'
    assert not result['whole_project_verified'] and not result['fresh_simulation_verified']


@pytest.mark.parametrize('change',['overlap','duplicate_group','wrong_article','wrong_group','wrong_room',
    'duplicate_id','missing_id','field_count','missing_header','duplicate_product','duplicate_arrangement',
    'total_count','negative_power','missing_fitting','unknown_row'])
def test_rejects_incomplete_or_ambiguous_arrangement_evidence(report,change):
    request,pages=report
    if change=='overlap': request['sections'][1].update(first_page=1,last_page=1)
    if change=='duplicate_group': request['sections'][1]['expected_group']='Second'
    if change=='wrong_article': request['sections'][0]['expected_article_number']='other'
    if change=='wrong_group': request['sections'][0]['expected_group']='other'
    if change=='wrong_room': pages[0].text=pages[0].text.replace('Room','Other')
    if change=='duplicate_id': pages[0].ids=[1]
    if change=='missing_id': pages[0].ids=[4]
    if change=='field_count': pages[0].field=pages[0].field.replace('X-direction 1','X-direction 2')
    if change=='missing_header': pages[0].words=[]
    if change=='duplicate_product': pages[0].text+='Manufacturer Other P 20 W\n'
    if change=='duplicate_arrangement': pages[1].field=pages[1].field.replace('A1','A2')
    if change=='total_count': request['expected_count']=4
    if change=='negative_power': pages[0].text=pages[0].text.replace('26.0 W','-1 W')
    if change=='missing_fitting': pages[0].text=pages[0].text.replace('Fitting LED','Unknown LED')
    if change=='unknown_row': pages[0].ids=['unparsed']
    with pytest.raises(ValueError): reader.read_report_arrangements(**request)
