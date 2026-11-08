"""stdio MCP sharing the same validated backend as the CLI."""
from mcp.server.mcpserver import MCPServer
from backend import create_room, inspect_stf
from dialux_agent import inventory

server = MCPServer('DIALux-agent', instructions='Geometry tools do not run lighting calculations. Preserve source files; report unverified capabilities explicitly.')
server.tool()(create_room)
server.tool()(inspect_stf)
server.tool()(inventory)

if __name__ == '__main__':
    server.run()
