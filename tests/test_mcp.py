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
                assert {'create_room','inspect_stf','inventory','evaluate_profile','read_summary_pdf'} <= {t.name for t in listing.tools}
                spec=json.loads((ROOT/'examples/validation-room.json').read_text())
                path=tmp_path/'mcp-room.stf'
                result=await session.call_tool('create_room',{'spec':spec,'output':str(path)})
                assert not result.is_error
                assert path.is_file()
                readback=await session.call_tool('inspect_stf',{'path':str(path)})
                assert not readback.is_error
                assert 'Agent validation room' in str(readback)
    asyncio.run(run())
