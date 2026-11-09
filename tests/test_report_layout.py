from types import SimpleNamespace
import pytest
from src import report_layout as reader


class Page:
    width=600; height=840
    def __init__(self,number,rows,first=False):
        self.number=number;self.rows=rows
        self.text='Project\nBuilding . Storey . Room\nLuminaire layout plan\n'
        if first:
            self.text+='Manufacturer Example P 26.0 W\nArticle No. 123 \u03a6Luminaire 3602 lm\n2 x Example Panel\n'
        self.words=[{'text':text,'x0':200+i*60,'top':400} for i,text in enumerate(['X','Y','Mounting','Luminaire'])]
    def extract_text(self): return self.text
    def extract_words(self): return self.words
    def crop(self,bbox):
        assert bbox==(199.5,399,600,840)
        return SimpleNamespace(extract_text=lambda:'X Y Mounting Luminaire\nheight\n'+'\n'.join(self.rows)+'\n'+str(self.number))


@pytest.fixture
def report(tmp_path,monkeypatch):
    path=tmp_path/'test.pdf';path.write_bytes(b'fixture')
    pages=[Page(1,['1.000 m 2.000 m 3.035 m 1'],True),Page(2,['4.000 m 2.000 m 3.035 m 2'])]
    class Document:
        def __enter__(self): return SimpleNamespace(pages=pages)
        def __exit__(self,*args): pass
    monkeypatch.setattr(reader.pdfplumber,'open',lambda *a:Document())
    return path,pages


def test_complete_report_table_keeps_product_and_position_evidence(report):
    path,pages=report
    result=reader.read_report_layout(str(path),1,2,2,'Building . Storey . Room')
    assert result['fixture_count']==2 and result['fixtures'][1]['position_m']==[4,2,3.035]
    assert result['product']['article_number']=='123' and result['product']['power_w']==26
    assert result['coordinate_frame']=='report_unspecified' and not result['rotation_available']


@pytest.mark.parametrize('change',['missing','duplicate','room','product','unit','extra','header','count','power'])
def test_report_table_refuses_ambiguous_or_incomplete_evidence(report,change):
    path,pages=report
    if change=='missing': pages[1].rows=[]
    if change=='duplicate': pages[1].rows=['4.000 m 2.000 m 3.035 m 1']
    if change=='room': pages[1].text=pages[1].text.replace('Room','Other')
    if change=='product': pages[1].text+='1 x Other Panel\n'
    if change=='unit': pages[1].rows=['4.000 ft 2.000 m 3.035 m 2']
    if change=='extra': pages[1].rows.append('unparsed value')
    if change=='header': pages[1].words=[]
    if change=='count': pages[0].text=pages[0].text.replace('2 x','3 x')
    if change=='power': pages[0].text=pages[0].text.replace('26.0 W','0 W')
    with pytest.raises(ValueError): reader.read_report_layout(str(path),1,2,2,'Building . Storey . Room')
