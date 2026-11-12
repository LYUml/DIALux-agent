import asyncio
import json
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from test_pdf_bundle import fixture_pdf

ROOT=Path(__file__).resolve().parents[1]

def test_real_stdio_tools(tmp_path):
    async def run():
        params=StdioServerParameters(command=sys.executable,args=[str(ROOT/'src/server.py')])
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write,read_timeout_seconds=15) as session:
                await session.initialize()
                listing=await session.list_tools()
                import hashlib
                from test_cad_grid import fixture
                tiles = fixture(tmp_path)
                grid = await session.call_tool('drawing_read_tile_grid', {
                    'path': str(tiles), 'expected_sha256': hashlib.sha256(tiles.read_bytes()).hexdigest(),
                    'layer': 'Tiles', 'storey_origin_m': [10, 20], 'storey_rotation_deg': 13})
                assert not grid.is_error
                assert json.loads(grid.content[0].text)['tile_count'] == 4
                from test_tile_coverage import inputs
                coverage_layout, coverage_request = inputs(tmp_path)
                coverage = await session.call_tool('verify_layout_tile_coverage', {
                    'layout': coverage_layout, 'grid_request': coverage_request})
                assert not coverage.is_error
                assert json.loads(coverage.content[0].text)['all_supplied_footprints_covered']
                assert 'read_model_parameters' in {t.name for t in listing.tools}
                assert {'verify_array_execution','build_pdf_bundle','verify_pdf_bundle'} <= {t.name for t in listing.tools}
                source=tmp_path/'bundle-source.pdf';digest=fixture_pdf(source)
                bundle_args={'sections':[{'path':str(source),'sha256':digest,'pages':[2,1],'role':'main'}],
                             'output_directory':str(tmp_path/'bundle'),'max_main_pages':2,'max_bytes':1000000}
                bundle=await session.call_tool('build_pdf_bundle',bundle_args)
                assert not bundle.is_error
                replay=await session.call_tool('verify_pdf_bundle',{'evidence_directory':str(tmp_path/'bundle')})
                assert not replay.is_error and json.loads(replay.content[0].text)['page_count']==2
                rejected=await session.call_tool('verify_array_execution',{'evidence_directory':str(tmp_path/'bundle')})
                assert rejected.is_error
                assert 'run_layout_candidates' in {t.name for t in listing.tools}
                assert 'export_scheduled_layout_dxf' in {t.name for t in listing.tools}
                assert 'desktop_read_arrangement' in {t.name for t in listing.tools}
                assert 'generate_offset_candidates' in {t.name for t in listing.tools}
                assert 'run_offset_search' in {t.name for t in listing.tools}
                assert 'plan_array_transform' in {t.name for t in listing.tools}
                transform=await session.call_tool('plan_array_transform',json.loads((ROOT/'resources/examples/synthetic-array-transform.json').read_text()))
                assert not transform.is_error
                transform_payload=json.loads(transform.content[0].text)
                assert transform_payload['predicted_geometry']['matched_count']==6
                assert not transform_payload['native_mutation_verified']
                assert {'export_layout_dxf', 'verify_layout_native', 'desktop_edit_arrangement', 'desktop_project_tree', 'desktop_group_fixtures', 'verify_observed_layout', 'desktop_edit_fixture', 'apply_grid_layout', 'apply_array_transform', 'plot_layout_native', 'read_report_pdf', 'check_report_summary', 'create_rooms', 'desktop_close_project', 'desktop_read_space', 'desktop_room_context', 'desktop_arrange_room', 'verify_room_addition', 'calculation_checkpoint', 'drawing_extract_boundary', 'export_observed_layout_dxf', 'desktop_read_furniture', 'build_luminaire_schedule', 'build_mixed_luminaire_schedule', 'export_mixed_scheduled_layout_dxf', 'read_workplane_pdf', 'read_report_layout', 'read_report_arrangements', 'verify_group_checkpoint', 'inspect_group_checkpoint'} <= {t.name for t in listing.tools}
                layout_spec=json.loads((ROOT/'resources/examples/synthetic-grid-layout.json').read_text())
                cad_path=tmp_path/'mcp-layout.dxf'
                cad_result=await session.call_tool('export_layout_dxf',{'spec':layout_spec,'output':str(cad_path)})
                assert not cad_result.is_error
                assert cad_path.is_file()
                assert {'create_room','inspect_stf','inventory','evaluate_profile','read_summary_pdf','check_report','desktop_status','desktop_save','desktop_calculate','desktop_open','desktop_launch','desktop_import_stf','desktop_save_as','desktop_import_luminaire','desktop_arrange_space','desktop_export_pdf','drawing_convert','drawing_inspect','plan_grid'} <= {t.name for t in listing.tools}
                spec=json.loads((ROOT/'resources/examples/validation-room.json').read_text())
                path=tmp_path/'mcp-room.stf'
                result=await session.call_tool('create_room',{'spec':spec,'output':str(path)})
                assert not result.is_error
                assert path.is_file()
                readback=await session.call_tool('inspect_stf',{'path':str(path)})
                assert not readback.is_error
                assert 'Agent validation room' in str(readback)
                report = ROOT/'local/validation-summary-v2.pdf'
                if report.exists():
                    checked = await session.call_tool('check_report', {
                        'path': str(report),
                        'profile': json.loads((ROOT/'resources/profiles/hk-bec2024-office-lpd.json').read_text())})
                    assert not checked.is_error
                    payload = json.loads(checked.content[0].text)
                    assert payload['status'] == 'unverified'
                    assert payload['report']['measurements'][1]['value'] == .22
    asyncio.run(run())
