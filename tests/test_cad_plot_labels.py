from types import SimpleNamespace
import pytest
from src.cad_plot import plotted_fixture_ids

def page(words):
 return SimpleNamespace(curves=[{'pts':[(0,0),(100,0),(100,100),(0,100),(0,0)]}],rects=[],
  extract_text=lambda:' '.join(w['text'] for w in words),extract_words=lambda:words)
def word(name,x,y): return dict(text=name,x0=x,x1=x+10,top=y,bottom=y+5)

def test_schedule_references_do_not_duplicate_drawing_labels():
 p=page([word('L001',10,10),word('L002',40,40),word('L001',120,120)])
 assert plotted_fixture_ids(p,['L001','L002'],{'pdf_curve_index':0})==(['L001','L002'],'verified_scale_outline')
 with pytest.raises(ValueError): plotted_fixture_ids(p,['L001','L002'])

@pytest.mark.parametrize('words',[[word('L001',120,120)],[word('L001',10,10),word('L001',30,30)],
 [word('L001',10,10),word('L999',30,30)],[word('L001',95,10)]])
def test_references_cannot_mask_missing_duplicate_unknown_or_clipped_labels(words):
 with pytest.raises(ValueError): plotted_fixture_ids(page(words),['L001'],{'pdf_curve_index':0})
