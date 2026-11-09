"""Scope printed fixture-label checks to the independently verified room outline."""
import re
from shapely.geometry import Polygon, box


def plotted_fixture_ids(page, expected_ids, scale_evidence=None):
    if scale_evidence is None:
        ids=re.findall(r'\bL\d+\b',page.extract_text() or '')
        scope='whole_page'
    else:
        curves=page.curves+page.rects
        outline=Polygon(curves[scale_evidence['pdf_curve_index']]['pts'])
        if not outline.is_valid or outline.area<=0: raise ValueError('Invalid verified PDF outline')
        ids=[]
        for word in page.extract_words():
            if re.fullmatch(r'L\d+',word['text']) and outline.buffer(.25).covers(box(word['x0'],word['top'],word['x1'],word['bottom'])):
                ids.append(word['text'])
        scope='verified_scale_outline'
    if sorted(ids)!=sorted(expected_ids):
        raise ValueError('Expected plotted fixture labels missing or duplicated within '+scope)
    return ids,scope
