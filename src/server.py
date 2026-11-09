"""stdio MCP sharing the same validated backend as the CLI."""
from mcp.server.mcpserver import MCPServer
if __package__:
    from .schedule import build_luminaire_schedule
    from .workplane import read_workplane_pdf
    from .report_layout import read_report_layout
    from .inspection import verify_group_checkpoint
    from .verification import verify_room_addition
    from .placement import inspect_group_checkpoint, apply_grid_layout
    from .layout import plan_grid, verify_observed_layout
    from .cad_geometry import drawing_extract_boundary
    from .cad import export_observed_layout_dxf, drawing_convert, drawing_inspect, export_layout_dxf, verify_layout_native, plot_layout_native
    from .backend import create_rooms, create_room, inspect_stf
    from .dialux_agent import inventory, verify
    from .regulations import evaluate_profile
    from .results import read_summary_pdf, read_report_pdf
    from .workflow import calculation_checkpoint, check_report, check_report_summary
    from .desktop import desktop_read_furniture, desktop_arrange_room, desktop_room_context, desktop_read_space, desktop_close_project, desktop_edit_fixture, desktop_group_fixtures, desktop_project_tree, desktop_edit_arrangement, desktop_status, desktop_save, desktop_calculate, desktop_open, desktop_launch, desktop_import_stf, desktop_save_as, desktop_import_luminaire, desktop_arrange_space, desktop_export_pdf
else:
    from schedule import build_luminaire_schedule
    from workplane import read_workplane_pdf
    from report_layout import read_report_layout
    from inspection import verify_group_checkpoint
    from verification import verify_room_addition
    from placement import inspect_group_checkpoint, apply_grid_layout
    from layout import plan_grid, verify_observed_layout
    from cad_geometry import drawing_extract_boundary
    from cad import export_observed_layout_dxf, drawing_convert, drawing_inspect, export_layout_dxf, verify_layout_native, plot_layout_native
    from backend import create_rooms, create_room, inspect_stf
    from dialux_agent import inventory, verify
    from regulations import evaluate_profile
    from results import read_summary_pdf, read_report_pdf
    from workflow import calculation_checkpoint, check_report, check_report_summary
    from desktop import desktop_read_furniture, desktop_arrange_room, desktop_room_context, desktop_read_space, desktop_close_project, desktop_edit_fixture, desktop_group_fixtures, desktop_project_tree, desktop_edit_arrangement, desktop_status, desktop_save, desktop_calculate, desktop_open, desktop_launch, desktop_import_stf, desktop_save_as, desktop_import_luminaire, desktop_arrange_space, desktop_export_pdf

server = MCPServer('DIALux-agent', instructions='Geometry tools do not run lighting calculations. Preserve source files; report unverified capabilities explicitly.')
server.tool()(create_room)
server.tool()(create_rooms)
server.tool()(plan_grid)
server.tool()(apply_grid_layout)
server.tool()(inspect_group_checkpoint)
server.tool()(desktop_read_furniture)
server.tool()(verify_group_checkpoint)
server.tool()(read_report_layout)
server.tool()(read_workplane_pdf)
server.tool()(build_luminaire_schedule)
server.tool()(verify_room_addition)
server.tool()(verify_observed_layout)
server.tool()(drawing_convert)
server.tool()(drawing_inspect)
server.tool()(drawing_extract_boundary)
server.tool()(export_layout_dxf)
server.tool()(export_observed_layout_dxf)
server.tool()(verify_layout_native)
server.tool()(plot_layout_native)
server.tool()(inspect_stf)
server.tool()(inventory)
server.tool()(verify)
server.tool()(evaluate_profile)
server.tool()(read_summary_pdf)
server.tool()(read_report_pdf)
server.tool()(check_report)
server.tool()(check_report_summary)
server.tool()(calculation_checkpoint)
server.tool()(desktop_status)
server.tool()(desktop_close_project)
server.tool()(desktop_read_space)
server.tool()(desktop_room_context)
server.tool()(desktop_project_tree)
server.tool()(desktop_group_fixtures)
server.tool()(desktop_edit_fixture)
server.tool()(desktop_edit_arrangement)
server.tool()(desktop_save)
server.tool()(desktop_calculate)
server.tool()(desktop_open)
server.tool()(desktop_launch)
server.tool()(desktop_import_stf)
server.tool()(desktop_save_as)
server.tool()(desktop_import_luminaire)
server.tool()(desktop_arrange_space)
server.tool()(desktop_arrange_room)
server.tool()(desktop_export_pdf)

if __name__ == '__main__':
    server.run()
