"""DIALux-agent JSON CLI: source integrity, geometry exchange and criteria checks."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from pypdfium2 import PdfiumError


def _local_module(name):
    """Support both script and package entry points without altering sys.path."""
    from importlib import import_module
    return import_module(f'.{name}', __package__) if __package__ else import_module(name)


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def inventory(source):
    root = Path(source).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Source must be a directory')
    records = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in {'.pdf', '.dwg'}:
            record = {'name': path.name, 'bytes': path.stat().st_size,
                      'sha256': fingerprint(path)}
            if path.suffix.lower() == '.dwg':
                with path.open('rb') as stream:
                    record['header'] = stream.read(6).decode('ascii', errors='replace')
                record['geometry_validated'] = False
            records.append(record)
    if not records:
        raise ValueError('No PDF or DWG inputs found')
    return {'schema': 'dialux-agent/input-manifest/v1', 'source': str(root), 'files': records}


def verify(manifest):
    if manifest.get('schema') != 'dialux-agent/input-manifest/v1':
        raise ValueError('Unsupported manifest schema')
    root = Path(manifest['source']).resolve(strict=True)
    failures = []
    if not manifest['files']:
        raise ValueError('Manifest contains no inputs')
    for record in manifest['files']:
        path = (root / record['name']).resolve()
        if path.parent != root:
            raise ValueError('Input path escapes source directory')
        if not path.is_file() or fingerprint(path) != record['sha256']:
            failures.append(record['name'])
    return {'ok': not failures, 'changed_or_missing': failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('project-recover').add_argument('--request', required=True)
    commands.add_parser('report-check-model-parameters').add_argument('--request', required=True)
    commands.add_parser('layout-verify-tile-coverage').add_argument('--request', required=True)
    commands.add_parser('drawing-read-tile-grid').add_argument('--request', required=True)
    commands.add_parser('array-execution-verify').add_argument('--evidence-directory', required=True)
    commands.add_parser('pdf-bundle-build').add_argument('--request', required=True)
    commands.add_parser('report-model-parameters').add_argument('--request', required=True)
    commands.add_parser('pdf-bundle-verify').add_argument('--evidence-directory', required=True)
    commands.add_parser('layout-apply-array').add_argument('--request', required=True)
    commands.add_parser('schedule-build').add_argument('--request', required=True)
    commands.add_parser('schedule-build-mixed').add_argument('--request', required=True)
    commands.add_parser('drawing-export-scheduled').add_argument('--request', required=True)
    commands.add_parser('drawing-export-mixed').add_argument('--request', required=True)
    commands.add_parser('layout-candidates-generate').add_argument('--request', required=True)
    commands.add_parser('layout-offset-search').add_argument('--request', required=True)
    commands.add_parser('layout-array-transform-plan').add_argument('--request', required=True)
    array_read = commands.add_parser('desktop-read-arrangement')
    array_read.add_argument('--expected-project', required=True)
    array_read.add_argument('--tree-item-id', required=True)
    commands.add_parser('inventory').add_argument('--source', required=True)
    commands.add_parser('verify').add_argument('--manifest', required=True)
    room = commands.add_parser('room-create')
    room.add_argument('--spec', required=True)
    room.add_argument('--output', required=True)
    commands.add_parser('stf-inspect').add_argument('--path', required=True)
    workplane = commands.add_parser('report-workplane-read')
    workplane.add_argument('--path', required=True)
    workplane.add_argument('--page', required=True, type=int)
    workplane.add_argument('--expected-header', required=True)
    workplane.add_argument('--expected-surface', required=True)
    report_layout = commands.add_parser('report-layout-read')
    report_layout.add_argument('--path', required=True)
    report_layout.add_argument('--first-page', required=True, type=int)
    report_layout.add_argument('--last-page', required=True, type=int)
    report_layout.add_argument('--expected-count', required=True, type=int)
    report_layout.add_argument('--expected-header', required=True)
    commands.add_parser('report-arrangements-read').add_argument('--request', required=True)
    commands.add_parser('report-read').add_argument('--path', required=True)
    commands.add_parser('report-read-all').add_argument('--path', required=True)
    commands.add_parser('layout-plan').add_argument('--spec', required=True)
    apply_layout = commands.add_parser('layout-apply-grid')
    apply_layout.add_argument('--spec', required=True)
    apply_layout.add_argument('--expected-project', required=True)
    apply_layout.add_argument('--group-id', required=True)
    apply_layout.add_argument('--evidence-directory', required=True)
    addition_check = commands.add_parser('room-addition-verify')
    addition_check.add_argument('--evidence', required=True)
    compare = commands.add_parser('layout-verify-observed')
    compare.add_argument('--layout', required=True)
    compare.add_argument('--observed', required=True)
    layout_export = commands.add_parser('layout-export-dxf')
    layout_export.add_argument('--spec', required=True)
    layout_export.add_argument('--layout')
    layout_export.add_argument('--output', required=True)
    native_plot = commands.add_parser('layout-plot-native')
    native_plot.add_argument('--path', required=True)
    native_plot.add_argument('--output-directory', required=True)
    native_plot.add_argument('--fixture-ids', nargs='+', required=True)
    native_plot.add_argument('--scale-denominator', type=int)
    native_plot.add_argument('--scale-outline')
    native_plot.add_argument('--paper', choices=['A3','A2','A1','A0'], default='A3')
    native_layout = commands.add_parser('layout-verify-native')
    native_layout.add_argument('--path', required=True)
    native_layout.add_argument('--output-directory', required=True)
    native_layout.add_argument('--executable', default='C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe')
    cad = commands.add_parser('drawing-convert')
    cad.add_argument('--path', required=True)
    cad.add_argument('--output-directory', required=True)
    cad.add_argument('--executable', default='C:/Program Files/Autodesk/AutoCAD 2027/accoreconsole.exe')
    drawing = commands.add_parser('drawing-inspect')
    drawing.add_argument('--path', required=True)
    drawing.add_argument('--grid-layer', default='Ceiling Grid')
    edit_arrangement = commands.add_parser('desktop-edit-arrangement')
    edit_arrangement.add_argument('--expected-project', required=True)
    edit_arrangement.add_argument('--tree-item-id', required=True)
    edit_arrangement.add_argument('--values', required=True, help='Path to JSON parameter object')
    fixture_edit = commands.add_parser('desktop-edit-fixture')
    fixture_edit.add_argument('--expected-project', required=True)
    fixture_edit.add_argument('--parameters', required=True, help='JSON file with runtime_id, expected_position_m and position_m')
    fixtures = commands.add_parser('desktop-group-fixtures')
    fixtures.add_argument('--expected-project', required=True)
    fixtures.add_argument('--group-id', required=True)
    fixtures.add_argument('--offset', type=int, default=0)
    fixtures.add_argument('--limit', type=int, default=4)
    fixtures.add_argument('--inventory-token')
    fixtures.add_argument('--expected-count', type=int)
    tree = commands.add_parser('desktop-project-tree')
    tree.add_argument('--expected-project', required=True)
    tree.add_argument('--expand-id')
    context_room = commands.add_parser('desktop-room-context')
    context_room.add_argument('--expected-project', required=True)
    context_room.add_argument('--room-name')
    space = commands.add_parser('desktop-read-space')
    space.add_argument('--expected-project', required=True)
    space.add_argument('--tree-item-id', required=True)
    close = commands.add_parser('desktop-close-project')
    close.add_argument('--expected-project', required=True)
    close.add_argument('--save-current', action='store_true')
    rooms = commands.add_parser('rooms-create')
    rooms.add_argument('--spec', required=True)
    rooms.add_argument('--output', required=True)
    checkpoint = commands.add_parser('calculation-checkpoint')
    candidates = commands.add_parser('layout-candidates-run')
    candidates.add_argument('--request', required=True)
    checkpoint.add_argument('--expected-project', required=True)
    checkpoint.add_argument('--evidence-directory', required=True)
    checkpoint.add_argument('--checks', required=True)
    checkpoint.add_argument('--recalculate', action='store_true')
    boundary = commands.add_parser('drawing-extract-boundary')
    boundary.add_argument('--request', required=True)
    observed_cad = commands.add_parser('drawing-export-observed')
    observed_cad.add_argument('--request', required=True)
    scan_check = commands.add_parser('group-inspection-verify')
    scan_check.add_argument('--evidence-directory', required=True)
    scan_check.add_argument('--layout', required=True)
    furniture = commands.add_parser('desktop-read-furniture')
    furniture.add_argument('--expected-project', required=True)
    furniture.add_argument('--tree-item-id', required=True)
    scan = commands.add_parser('group-inspection-checkpoint')
    scan.add_argument('--expected-project', required=True)
    scan.add_argument('--group-id', required=True)
    scan.add_argument('--expected-count', required=True, type=int)
    scan.add_argument('--evidence-directory', required=True)
    commands.add_parser('desktop-status')
    launching = commands.add_parser('desktop-launch')
    launching.add_argument('--executable', default='C:/Program Files/DIAL GmbH/DIALux/DIALux_x64.exe')
    launching.add_argument('--runtime-temp')
    launching.add_argument('--wait-for-ready', action='store_true')
    commands.add_parser('desktop-import-stf').add_argument('--path', required=True)
    exporting = commands.add_parser('desktop-export-pdf')
    exporting.add_argument('--expected-project', required=True)
    exporting.add_argument('--path', required=True)
    room_arrangement = commands.add_parser('desktop-arrange-room')
    room_arrangement.add_argument('--expected-project', required=True)
    room_arrangement.add_argument('--spec', required=True)
    arrangement = commands.add_parser('desktop-arrange-space')
    arrangement.add_argument('--expected-project', required=True)
    arrangement.add_argument('--product-id', required=True)
    luminaire = commands.add_parser('desktop-import-luminaire')
    luminaire.add_argument('--expected-project', required=True)
    luminaire.add_argument('--path', required=True)
    luminaire.add_argument('--product-id', required=True)
    saving_as = commands.add_parser('desktop-save-as')
    saving_as.add_argument('--expected-project', required=True)
    saving_as.add_argument('--path', required=True)
    commands.add_parser('desktop-save').add_argument('--expected-project', required=True)
    calculation = commands.add_parser('desktop-calculate')
    calculation.add_argument('--expected-project', required=True)
    calculation.add_argument('--recalculate', action='store_true')
    opening = commands.add_parser('desktop-open')
    opening.add_argument('--path', required=True)
    opening.add_argument('--expected-current-project')
    opening.add_argument('--save-current', action='store_true')
    criteria = commands.add_parser('criteria-check')
    criteria.add_argument('--profile', required=True)
    criteria.add_argument('--measurements', required=True)
    criteria.add_argument('--context', help='JSON object of evidenced applicability facts')
    report_check = commands.add_parser('report-check')
    report_check.add_argument('--path', required=True)
    report_check.add_argument('--profile', required=True)
    report_check.add_argument('--summary-id', help='Exact room/scene ID from report-read-all')
    report_check.add_argument('--context', help='JSON object of evidenced applicability facts')
    args = parser.parse_args()
    try:
        if args.command == 'project-recover':
            result = _local_module('recovery').recover_saved_project(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'report-check-model-parameters':
            result = _local_module('model_parameter_check').check_model_parameters(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'layout-verify-tile-coverage':
            result = _local_module('tile_coverage').verify_layout_tile_coverage(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'drawing-read-tile-grid':
            result = _local_module('cad_grid').drawing_read_tile_grid(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'array-execution-verify':
            result = _local_module('array_audit').verify_array_execution(args.evidence_directory)
        elif args.command == 'pdf-bundle-build':
            result = _local_module('pdf_bundle').build_pdf_bundle(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'report-model-parameters':
            result = _local_module('model_parameters').read_model_parameters(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'pdf-bundle-verify':
            result = _local_module('pdf_bundle').verify_pdf_bundle(args.evidence_directory)
        elif args.command == 'layout-export-dxf':
            spec = json.loads(Path(args.spec).read_text(encoding='utf-8'))
            layout = json.loads(Path(args.layout).read_text(encoding='utf-8')) if args.layout else None
            result = _local_module('cad').export_layout_dxf(spec, args.output, layout)
        elif args.command == 'layout-plot-native':
            result = _local_module('cad').plot_layout_native(args.path, args.output_directory, args.fixture_ids, scale_denominator=args.scale_denominator, paper=args.paper, scale_outline_m=json.loads(Path(args.scale_outline).read_text(encoding='utf-8-sig')) if args.scale_outline else None)
        elif args.command == 'layout-verify-native':
            result = _local_module('cad').verify_layout_native(args.path, args.output_directory, args.executable)
        elif args.command == 'room-addition-verify':
            evidence = json.loads(Path(args.evidence).read_text(encoding='utf-8-sig'))
            result = _local_module('verification').verify_room_addition(**evidence)
        elif args.command == 'layout-verify-observed':
            result = _local_module('layout').verify_observed_layout(json.loads(Path(args.layout).read_text(encoding='utf-8')), json.loads(Path(args.observed).read_text(encoding='utf-8')))
        elif args.command == 'layout-apply-array':
            result = _local_module('desktop').apply_array_transform(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'layout-apply-grid':
            result = _local_module('placement').apply_grid_layout(json.loads(Path(args.spec).read_text(encoding='utf-8')), args.expected_project, args.group_id, args.evidence_directory)
        elif args.command == 'report-read-all':
            result = _local_module('results').read_report_pdf(args.path)
        elif args.command == 'layout-plan':
            result = _local_module('layout').plan_grid(json.loads(Path(args.spec).read_text(encoding='utf-8')))
        elif args.command == 'drawing-convert':
            result = _local_module('cad').drawing_convert(args.path, args.output_directory, args.executable)
        elif args.command == 'drawing-inspect':
            result = _local_module('cad').drawing_inspect(args.path, args.grid_layer)
        elif args.command == 'desktop-edit-arrangement':
            result = _local_module('desktop').desktop_edit_arrangement(args.expected_project, args.tree_item_id, json.loads(Path(args.values).read_text(encoding='utf-8')))
        elif args.command == 'desktop-edit-fixture':
            result = _local_module('desktop').desktop_edit_fixture(args.expected_project, **json.loads(Path(args.parameters).read_text(encoding='utf-8')))
        elif args.command == 'desktop-group-fixtures':
            result = _local_module('desktop').desktop_group_fixtures(args.expected_project, args.group_id, args.offset, args.limit, args.inventory_token, args.expected_count)
        elif args.command == 'desktop-project-tree':
            result = _local_module('desktop').desktop_project_tree(args.expected_project, args.expand_id)
        elif args.command == 'rooms-create':
            result = _local_module('backend').create_rooms(json.loads(Path(args.spec).read_text(encoding='utf-8')), args.output)
        elif args.command == 'desktop-room-context':
            result = _local_module('desktop').desktop_room_context(args.expected_project, args.room_name)
        elif args.command == 'desktop-read-space':
            result = _local_module('desktop').desktop_read_space(args.expected_project, args.tree_item_id)
        elif args.command == 'desktop-close-project':
            result = _local_module('desktop').desktop_close_project(args.expected_project, args.save_current)
        elif args.command == 'desktop-status':
            result = _local_module('desktop').desktop_status()
        elif args.command == 'desktop-launch':
            result = _local_module('desktop').desktop_launch(args.executable, args.runtime_temp, args.wait_for_ready)
        elif args.command == 'desktop-import-stf':
            result = _local_module('desktop').desktop_import_stf(args.path)
        elif args.command == 'desktop-export-pdf':
            result = _local_module('desktop').desktop_export_pdf(args.expected_project, args.path)
        elif args.command == 'schedule-build':
            result = _local_module('schedule').build_luminaire_schedule(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'schedule-build-mixed':
            result = _local_module('mixed_schedule').build_mixed_luminaire_schedule(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'drawing-export-scheduled':
            result = _local_module('cad').export_scheduled_layout_dxf(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'drawing-export-mixed':
            result = _local_module('mixed_cad').export_mixed_scheduled_layout_dxf(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'layout-candidates-generate':
            result = _local_module('candidate_search').generate_offset_candidates(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'layout-offset-search':
            result = _local_module('candidate_search').run_offset_search(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'layout-array-transform-plan':
            result = _local_module('array_transform').plan_array_transform(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'desktop-read-arrangement':
            result = _local_module('desktop').desktop_read_arrangement(args.expected_project,args.tree_item_id)
        elif args.command == 'report-workplane-read':
            result = _local_module('workplane').read_workplane_pdf(args.path,args.page,args.expected_header,args.expected_surface)
        elif args.command == 'report-layout-read':
            result = _local_module('report_layout').read_report_layout(args.path, args.first_page, args.last_page, args.expected_count, args.expected_header)
        elif args.command == 'report-arrangements-read':
            result = _local_module('report_layout').read_report_arrangements(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'group-inspection-verify':
            result = _local_module('inspection').verify_group_checkpoint(args.evidence_directory, json.loads(Path(args.layout).read_text(encoding='utf-8-sig')))
        elif args.command == 'desktop-read-furniture':
            result = _local_module('desktop').desktop_read_furniture(args.expected_project,args.tree_item_id)
        elif args.command == 'group-inspection-checkpoint':
            result = _local_module('placement').inspect_group_checkpoint(args.expected_project, args.group_id, args.expected_count, args.evidence_directory)
        elif args.command == 'drawing-export-observed':
            result = _local_module('cad').export_observed_layout_dxf(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'drawing-extract-boundary':
            result = _local_module('cad_geometry').drawing_extract_boundary(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'calculation-checkpoint':
            result = _local_module('workflow').calculation_checkpoint(args.expected_project, args.evidence_directory, json.loads(Path(args.checks).read_text(encoding='utf-8-sig')), args.recalculate)
        elif args.command == 'layout-candidates-run':
            result = _local_module('iterations').run_layout_candidates(**json.loads(Path(args.request).read_text(encoding='utf-8-sig')))
        elif args.command == 'desktop-arrange-room':
            spec = json.loads(Path(args.spec).read_text(encoding='utf-8-sig'))
            result = _local_module('desktop').desktop_arrange_room(args.expected_project, **spec)
        elif args.command == 'desktop-arrange-space':
            result = _local_module('desktop').desktop_arrange_space(args.expected_project, args.product_id)
        elif args.command == 'desktop-import-luminaire':
            result = _local_module('desktop').desktop_import_luminaire(args.expected_project, args.path, args.product_id)
        elif args.command == 'desktop-save-as':
            result = _local_module('desktop').desktop_save_as(args.expected_project, args.path)
        elif args.command == 'desktop-save':
            result = _local_module('desktop').desktop_save(args.expected_project)
        elif args.command == 'desktop-calculate':
            result = _local_module('desktop').desktop_calculate(args.expected_project, args.recalculate)
        elif args.command == 'desktop-open':
            result = _local_module('desktop').desktop_open(args.path, args.expected_current_project, args.save_current)
        elif args.command == 'room-create':
            create_room = _local_module('backend').create_room
            result = create_room(json.loads(Path(args.spec).read_text(encoding='utf-8-sig')), args.output)
        elif args.command == 'stf-inspect':
            inspect_stf = _local_module('backend').inspect_stf
            result = inspect_stf(args.path)
        elif args.command == 'report-read':
            read_summary_pdf = _local_module('results').read_summary_pdf
            result = read_summary_pdf(args.path)
        elif args.command == 'report-check':
            profile = json.loads(Path(args.profile).read_text(encoding='utf-8-sig'))
            context = json.loads(Path(args.context).read_text(encoding='utf-8-sig')) if args.context else None
            if args.summary_id:
                result = _local_module('workflow').check_report_summary(args.path, args.summary_id, profile, context)
            else:
                result = _local_module('workflow').check_report(args.path, profile, context)
        elif args.command == 'criteria-check':
            evaluate_profile = _local_module('regulations').evaluate_profile
            result = evaluate_profile(
                json.loads(Path(args.profile).read_text(encoding='utf-8-sig')),
                json.loads(Path(args.measurements).read_text(encoding='utf-8-sig')),
                json.loads(Path(args.context).read_text(encoding='utf-8-sig')) if args.context else None)
        else:
            result = inventory(args.source) if args.command == 'inventory' else verify(
                json.loads(Path(args.manifest).read_text(encoding='utf-8-sig')))
        print(json.dumps(result, ensure_ascii=True, indent=2))
        if args.command in {'criteria-check', 'report-check', 'calculation-checkpoint'}:
            return {'pass': 0, 'fail': 1, 'unverified': 3}[result['status']]
        return 0 if result.get('ok', True) else 1
    except (OSError, ValueError, KeyError, TypeError, PdfiumError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
