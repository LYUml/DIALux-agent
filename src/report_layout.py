"""Read explicit English native PDF luminaire coordinate-table pages."""
import hashlib
from io import BytesIO
import math
from pathlib import Path
import re
import pdfplumber

VALUE=r'-?\d+(?:\.\d+)?'
ROW=re.compile(rf'({VALUE}) m ({VALUE}) m ({VALUE}) m (\d+)')


def parse_coordinate_page(page, page_number):
    words=page.extract_words()
    candidates=[]
    for x in words:
        if x['text']!='X': continue
        line=sorted([w for w in words if abs(w['top']-x['top'])<1 and w['x0']>=x['x0']],key=lambda w:w['x0'])
        if [w['text'] for w in line]==['X','Y','Mounting','Luminaire']:
            candidates.append(x)
    if len(candidates)!=1: raise ValueError('Expected one coordinate table header on each page')
    x=candidates[0]
    text=page.crop((x['x0']-.5,x['top']-1,page.width,page.height)).extract_text() or ''
    lines=text.splitlines()
    if lines[:2]!=['X Y Mounting Luminaire','height'] or not lines or lines[-1]!=str(page_number):
        raise ValueError('Unsupported coordinate table header/footer')
    records=[]
    for line in lines[2:-1]:
        match=ROW.fullmatch(line.strip())
        if not match: raise ValueError('Unsupported or ambiguous coordinate table row: '+line)
        position=[float(value) for value in match.groups()[:3]]
        if not all(math.isfinite(value) for value in position): raise ValueError('Nonfinite reported coordinate')
        records.append({'report_luminaire_number':int(match[4]),'position_m':position,'page':page_number})
    if not records: raise ValueError('Empty coordinate table')
    return records


def read_report_layout(path: str, first_page: int, last_page: int, expected_count: int, expected_header: str) -> dict:
    """Read an explicitly selected, single-product coordinate table from a native report.

    Requires consecutive pages and complete 1..N report IDs. No rotation, native
    runtime identity, coordinate-frame transform or fresh simulation is inferred.
    """
    if any(type(v) is not int for v in (first_page,last_page,expected_count)) or not 1<=first_page<=last_page or not 1<=expected_count<=2000:
        raise ValueError('Expected valid one-based page range and count 1 to 2000')
    if not isinstance(expected_header,str) or not expected_header.strip(): raise ValueError('Exact report room header required')
    target=Path(path).resolve(strict=True);data=target.read_bytes()
    records=[];product=None
    with pdfplumber.open(BytesIO(data)) as doc:
        if last_page>len(doc.pages): raise ValueError('Page range exceeds report')
        for number in range(first_page,last_page+1):
            page=doc.pages[number-1];text=page.extract_text() or ''
            prefix=text.split('\nLuminaire layout plan\n')
            if len(prefix)!=2 or ' '.join(prefix[0].splitlines()[1:]).strip()!=expected_header:
                raise ValueError('Coordinate page room header differs or layout heading missing')
            if number==first_page:
                def one(pattern):
                    matches=re.findall(pattern,text,re.MULTILINE)
                    if len(matches)!=1: raise ValueError('Missing or ambiguous product evidence')
                    return matches[0]
                quantity,label=one(r'^(\d+) x (.+)$')
                manufacturer,power=one(r'^Manufacturer (.+?) P ('+VALUE+r') W$')
                article,flux=one(r'^Article No\. (\S+) \u03a6Luminaire ('+VALUE+r') lm$')
                if int(quantity)!=expected_count or any(not math.isfinite(float(v)) or float(v)<=0 for v in (power,flux)):
                    raise ValueError('Product quantity or photometric data differs')
                product={'reported_label':label,'manufacturer':manufacturer,'article_number':article,
                         'power_w':float(power),'luminaire_flux_lm':float(flux),'quantity':int(quantity),'page':number}
            elif re.search(r'^Manufacturer |^\d+ x ',text,re.MULTILINE):
                raise ValueError('Multiple product/arrangement sections are not one coordinate table')
            records.extend(parse_coordinate_page(page,number))
    if [row['report_luminaire_number'] for row in records]!=list(range(1,expected_count+1)):
        raise ValueError('Report coordinates do not provide complete ordered 1..N coverage')
    return {'schema':'dialux-agent/report-layout/v1','path':str(target),'sha256':hashlib.sha256(data).hexdigest(),
            'room_header':expected_header,'pages':list(range(first_page,last_page+1)),
            'units':'m','coordinate_frame':'report_unspecified','fixtures':records,'fixture_count':len(records),
            'product':product,'rotation_available':False,'fresh_simulation_verified':False,
            'whole_project_verified':False,
            'warning':'Native report coordinate table only. Explicitly establish frame correspondence before comparing UI/CAD coordinates; report IDs are not native runtime IDs.'}
