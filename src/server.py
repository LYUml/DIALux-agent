"""stdio MCP sharing the same validated backend as the CLI."""
from mcp.server.mcpserver import MCPServer
if __package__:
    from .layout import plan_grid
    from .cad import drawing_convert, drawing_inspect, export_layout_dxf, verify_layout_native
    from .backend import create_room, inspect_stf
    from .dialux_agent import inventory, verify
    from .regulations import evaluate_profile
    from .results import read_summary_pdf
    from .workflow import check_report
    from .desktop import desktop_edit_arrangement, desktop_status, desktop_save, desktop_calculate, desktop_open, desktop_launch, desktop_import_stf, desktop_save_as, desktop_import_luminaire, desktop_arrange_space, desktop_export_pdf
else:
    from layout import plan_grid
    from cad import drawing_convert, drawing_inspect, export_layout_dxf, verify_layout_native
    from backend import create_room, inspect_stf
    from dialux_agent import inventory, verify
    from regulations import evaluate_profile
    from results import read_summary_pdf
    from workflow import check_report
    from desktop import desktop_edit_arrangement, desktop_status, desktop_save, desktop_calculate, desktop_open, desktop_launch, desktop_import_stf, desktop_save_as, desktop_import_luminaire, desktop_arrange_space, desktop_export_pdf

server = MCPServer('DIALux-agent', instructions='Geometry tools do not run lighting calculations. Preserve source files; report unverified capabilities explicitly.')
server.tool()(create_room)
server.tool()(plan_grid)
server.tool()(drawing_convert)
server.tool()(drawing_inspect)
server.tool()(export_layout_dxf)
server.tool()(verify_layout_native)
server.tool()(inspect_stf)
server.tool()(inventory)
server.tool()(verify)
server.tool()(evaluate_profile)
server.tool()(read_summary_pdf)
server.tool()(check_report)
server.tool()(desktop_status)
server.tool()(desktop_edit_arrangement)
server.tool()(desktop_save)
server.tool()(desktop_calculate)
server.tool()(desktop_open)
server.tool()(desktop_launch)
server.tool()(desktop_import_stf)
server.tool()(desktop_save_as)
server.tool()(desktop_import_luminaire)
server.tool()(desktop_arrange_space)
server.tool()(desktop_export_pdf)

if __name__ == '__main__':
    server.run()
