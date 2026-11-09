"""Read-only CAD survey using installed AutoCAD and the existing ezdxf dependency."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import math

import ezdxf

if __package__:
    from .cad_labels import place_fixture_labels
    from .cad_dimensions import add_dimensions, dimension_records, compare_dimensions, validate_dimensions
else:
    from cad_labels import place_fixture_labels
    from cad_dimensions import add_dimensions, dimension_records, compare_dimensions, validate_dimensions


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
    return _write_layout_dxf(spec, output, layout)


def export_observed_layout_dxf(spec: dict, observed: dict, fixture_ids: list[str], output: str) -> dict:
    """Export supplied native fixture positions, preserving explicit IDs and evidence hashes.

    Requires boundary/fixture assumptions and validates envelopes. No grid regeneration
    or native simulation proof. Produces a clearly labelled synthetic test drawing.
    """
    if __package__:
        from .design_data import observed_layout
    else:
        from design_data import observed_layout
    layout = observed_layout(spec, observed, fixture_ids)
    result = _write_layout_dxf(spec, output, layout)
    result['observed_layout'] = layout
    return result


def _write_layout_dxf(spec, output, layout):
    dimensions = validate_dimensions(spec.get('dimensions', []))
    target = Path(output).resolve()
    if target.suffix.lower() != '.dxf' or target.exists():
        raise ValueError('Choose a new .dxf output path')
    annotations=spec.get('annotations', {})
    if not isinstance(annotations,dict) or set(annotations)-{'fixture_height_m','note_height_m'}:
        raise ValueError('Unsupported drawing annotations')
    label_height=annotations.get('fixture_height_m',.12)
    note_height=annotations.get('note_height_m',.18)
    if any(type(v) not in (int,float) or not math.isfinite(v) or not .02<=v<=2 for v in (label_height,note_height)):
        raise ValueError('Drawing text heights must be finite metres between 0.02 and 2')
    label_positions = place_fixture_labels(spec, layout, label_height)
    doc = ezdxf.new('R2018')
    doc.units = 6  # metres, matching shared layout coordinates
    doc.styles.get('Standard').dxf.font = 'arial.ttf'
    for layer, color in [('ROOM', 7), ('KEEP_OUT', 1), ('LUMINAIRES', 3), ('LABELS', 7), ('NOTES', 7)]:
        doc.layers.new(layer, dxfattribs={'color': color})
    model = doc.modelspace()
    add_dimensions(doc, dimensions, label_height)
    model.add_lwpolyline(spec['contour'], close=True, dxfattribs={'layer': 'ROOM'})
    for region in spec.get('exclusions', []):
        model.add_lwpolyline(region, close=True, dxfattribs={'layer': 'KEEP_OUT'})
    width, depth = spec['fixture']['width_m'], spec['fixture']['depth_m']
    symbol = doc.blocks.new('DIALUX_AGENT_PANEL')
    symbol.add_lwpolyline([(-width/2,-depth/2),(width/2,-depth/2),(width/2,depth/2),(-width/2,depth/2)], close=True)
    symbol.add_line((-width/2,-depth/2),(width/2,depth/2))
    symbol.add_attdef('FIXTURE_ID', (0,-depth/2-label_height*1.5), height=label_height)
    handles = {}
    for fixture in layout['fixtures']:
        x, y, z = fixture['position_m']
        insert = model.add_blockref(symbol.name, (x,y,0), dxfattribs={'layer':'LUMINAIRES','rotation':fixture['rotation_deg']})
        insert.add_auto_attribs({'FIXTURE_ID':fixture['id']})
        label = insert.get_attrib('FIXTURE_ID')
        label.dxf.rotation = 0
        label.set_placement(label_positions[fixture['id']]['center_m'],
                            align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        handles[fixture['id']] = insert.dxf.handle
    xs, ys = zip(*spec['contour'])
    tx, ty = max(xs)+1, max(ys)
    notes = ['DIALux-agent | SYNTHETIC TOOL TEST', 'NOT FOR SUBMISSION OR CONSTRUCTION',
             f"Fixtures: {layout['fixture_count']} | Units: metres",
             f"Product: {spec['fixture']['product_id']}",
             f"Mounting height: {spec['fixture']['mounting_height_m']} m",
             'Plot scale: fit to page (not to scale)',
             'LUMINAIRES: fixtures; KEEP_OUT: no placement',
             'No simulated performance or compliance claimed',
             'Specification SHA256:', layout['input_sha256'][:32], layout['input_sha256'][32:]]
    if layout.get('observations_sha256'):
        notes += ['Native observation snapshot SHA256:', layout['observations_sha256'][:32],
                  layout['observations_sha256'][32:], 'Product and envelope dimensions: supplied assumptions']
    for index, text in enumerate(notes):
        model.add_text(text, dxfattribs={'height':note_height,'layer':'NOTES','insert':(tx,ty-index*note_height*20/9)})
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
            'label_placement':label_positions, 'label_envelopes_verified':True,
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
        result = subprocess.run([str(core), '/i', str(copy), '/s', str(script), '/product', 'ACAD', '/l', 'en-US'],
                                capture_output=True, timeout=90, cwd=destination)
    except subprocess.TimeoutExpired as exc:
        (destination / 'console.log').write_text((exc.stdout or b'').decode('utf-16le', errors='replace'), encoding='utf-8')
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


def _fixture_records(path: Path) -> dict:
    doc = ezdxf.readfile(path)
    records = {}
    for entity in doc.modelspace().query('INSERT[layer=="LUMINAIRES"]'):
        identity = entity.get_attrib_text('FIXTURE_ID')
        if not identity or identity in records:
            raise ValueError('Missing or duplicate fixture ID')
        records[identity] = {'position': tuple(entity.dxf.insert), 'rotation': entity.dxf.rotation,
                             'scale': (entity.dxf.xscale, entity.dxf.yscale, entity.dxf.zscale),
                             'block': entity.dxf.name}
        label = entity.get_attrib('FIXTURE_ID')
        # AutoCAD recomputes the glyph-origin insert for aligned text. Compare
        # the authoritative alignment anchor instead of that derived origin.
        anchor = label.dxf.align_point if label.dxf.halign or label.dxf.valign else label.dxf.insert
        records[identity]['label'] = (*anchor,
                                     label.dxf.rotation, label.dxf.height,
                                     label.dxf.halign, label.dxf.valign)
    if not records or doc.units != 6:
        raise ValueError('Expected nonempty metre-unit agent layout')
    return records


def verify_layout_native(path: str, output_directory: str,
                         executable: str = 'C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe') -> dict:
    """Save a synthetic DXF as native DWG, reopen it and compare fixture records.

    This verifies identity, insertion coordinates, rotation and scale, not plotting
    or block-shape fidelity. All writes stay in a new output directory.
    """
    source = Path(path).resolve(strict=True)
    core = Path(executable).resolve(strict=True)
    destination = Path(output_directory).resolve()
    if source.suffix.lower() != '.dxf' or core.name.lower() != 'accoreconsole.exe':
        raise ValueError('Expected DXF and installed accoreconsole.exe')
    before = _fixture_records(source)
    dimensions_before = dimension_records(source)
    if destination.exists() or not str(destination).isascii():
        raise ValueError('Choose a new ASCII output directory')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    destination.mkdir(parents=True)
    copied = destination / 'input.dxf'
    shutil.copy2(source, copied)
    native = destination / 'layout.dwg'
    script = destination / 'save.scr'
    script.write_text('(setvar "FILEDIA" 0)\n'
                      + '(command "_.SAVEAS" "_2018" ' + json.dumps(native.as_posix()) + ')\n'
                      + '(princ "LAYOUT_NATIVE_COMPLETE")\n(princ)\n', encoding='ascii')
    try:
        result = subprocess.run([str(core), '/i', str(copied), '/s', str(script), '/product', 'ACAD', '/l', 'en-US'],
                                capture_output=True, timeout=90, cwd=destination)
    except subprocess.TimeoutExpired as exc:
        (destination / 'save.log').write_text((exc.stdout or b'').decode('utf-16le', errors='replace'), encoding='utf-8')
        raise ValueError('Native save timed out; inspect output before retrying') from exc
    log = result.stdout.decode('utf-16le', errors='replace')
    (destination / 'save.log').write_text(log, encoding='utf-8')
    if result.returncode or 'LAYOUT_NATIVE_COMPLETE' not in log or '; error:' in log.lower() or not native.is_file():
        raise ValueError('Native save failed; inspect save.log')
    reopened = drawing_convert(str(native), str(destination / 'reopened'), str(core))
    after = _fixture_records(Path(reopened['dxf']))
    dimensions_after = dimension_records(Path(reopened['dxf']))
    compare_dimensions(dimensions_before, dimensions_after)
    if set(before) != set(after):
        raise ValueError('Native fixture IDs changed')
    for identity, record in before.items():
        other = after[identity]
        if record['block'] != other['block'] or any(
            not math.isclose(a, b, rel_tol=0, abs_tol=1e-8)
            for a, b in zip((*record['position'], record['rotation'], *record['scale'], *record['label']),
                            (*other['position'], other['rotation'], *other['scale'], *other['label']))):
            raise ValueError(f'Native fixture geometry changed: {identity}')
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('Source DXF changed')
    evidence = {'schema': 'dialux-agent/native-layout/v1', 'source': str(source),
                'source_sha256': digest, 'original_unchanged': True, 'dwg': str(native),
                'dwg_sha256': hashlib.sha256(native.read_bytes()).hexdigest(),
                'fixture_count': len(after), 'fixture_records_verified': True,
                'dimension_count': len(dimensions_after), 'dimension_records_verified': True,
                'native_reopen_verified': True, 'block_shapes_verified': False,
                'print_verified': False, 'reopen_evidence': reopened}
    (destination / 'manifest.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    return evidence


def plot_layout_native(path: str, output_directory: str, expected_fixture_ids: list[str],
                       executable: str = 'C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe',
                       scale_denominator: int | None = None, scale_outline_m: list | None = None, paper: str = 'A3') -> dict:
    """Plot a copied agent test DWG to an explicit ISO landscape PDF with text and rendered-content checks.

    Defaults to fit-to-page. Optional fixed scale requires an explicit metre
    outline and verifies its PDF vector dimensions; copied drawing must use metres.
    Visual review remains separate. Requires generated test labels and fixture IDs.
    """
    import re
    import pdfplumber
    from PIL import ImageChops, Image
    if (not isinstance(expected_fixture_ids, list) or not expected_fixture_ids
            or any(not isinstance(i, str) or not re.fullmatch(r'L\d+', i) for i in expected_fixture_ids)
            or len(set(expected_fixture_ids)) != len(expected_fixture_ids)):
        raise ValueError('Expected unique generated fixture IDs')
    if (scale_denominator is None) != (scale_outline_m is None):
        raise ValueError('Fixed scale requires both denominator and explicit outline in metres')
    if scale_denominator is not None:
        if type(scale_denominator) is not int or scale_denominator not in {25,50,100,200,500}:
            raise ValueError('Supported fixed scale denominators: 25, 50, 100, 200, 500')
        if __package__:
            from .layout import polygon
        else:
            from layout import polygon
        polygon(scale_outline_m, 'scale reference outline')
    papers={'A3':(420,297),'A2':(594,420),'A1':(841,594),'A0':(1189,841)}
    if not isinstance(paper,str) or paper not in papers:
        raise ValueError('Supported landscape paper sizes: A3, A2, A1, A0')
    paper_width,paper_height=papers[paper]
    source = Path(path).resolve(strict=True)
    core = Path(executable).resolve(strict=True)
    destination = Path(output_directory).resolve()
    if source.suffix.lower() != '.dwg' or core.name.lower() != 'accoreconsole.exe':
        raise ValueError('Expected DWG and installed accoreconsole.exe')
    if destination.exists() or not str(destination).isascii():
        raise ValueError('Choose a new ASCII output directory')
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    destination.mkdir(parents=True)
    copied = destination / 'input.dwg'
    shutil.copy2(source, copied)
    output = destination / 'layout.pdf'
    script = destination / 'plot.scr'
    arguments = ['_.-PLOT', '_Y', 'Model', 'DWG To PDF.pc3', f'ISO {paper} ({paper_width:.2f} x {paper_height:.2f} MM)',
                 '_M', '_L', '_N', '_E', f'1000={scale_denominator}' if scale_denominator else '_F', '_C', '_Y', 'monochrome.ctb', '_Y', '_A',
                 output.as_posix(), '_N', '_Y']
    preparation = ''
    if scale_denominator:
        preparation = ('(if (/= (getvar "INSUNITS") 6) (error "Fixed plot requires metre drawing units"))\n'
            '(setq daScaleNotes (ssget "_X" (list (cons 0 "TEXT") (cons 1 "Plot scale: fit to page (not to scale)"))))\n'
            '(if (or (null daScaleNotes) (/= (sslength daScaleNotes) 1)) (error "Expected one original scale note"))\n'
            '(setq daScaleEntity (ssname daScaleNotes 0) daScaleData (entget daScaleEntity))\n'
            f'(entmod (subst (cons 1 "Plot scale: 1:{scale_denominator} at {paper} (print 100%)") (assoc 1 daScaleData) daScaleData))\n')
    script.write_text('(setvar "FILEDIA" 0)\n(setvar "BACKGROUNDPLOT" 0)\n' + preparation
                      + '(command ' + ' '.join(json.dumps(a) for a in arguments) + ')\n'
                      + '(princ "NATIVE_PLOT_COMPLETE")\n(princ)\n', encoding='ascii')
    try:
        result = subprocess.run([str(core), '/i', str(copied), '/s', str(script), '/product', 'ACAD', '/l', 'en-US'],
                                capture_output=True, timeout=90, cwd=destination)
    except subprocess.TimeoutExpired as exc:
        (destination / 'console.log').write_text((exc.stdout or b'').decode('utf-16le', errors='replace'), encoding='utf-8')
        raise ValueError('Native plot timed out; inspect output before retry') from exc
    log = result.stdout.decode('utf-16le', errors='replace')
    (destination / 'console.log').write_text(log, encoding='utf-8')
    if result.returncode or '; error:' in log.lower() or 'NATIVE_PLOT_COMPLETE' not in log or not output.is_file():
        raise ValueError('Native plotting failed; inspect console.log')
    if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
        raise ValueError('Original DWG changed')
    with pdfplumber.open(output) as pdf:
        if len(pdf.pages) != 1:
            raise ValueError('Expected one plotted page')
        page = pdf.pages[0]
        text = page.extract_text() or ''
        ids = re.findall(r'\bL\d+\b', text)
        if sorted(ids) != sorted(expected_fixture_ids) or 'SYNTHETIC TOOL TEST' not in text or 'NOT FOR SUBMISSION' not in text:
            raise ValueError('Expected plot labels/fixture IDs missing or duplicated; inspect PDF')
        if abs(page.width - paper_width*72/25.4) > 2 or abs(page.height - paper_height*72/25.4) > 2:
            raise ValueError('Unexpected PDF paper dimensions')
        scale_evidence = None
        if scale_denominator:
            scale_evidence = verify_pdf_outline_scale(page.curves + page.rects, scale_outline_m, scale_denominator)
            if f'1:{scale_denominator}' not in text or 'not to scale' in text:
                raise ValueError('Fixed scale annotation missing or contradictory')
        rendered = page.to_image(resolution=120, antialias=True).original.convert('RGB')
        bounds = ImageChops.difference(rendered, Image.new('RGB', rendered.size, 'white')).convert('L').point(lambda v: 255 if v > 20 else 0).getbbox()
        if not bounds or bounds[0] < 5 or bounds[1] < 5 or bounds[2] > rendered.width-5 or bounds[3] > rendered.height-5:
            raise ValueError('Blank plot or content touches paper edge; inspect PDF')
        rendered.save(destination / 'preview.png')
        evidence = {'schema': 'dialux-agent/native-plot/v1', 'source': str(source), 'source_sha256': digest,
                    'original_unchanged': True, 'pdf': str(output), 'pdf_sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
                    'pages': 1, 'paper':paper, 'paper_size_mm':[paper_width,paper_height], 'fixture_ids': ids, 'text_labels_verified': True, 'rendered_content_bounds_px': bounds,
                    'preview': str(destination / 'preview.png'), 'plot_scale': f'1:{scale_denominator}' if scale_denominator else 'fit_to_page',
                    'scale_evidence': scale_evidence,
                    'visual_review_verified': False, 'warning': 'Synthetic tool-test plot; visual review and engineering drawing acceptance are separate.'}
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


def verify_pdf_outline_scale(curves: list, outline_m: list, denominator: int) -> dict:
    """Require one straight PDF path matching the supplied outline at physical scale."""
    if type(denominator) is not int or denominator<=0:
        raise ValueError('Positive scale denominator required')
    if __package__:
        from .layout import polygon
    else:
        from layout import polygon
    polygon(outline_m,'scale reference outline')
    outline=[tuple(p) for p in outline_m]
    if outline[0]==outline[-1]: outline.pop()
    factor=1000/denominator*72/25.4
    def normalize(points):
        minx=min(p[0] for p in points); miny=min(p[1] for p in points)
        return [(p[0]-minx,p[1]-miny) for p in points]
    expected=normalize([(x*factor,-y*factor) for x,y in outline])
    matches=[]
    for index,curve in enumerate(curves):
        if any(command[0] not in {'m','l','h'} for command in curve.get('path',[])): continue
        points=list(curve.get('pts',[]))
        if curve.get('object_type')=='rect' and len(points)==4:
            points.append(points[0])
        if len(points)!=len(outline)+1: continue
        if any(not math.isfinite(v) for point in points for v in point): continue
        if max(abs(a-b) for a,b in zip(points[0],points[-1]))>.25: continue
        actual=normalize(points[:-1])
        errors=[]
        for direction in (actual,list(reversed(actual))):
            for offset in range(len(direction)):
                rotated=direction[offset:]+direction[:offset]
                errors.append(max(abs(a-b) for p,q in zip(expected,rotated) for a,b in zip(p,q)))
        error=min(errors)
        if error<=.25: matches.append({'pdf_curve_index':index,'pdf_object_type':curve.get('object_type','curve'),'maximum_coordinate_error_pt':error})
    if len(matches)!=1:
        raise ValueError('Expected one PDF outline at the requested physical scale; found '+str(len(matches)))
    return {**matches[0],'verified':True,'denominator':denominator,'pdf_points_per_model_metre':factor,
            'coordinate_tolerance_pt':.25,'outline_sha256':hashlib.sha256(json.dumps(outline_m,sort_keys=True).encode()).hexdigest(),
            'warning':'Verifies this PDF vector outline at original page size, not downstream print scaling or all drawing dimensions.'}
