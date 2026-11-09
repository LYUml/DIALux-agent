import asyncio
import json
from pathlib import Path
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]

def test_real_stdio_tools(tmp_path):
    async def run():
        params=StdioServerParameters(command=sys.executable,args=[str(ROOT/'src/server.py')])
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write,read_timeout_seconds=15) as session:
                await session.initialize()
                listing=await session.list_tools()
                assert {'export_layout_dxf', 'verify_layout_native', 'desktop_edit_arrangement', 'desktop_project_tree', 'desktop_group_fixtures', 'verify_observed_layout', 'desktop_edit_fixture', 'apply_grid_layout', 'plot_layout_native', 'read_report_pdf', 'check_report_summary', 'create_rooms', 'desktop_close_project', 'desktop_read_space', 'desktop_room_context', 'desktop_arrange_room', 'verify_room_addition', 'calculation_checkpoint', 'drawing_extract_boundary', 'export_observed_layout_dxf', 'desktop_read_furniture', 'read_report_layout', 'verify_group_checkpoint', 'inspect_group_checkpoint'} <= {t.name for t in listing.tools}
                layout_spec=json.loads((ROOT/'examples/synthetic-grid-layout.json').read_text())
                cad_path=tmp_path/'mcp-layout.dxf'
                cad_result=await session.call_tool('export_layout_dxf',{'spec':layout_spec,'output':str(cad_path)})
                assert not cad_result.is_error
                assert cad_path.is_file()
                assert {'create_room','inspect_stf','inventory','evaluate_profile','read_summary_pdf','check_report','desktop_status','desktop_save','desktop_calculate','desktop_open','desktop_launch','desktop_import_stf','desktop_save_as','desktop_import_luminaire','desktop_arrange_space','desktop_export_pdf','drawing_convert','drawing_inspect','plan_grid'} <= {t.name for t in listing.tools}
                spec=json.loads((ROOT/'examples/validation-room.json').read_text())
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
                        'profile': json.loads((ROOT/'profiles/hk-bec2024-office-lpd.json').read_text())})
                    assert not checked.is_error
                    payload = json.loads(checked.content[0].text)
                    assert payload['status'] == 'unverified'
                    assert payload['report']['measurements'][1]['value'] == .22
    asyncio.run(run())
