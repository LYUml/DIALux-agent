"""stdio MCP sharing the same validated backend as the CLI."""
from mcp.server.mcpserver import MCPServer
if __package__:
    from .backend import create_room, inspect_stf
    from .dialux_agent import inventory, verify
    from .regulations import evaluate_profile
    from .results import read_summary_pdf
    from .workflow import check_report
else:
    from backend import create_room, inspect_stf
    from dialux_agent import inventory, verify
    from regulations import evaluate_profile
    from results import read_summary_pdf
    from workflow import check_report

server = MCPServer('DIALux-agent', instructions='Geometry tools do not run lighting calculations. Preserve source files; report unverified capabilities explicitly.')
server.tool()(create_room)
server.tool()(inspect_stf)
server.tool()(inventory)
server.tool()(verify)
server.tool()(evaluate_profile)
server.tool()(read_summary_pdf)
server.tool()(check_report)

if __name__ == '__main__':
    server.run()
