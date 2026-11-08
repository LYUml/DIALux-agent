from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from results import parse_summary_pages, parse_report_pages, read_summary_pdf


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


def test_room_header_wrap_before_light_scene(pages):
    wrapped = [page.replace('Room R (Light scene', 'Room R\n(Light scene') for page in pages]
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


@pytest.mark.skipif(not (ROOT/'local/standalone-cli-export-v3.pdf').exists(), reason='Local live artifact is not distributed')
def test_standalone_full_document_export():
    result = read_summary_pdf(str(ROOT/'local/standalone-cli-export-v3.pdf'))
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


@pytest.mark.skipif(not (ROOT/'local/validation-summary-v1.pdf').exists(), reason='Local live artifact is not distributed')
def test_real_evo_export():
    result = read_summary_pdf(str(ROOT/'local/validation-summary-v1.pdf'))
    assert result['area_m2'] == 24
    assert [r['value'] for r in result['measurements']] == [104, .20, 1.08]
    assert result['sha256'] == 'ab6af3bc36541c8bb0d6d2634e3ee7367239af082de1c42de0fe2cf9dd0038f7'
    assert all(result['sha256'] in r['evidence'] for r in result['measurements'])


@pytest.mark.skipif(not (ROOT/'local/validation-summary-v2.pdf').exists(), reason='Local live artifact is not distributed')
def test_second_evo_export():
    result = read_summary_pdf(str(ROOT/'local/validation-summary-v2.pdf'))
    assert result['area_m2'] == 24
    assert [r['value'] for r in result['measurements']] == [104, .22, 1.08]
    assert result['sha256'] == '25f4a51ecbf4a5a9187a2dd1fc354bdf98b2e3dc3149d6d8234d0fae3e7d0820'
