"""Exercise actual entrypoints so test sys.path changes cannot hide import errors."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('entry', [['src/dialux_agent.py'], ['-m', 'src.dialux_agent']])
@pytest.mark.parametrize('command', ['report-read', 'stf-inspect'])
def test_entrypoints_return_json_for_missing_input(entry, command, tmp_path):
    run = subprocess.run([sys.executable, *entry, command, '--path', str(tmp_path/'absent.pdf')],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 2, run.stderr
    assert json.loads(run.stdout)['ok'] is False
    assert not run.stderr


def test_package_server_import():
    run = subprocess.run([sys.executable, '-c', 'import src.server'], cwd=ROOT,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_broken_report_returns_json_instead_of_traceback(tmp_path):
    path = tmp_path/'broken.pdf'
    path.write_bytes(b'not a PDF')
    run = subprocess.run([sys.executable, '-m', 'src.dialux_agent', 'report-read', '--path', str(path)],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 2
    assert 'Unreadable' in json.loads(run.stdout)['error']
    assert not run.stderr


def test_pdf_bundle_main_cli_build_and_verify(tmp_path):
    from test_pdf_bundle import fixture_pdf
    source=tmp_path/'source.pdf';digest=fixture_pdf(source)
    args={'sections':[{'path':str(source),'sha256':digest,'pages':[1],'role':'main'}],
          'output_directory':str(tmp_path/'bundle'),'max_main_pages':1,'max_bytes':1000000}
    request_file=tmp_path/'request.json';request_file.write_text(json.dumps(args))
    for command,option,value in [('pdf-bundle-build','--request',request_file),('pdf-bundle-verify','--evidence-directory',tmp_path/'bundle')]:
        result=subprocess.run([sys.executable,'-m','src.dialux_agent',command,option,str(value)],cwd=ROOT,capture_output=True,text=True)
        assert result.returncode==0,result.stderr+result.stdout
        assert json.loads(result.stdout)['page_count']==1


def test_array_main_cli_rejects_incomplete_evidence(tmp_path):
    (tmp_path/'journal.json').write_text(json.dumps({'schema':'dialux-agent/array-execution/v1','state':'reading_after'}))
    result=subprocess.run([sys.executable,'-m','src.dialux_agent','array-execution-verify','--evidence-directory',str(tmp_path)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==2 and not json.loads(result.stdout)['ok']
    assert not result.stderr


@pytest.mark.parametrize('entry', [['src/dialux_agent.py'], ['-m', 'src.dialux_agent']])
def test_tile_grid_cli(entry, tmp_path):
    import hashlib
    from test_cad_grid import fixture
    path = fixture(tmp_path)
    request = tmp_path/'request.json'
    request.write_text(json.dumps(dict(path=str(path), expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                      layer='Tiles', storey_origin_m=[10,20], storey_rotation_deg=13)))
    run = subprocess.run([sys.executable, *entry, 'drawing-read-tile-grid', '--request', str(request)],
                         cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr+run.stdout
    assert json.loads(run.stdout)['tile_count'] == 4


@pytest.mark.parametrize('entry', [['src/dialux_agent.py'], ['-m', 'src.dialux_agent']])
def test_tile_coverage_cli_reports_missing_cell(entry, tmp_path):
    from test_tile_coverage import inputs
    layout, grid_request = inputs(tmp_path, x=1.5)
    request = tmp_path/'coverage.json'
    request.write_text(json.dumps(dict(layout=layout, grid_request=grid_request)))
    run = subprocess.run([sys.executable,*entry,'layout-verify-tile-coverage','--request',str(request)],
                         cwd=ROOT,capture_output=True,text=True)
    assert run.returncode == 0, run.stderr+run.stdout
    assert not json.loads(run.stdout)['all_supplied_footprints_covered']
