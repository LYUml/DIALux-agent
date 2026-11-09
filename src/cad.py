"""Read-only CAD survey using installed AutoCAD and the existing ezdxf dependency."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import math

import ezdxf


def export_layout_dxf(spec: dict, output: str, layout: dict | None = None) -> dict:
    """Export the shared planned fixtures as editable CAD blocks, with ID readback.

    This exports a generic tool-test drawing, not a submission sheet or a
    photometrically verified design. The original architectural DWG is untouched.
    """
    if __package__:
        from .layout import plan_grid
    else:
        from layout import plan_grid
    expected = plan_grid(spec)
    if layout is None:
        layout = expected
    if layout != expected:
        raise ValueError('Layout does not match the supplied specification; regenerate or review the plan')
    target = Path(output).resolve()
    if target.suffix.lower() != '.dxf' or target.exists():
        raise ValueError('Choose a new .dxf output path')
    doc = ezdxf.new('R2018')
    doc.units = 6  # metres, matching shared layout coordinates
    for layer, color in [('ROOM', 7), ('KEEP_OUT', 1), ('LUMINAIRES', 3), ('LABELS', 7), ('NOTES', 7)]:
        doc.layers.new(layer, dxfattribs={'color': color})
    model = doc.modelspace()
    model.add_lwpolyline(spec['contour'], close=True, dxfattribs={'layer': 'ROOM'})
    for region in spec.get('exclusions', []):
        model.add_lwpolyline(region, close=True, dxfattribs={'layer': 'KEEP_OUT'})
    width, depth = spec['fixture']['width_m'], spec['fixture']['depth_m']
    symbol = doc.blocks.new('DIALUX_AGENT_PANEL')
    symbol.add_lwpolyline([(-width/2,-depth/2),(width/2,-depth/2),(width/2,depth/2),(-width/2,depth/2)], close=True)
    symbol.add_line((-width/2,-depth/2),(width/2,depth/2))
    symbol.add_attdef('FIXTURE_ID', (0,-depth/2-.18), height=.12)
    handles = {}
    for fixture in layout['fixtures']:
        x, y, z = fixture['position_m']
        insert = model.add_blockref(symbol.name, (x,y,0), dxfattribs={'layer':'LUMINAIRES','rotation':fixture['rotation_deg']})
        insert.add_auto_attribs({'FIXTURE_ID':fixture['id']})
        handles[fixture['id']] = insert.dxf.handle
    xs, ys = zip(*spec['contour'])
    tx, ty = max(xs)+1, max(ys)
    notes = ['DIALux-agent | SYNTHETIC TOOL TEST', 'NOT FOR SUBMISSION OR CONSTRUCTION',
             f"Fixtures: {layout['fixture_count']} | Units: metres",
             f"Product: {spec['fixture']['product_id']}",
             f"Mounting height: {spec['fixture']['mounting_height_m']} m",
             'Green blocks: fixtures; red: placement keep-out',
             'No simulated performance or compliance claimed',
             'Specification SHA256:', layout['input_sha256']]
    for index, text in enumerate(notes):
        model.add_text(text, dxfattribs={'height':.18,'layer':'NOTES','insert':(tx,ty-index*.4)})
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8') as stream:
        doc.write(stream)
    reopened = ezdxf.readfile(target)
    inserts = list(reopened.modelspace().query('INSERT[layer=="LUMINAIRES"]'))
    by_id = {e.get_attrib_text('FIXTURE_ID'): e for e in inserts}
    if len(by_id) != len(inserts) or set(by_id) != set(handles) or reopened.units != 6:
        raise ValueError('Exported CAD identity/count/units readback failed')
    for fixture in layout['fixtures']:
        entity = by_id[fixture['id']]
        if any(not math.isclose(a,b,abs_tol=1e-9) for a,b in zip(tuple(entity.dxf.insert)[:2],fixture['position_m'][:2])):
            raise ValueError('Exported CAD position readback failed')
        if not math.isclose(entity.dxf.rotation,fixture['rotation_deg'],abs_tol=1e-9):
            raise ValueError('Exported CAD rotation readback failed')
    return {'schema':'dialux-agent/layout-cad/v1','path':str(target),'fixture_count':len(inserts),
            'fixture_handles':handles,'input_sha256':layout['input_sha256'],
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
            'dxf_readback_verified':True,'native_dwg_verified':False,'print_verified':False,
            'warnings':['Synthetic tool-test drawing only. Native AutoCAD opening and plotting remain separate verification gates.']}


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
