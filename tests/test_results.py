from pathlib import Path
import sys
import json
import hashlib
import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT/'tests/fixtures/reports'
MANIFEST = json.loads((REPORTS/'manifest.json').read_text())

def fixture_report(name):
    record = MANIFEST[name]
    path = REPORTS/record['file']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256']
    return str(path)

sys.path.insert(0, str(ROOT / 'src'))
from results import parse_summary_pages, parse_report_pages, read_summary_pdf, parse_report_summaries, read_report_pdf


@pytest.fixture
def pages():
    # Synthetic layout fixture, deliberately different values and surface from the live report.
    header = 'Building B · Storey S · Room R (Light scene\n2)\nSummary\n'
    return [header + 'Ground area 30.00 m² Clearance height 3.000 m\nHeight Working plane 0.800 m',
            header + 'Results\nWorking plane Ēperpendicular 217 lx ≥ 500 lx WP7\nUo (g1) 0.41 ≥ 0.60 WP7\nSpace Lighting power density 4.20 W/m² –\n']


def test_actual_values_not_targets(pages):
    result = parse_summary_pages(pages)
    assert [r['value'] for r in result['measurements']] == [217, .41, 4.2]
    assert result['measurements'][0]['calculation_surface'] == 'WP7'


def test_custom_building_header_and_unavailable_uniformity(pages):
    pages = [p.replace('Building B', 'STF Building') for p in pages]
    pages[1] = pages[1].replace('217 lx', '0.00 lx').replace('0.41', '-')
    result = parse_report_summaries(['Cover'] + pages)['summaries'][0]
    assert [r['metric'] for r in result['measurements']] == [
        'average_perpendicular_illuminance', 'lighting_power_density']
    missing = result['unavailable_measurements'][0]
    assert missing['reported_value'] == '-'
    assert missing['page'] == 3
    assert missing['summary_id'] == result['summary_id']
    assert missing['calculation_surface'] == 'WP7'
    assert 'value' not in missing


def test_synthetic_three_room_report():
    result = read_report_pdf(fixture_report('three-rooms'))
    assert result['sha256'] == MANIFEST['three-rooms']['sha256']
    assert result['document_pages'] == 39
    assert result['summary_count'] == 3
    summaries = result['summaries']
    assert [s['summary_pages'] for s in summaries] == [[15,16],[20,21],[28,29]]
    assert [s['measurements'][0]['value'] for s in summaries] == [0,693,0]
    assert [len(s['unavailable_measurements']) for s in summaries] == [1,0,1]
    assert [r['value'] for r in summaries[1]['measurements']] == [693,.57,9.75]
    for summary in summaries:
        for row in summary['measurements'] + summary['unavailable_measurements']:
            assert result['sha256'] in row['evidence']
    with pytest.raises(ValueError):
        read_summary_pdf(fixture_report('three-rooms'))


def test_synthetic_two_lit_rooms():
    report = read_report_pdf(fixture_report('two-lit-rooms'))
    assert report['sha256'] == MANIFEST['two-lit-rooms']['sha256']
    assert report['document_pages'] == 42
    assert [s['summary_pages'] for s in report['summaries']] == [[15,16],[23,24],[31,32]]
    assert [[m['value'] for m in s['measurements']] for s in report['summaries']] == [
        [531,.57,6.5],[693,.59,9.75],[0,0]]
    assert [len(s['unavailable_measurements']) for s in report['summaries']] == [0,0,1]


def test_multi_room_scene_results_remain_separate_with_original_pages(pages):
    other = [p.replace('Room R', 'Room X').replace('217 lx', '333 lx') for p in pages]
    scene = [p.replace('scene\n2', 'scene\n3').replace('217 lx', '111 lx') for p in pages]
    result = parse_report_summaries(['Cover']+pages+['Separator']+other+scene)
    assert result['summary_count'] == 3
    assert [r['summary_pages'] for r in result['summaries']] == [[2,3],[5,6],[7,8]]
    assert [r['measurements'][0]['value'] for r in result['summaries']] == [217,333,111]
    assert len({r['summary_id'] for r in result['summaries']}) == 3
    for summary in result['summaries']:
        assert all(r['summary_id']==summary['summary_id'] for r in summary['measurements'])
    assert not result['complete_project_coverage_verified']


