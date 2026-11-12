# DIALux-agent

Control DIALux evo through a command-line interface or an MCP-compatible AI client.
Create room geometry, place luminaires, calculate lighting, save projects and export reports.

## Requirements

Windows, Python 3.12 and DIALux evo. Tested with DIALux evo 14.1.
Desktop commands require an interactive Windows session and may take foreground focus.
Native CAD conversion and plotting also require AutoCAD Core Console, with AutoCAD 2027 as the default.

## Install

Run in PowerShell:

```powershell
git clone https://github.com/LYUml/DIALux-agent.git
cd DIALux-agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m src.dialux_agent --help
```

## CLI

Start DIALux and inspect its state:

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-launch
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-status
```

Create a sample room file:

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent room-create --spec resources/examples/validation-room.json --output local/demo-room.stf
.\.venv\Scripts\python.exe -m src.dialux_agent stf-inspect --path local/demo-room.stf
```

Calculate, save and export an open project. Replace the paths with your own:

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-calculate --expected-project C:/Projects/demo.evo
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-save --expected-project C:/Projects/demo.evo
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-export-pdf --expected-project C:/Projects/demo.evo --path C:/Projects/report.pdf
```

Commands return JSON and support --help. Cold startup can take several minutes.
Use fresh output paths and run one desktop operation at a time. After a timeout,
inspect the project before retrying. Keep generated projects and reports in local/.

## MCP

Add this server to your AI client's MCP configuration, replacing the checkout path:

```json
{
  "mcpServers": {
    "dialux": {
      "command": "C:/path/to/DIALux-agent/.venv/Scripts/python.exe",
      "args": ["C:/path/to/DIALux-agent/src/server.py"]
    }
  }
}
```

Reconnect the client to access tools such as desktop_status, create_room and
 desktop_calculate. CLI and MCP share the same backend. The optional
[skill](resources/skills/dialux-agent/SKILL.md) gives AI clients workflow instructions.

## Repository

| Folder | Contents |
| --- | --- |
| src/ | CLI, MCP server and shared implementation |
| resources/ | Examples, regulation profiles, skill and licensed dependencies |
| docs/ | Usage guides, sources and supported limits |
| scripts/ | Maintenance and native acceptance utilities |
| tests/ | Automated tests |

Hong Kong profiles are replaceable and require project-specific applicability checks.
Report parsing primarily supports English DIALux output. See
[acceptance and limits](docs/current-acceptance.md), [desktop usage](docs/standalone-desktop.md)
and the [CAD quickstart](docs/framed-cad-quickstart.md).

Run tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

STF support reuses MCP_Dialux under its original MIT license, retained in
resources/vendor/MCP_Dialux/LICENSE. See [upstream attribution](docs/upstream-review.md).
