"""Reproducible synthetic CAD acceptance: run as python -m scripts.validate_native_tile_grid."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess

import ezdxf

from src.cad import drawing_convert
from src.cad_grid import drawing_read_tile_grid


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(output_directory, executable):
    root = Path(output_directory).resolve()
    core = Path(executable).resolve(strict=True)
    if core.name.lower() != 'accoreconsole.exe':
        raise ValueError('Expected installed AutoCAD Core Console')
    if root.exists() or not str(root).isascii():
        raise ValueError('Choose a new ASCII output directory')
    root.mkdir(parents=True)
    state = {'state': 'running', 'synthetic_only': True, 'tile_count': 2800}
    def persist():
        (root/'journal.json').write_text(json.dumps(state, indent=2), encoding='utf-8')
    persist()
    try:
        doc = ezdxf.new('R2018'); doc.units = 4
        angle = math.radians(23)
        for iy in range(40):
            for ix in range(70):
                points = []
                for dx, dy in [(0,0),(600,0),(600,300),(0,300)]:
                    x, y = ix*600+dx, iy*300+dy
                    points.append((10000+x*math.cos(angle)-y*math.sin(angle),
                                   20000+x*math.sin(angle)+y*math.cos(angle)))
                doc.modelspace().add_lwpolyline(points, close=True, dxfattribs={'layer':'Synthetic Tiles'})
        source = root/'synthetic.dxf'; doc.saveas(source)
        original = fingerprint(source)
        def extract(path):
            return drawing_read_tile_grid(str(path),fingerprint(path),'Synthetic Tiles',[10,20],13)
        before = extract(source)
        copied = root/'native-input.dxf'; shutil.copy2(source,copied)
        dwg = root/'native.dwg'; script = root/'save.scr'
        script.write_text('(setvar "FILEDIA" 0)\n(command "_.SAVEAS" "_2018" '
                          +json.dumps(dwg.as_posix())+')\n(princ "TILE_NATIVE_SAVED")\n(princ)\n',encoding='ascii')
        try:
            run = subprocess.run([str(core),'/i',str(copied),'/s',str(script),'/product','ACAD','/l','en-US'],
                                 capture_output=True,timeout=90,cwd=root)
        except subprocess.TimeoutExpired as exc:
            (root/'console.log').write_text((exc.stdout or b'').decode('utf-16le',errors='replace'),encoding='utf-8')
            raise ValueError('Native save timed out; preserve this directory for inspection') from exc
        log = run.stdout.decode('utf-16le',errors='replace')
        (root/'console.log').write_text(log,encoding='utf-8')
        if run.returncode or 'TILE_NATIVE_SAVED' not in log or '; error:' in log.lower() or not dwg.is_file():
            raise ValueError('Native save failed; inspect console.log')
        converted = drawing_convert(str(dwg),str(root/'reopened'),str(core))
        after = extract(Path(converted['dxf']))
        if before['tile_count'] != 2800 or after['tile_count'] != 2800:
            raise ValueError('Native tile count differs')
        cells = lambda result: sorted(tuple(t['cell']) for t in result['tiles'])
        if cells(before) != cells(after):
            raise ValueError('Native grid cells differ')
        for key, first in before['grid'].items():
            second = after['grid'][key]
            error = max(abs(a-b) for a,b in zip(first,second)) if isinstance(first,list) else abs(first-second)
            if error > 1e-8:
                raise ValueError('Native grid parameter differs: '+key)
        if fingerprint(source) != original:
            raise ValueError('Original synthetic source changed')
        evidence = dict(before=before,after=after,native_variables=converted['native_variables'])
        evidence_path = root/'evidence.json'
        evidence_path.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        state.update(state='verified',original_sha256=original,native_dwg_sha256=fingerprint(dwg),
                     converted_dxf_sha256=converted['dxf_sha256'],evidence_sha256=fingerprint(evidence_path),
                     all_cells_and_grid_parameters_match=True,original_unchanged=True,
                     semantic_ceiling_verified=False,native_dialux_placement_verified=False)
        persist()
        return state
    except Exception as exc:
        state.update(state='failed',error=str(exc)); persist()
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory',required=True)
    parser.add_argument('--executable',default='C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe')
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.output_directory,args.executable),indent=2))
    except (ValueError,OSError) as exc:
        print(json.dumps({'state':'rejected_or_failed','error':str(exc)}))
        raise SystemExit(2)