@pytest.mark.parametrize('kind', ['duplicate', 'missing', 'mixed', 'separated'])
def test_collection_rejects_ambiguous_pairing(pages, kind):
    other = [p.replace('Room R', 'Room X') for p in pages]
    if kind == 'duplicate': report = pages+pages
    elif kind == 'missing': report = pages+[other[0]]
    elif kind == 'mixed': report = [pages[0], other[1]]
    else: report = pages+[other[0], 'interruption', other[1]]
    with pytest.raises(ValueError): parse_report_summaries(report)


def test_room_header_wrap_before_light_scene(pages):
    wrapped = [page.replace('Room R (Light scene', 'Room R\n(Light scene') for page in pages]
    assert parse_report_pages(wrapped)['measurements'][0]['value'] == 217


def test_room_header_wrap_inside_light_scene(pages):
    wrapped = [page.replace('Light scene', 'Light\nscene') for page in pages]
    assert parse_report_pages(wrapped)['measurements'][0]['value'] == 217


def test_full_document_preserves_original_page_numbers(pages):
    result = parse_report_pages(['Cover', 'Table of Contents\nSummary'] + pages + ['Glossary'])
    assert result['summary_pages'] == [3, 4]
    assert result['document_pages'] == 5
    assert all(row['page'] == 4 for row in result['measurements'])


@pytest.mark.parametrize('kind', ['multiple', 'separated', 'mixed_room'])
def test_full_document_refuses_ambiguous_summary_selection(pages, kind):
    if kind == 'multiple': report = pages + pages
    elif kind == 'separated': report = [pages[0], 'Unrelated page', pages[1]]
    else: report = [pages[0], pages[1].replace('Room R', 'Room X')]
    with pytest.raises(ValueError):
        parse_report_pages(report)


def test_synthetic_full_document_report():
    result = read_summary_pdf(fixture_report('full-document'))
    assert result['document_pages'] == 28
    assert result['summary_pages'] == [14, 15]
    assert [row['value'] for row in result['measurements']] == [104, .21, 1.08]
    assert all('#page=15;' in row['evidence'] for row in result['measurements'])


def test_overflow_value_is_not_reported_as_infinity(pages):
    pages[1] = pages[1].replace('217 lx', '9' * 400 + ' lx')
    with pytest.raises(ValueError, match='physical'):
        parse_summary_pages(pages)


def test_corrupt_pdf_is_domain_error(tmp_path):
    path = tmp_path/'broken.pdf'
    path.write_bytes(b'not a PDF')
    with pytest.raises(ValueError, match='Unreadable'):
        read_summary_pdf(str(path))


@pytest.mark.parametrize('mutation', ['duplicate', 'room', 'surface', 'missing', 'unit', 'extra_page'])
def test_reject_ambiguous_reports(pages, mutation):
    if mutation == 'duplicate': pages[1] += '\nWorking plane Ēperpendicular 9 lx ≥ 500 lx WP7'
    if mutation == 'room': pages[1] = pages[1].replace('Room R', 'Room X')
    if mutation == 'surface': pages[1] = pages[1].replace('0.60 WP7', '0.60 WP8')
    if mutation == 'missing': pages[1] = pages[1].replace('Uo (g1)', 'Unknown')
    if mutation == 'unit': pages[1] = pages[1].replace('217 lx', '217 fc')
    if mutation == 'extra_page': pages.append(pages[0])
    with pytest.raises(ValueError): parse_summary_pages(pages)


def test_synthetic_summary_v1():
    result = read_summary_pdf(fixture_report('summary-v1'))
    assert result['area_m2'] == 24
    assert [r['value'] for r in result['measurements']] == [104, .20, 1.08]
    assert result['sha256'] == MANIFEST['summary-v1']['sha256']
    assert all(result['sha256'] in r['evidence'] for r in result['measurements'])


def test_synthetic_summary_v2():
    result = read_summary_pdf(fixture_report('summary-v2'))
    assert result['area_m2'] == 24
    assert [r['value'] for r in result['measurements']] == [104, .22, 1.08]
    assert result['sha256'] == MANIFEST['summary-v2']['sha256']

def test_synthetic_concave_area_and_results():
    result=read_summary_pdf(fixture_report('concave-area'))
    assert result['sha256'] == MANIFEST['concave-area']['sha256']
    assert result['area_m2']==20
    assert result['summary_pages']==[14,15]
    assert [m['value'] for m in result['measurements']]==[493,.55,6.5]
