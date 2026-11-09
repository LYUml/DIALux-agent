"""Read-only CAD survey using installed AutoCAD and the existing ezdxf dependency."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import ezdxf


def drawing_convert(path: str, output_directory: str,
                    executable: str = 'C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe') -> dict:
    """Export a copied DWG through native AutoCAD; never open the original for writing."""
    source = Path(path).resolve(strict=True)
    core = Path(executable).resolve(strict=True)
    destination = Path(output_directory).resolve()
    if source.suffix.lower() != '.dwg' or core.name.lower() != 'accoreconsole.exe':
        raise ValueError('Expected DWG input and installed accoreconsole.exe')
    if destination.exists():
        raise ValueError('Choose a new output directory; existing survey data is preserved')
    if not str(destination).isascii():
        raise ValueError('Native survey currently requires an ASCII output directory')
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    destination.mkdir(parents=True)
    copy = destination / 'source-copy.dwg'
    shutil.copy2(source, copy)
    output = destination / 'source-copy.dxf'
    audit = destination / 'native-vars.txt'
    script = destination / 'survey.scr'
    quoted = lambda p: json.dumps(p.as_posix())
    commands = ['(setvar "FILEDIA" 0)', f'(setq f (open {quoted(audit)} "w"))',
                '(foreach n \'("ACADVER" "INSUNITS" "LUNITS" "MEASUREMENT" "EXTMIN" "EXTMAX") (write-line (strcat n "=" (vl-princ-to-string (getvar n))) f))',
                '(close f)', f'(command "_.DXFOUT" {quoted(output)} "16")',
                '(princ "DIALUX_SURVEY_COMPLETE")', '(princ)']
    script.write_text('\n'.join(commands) + '\n', encoding='ascii')
    try:
        result = subprocess.run([str(core), '/i', str(copy), '/s', str(script), '/l', 'en-US'],
                                capture_output=True, timeout=90, cwd=destination)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Native survey timed out; inspect its output directory before retrying') from exc
    log = result.stdout.decode('utf-16le', errors='replace')
    (destination / 'console.log').write_text(log, encoding='utf-8')
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise ValueError('Original DWG hash changed during survey')
    if result.returncode or 'DIALUX_SURVEY_COMPLETE' not in log or '; error:' in log.lower() or not output.is_file():
        raise ValueError('Native DXF export not verified; inspect console.log')
    native = dict(line.split('=', 1) for line in audit.read_text().splitlines() if '=' in line)
    evidence = {'schema': 'dialux-agent/native-cad-survey/v1', 'source': str(source),
                'source_sha256': before, 'original_unchanged': True, 'dxf': str(output),
                'dxf_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                'native_variables': native, 'geometry_verified': False}
    (destination / 'manifest.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    return evidence


def drawing_inspect(path: str, grid_layer: str = 'Ceiling Grid') -> dict:
    """Inventory DXF entities and closed straight grid cells; do not infer a room boundary."""
    source = Path(path).resolve(strict=True)
    if source.suffix.lower() != '.dxf':
        raise ValueError('Expected native-exported DXF')
    doc = ezdxf.readfile(source)
    model = doc.modelspace()
    texts, cells = [], []
    for entity in model:
        if entity.dxftype() in {'TEXT', 'MTEXT'}:
            texts.append({'handle': entity.dxf.handle, 'layer': entity.dxf.layer,
                          'text': entity.plain_text() if entity.dxftype() == 'MTEXT' else entity.dxf.text,
                          'position': list(entity.dxf.insert)})
        if entity.dxftype() == 'LWPOLYLINE' and entity.dxf.layer == grid_layer and entity.closed:
            points = list(entity.get_points('xyb'))
            if len(points) == 4 and all(bulge == 0 for _, _, bulge in points):
                cells.append({'handle': entity.dxf.handle, 'vertices': [[x, y] for x, y, _ in points]})
    return {'schema': 'dialux-agent/dxf-inventory/v1', 'source': str(source),
            'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'insunits': doc.units,
            'entity_counts': dict(Counter(e.dxftype() for e in model)),
            'layer_counts': dict(Counter(e.dxf.layer for e in model)),
            'texts': texts, 'grid_layer': grid_layer, 'closed_four_vertex_grid_candidates': cells,
            'room_boundary_verified': False,
            'warnings': ['INSUNITS and annotations need scale cross-checks. Grid candidates are not validated ceiling tiles or room boundaries.',
                         'DXF inventory does not replace native DWG and plotted visual review.']}
