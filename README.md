# DIALux-agent

Independent Windows CLI/MCP tools for DIALux evo and native AutoCAD verification.
The shared Python backend runs desktop operations through pywinauto; Codex
Computer Use is not required.

**Current scope: develop and verify the agent first.** BSE3125 materials inform
requirements only. Assignment design and submission production require a separate
user instruction. All development layouts are synthetic tests.

Start with the [current acceptance matrix](docs/current-acceptance.md),
[scope](docs/agent-development-scope.md) and
[workflow skill](skills/dialux-agent/SKILL.md). Passing unit tests or exporting a
file does not establish complete native engineering acceptance.

## Verified capability and remaining limits

| Area | Native evidence and present boundary |
| --- | --- |
| Independent desktop control | STF/ULD import, arrangement, actual calculation, save, PDF export and reopen through standalone workers. Requires an interactive Windows session; no private mouse. |
| Geometry | Concave and adjacent synthetic rooms, ground-supported box obstacles, source-preserving DWG survey and explicitly selected DXF boundary extraction. General CAD room inference and arbitrary object topology are not established. |
| Fixture control | Six-fixture explicit grid movement and 168-fixture regular-array translation passed full position checks, calculation and persistence. A six-fixture 5° native rotation also passed those gates. Arbitrary large individual movement and general recovery remain unaccepted. |
| Iteration | Two explicit candidates passed actual calculations, comparison and reopen checks. A generated four-candidate domain also passed calculation, comparison and reopen checks; previous failures are retained. No global-optimum or automatic winner-installation claim. |
| Drawing | Observed fixture coordinates, editable IDs, bounded label placement, linear dimensions, single-product schedule and fixed-paper frame/titleblock. Native DWG reopen and physical PDF scale checked on A3, A2 and 168-symbol A1 synthetic sheets. Mixed-product tables and general sheet composition remain unfinished. |
| Results | Exact supported English room/scene summaries, direct working-plane minimum/maximum and explicitly scoped coordinate tables. Missing/ambiguous evidence is rejected; whole-project completeness is not inferred. |
| Regulation | Replaceable source-bearing Hong Kong BEC office LPD, selected-zone automatic-control numerical checks and separately adopted Labour advisory modules. Project applicability remains explicit; these do not constitute comprehensive legal compliance. |

Detailed acceptance and retained failures are linked from the matrix. See the
[generated four-candidate acceptance](docs/generated-search-acceptance.md). The latest
notification-transition investigation is in
[desktop notification transitions](docs/desktop-notification-transitions.md).

## Setup

Tested with Python 3.12, DIALux evo 14.1 and AutoCAD 2027 on Windows. Native CAD
commands use the installed AutoCAD Core Console. From this checkout in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m src.dialux_agent --help
```

Commands emit JSON and expose per-command `--help`. Use new output paths: creation
operations preserve existing artifacts. Local source copies, native projects,
reports and logs belong in ignored `local/`, not Git.

A small offline geometry example:

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent room-create --spec examples/validation-room.json --output local/demo-room.stf
.\.venv\Scripts\python.exe -m src.dialux_agent stf-inspect --path local/demo-room.stf
.\.venv\Scripts\python.exe -m src.dialux_agent layout-plan --spec examples/synthetic-grid-layout.json
```

STF round-trip and layout planning do not run DIALux. For a reproducible synthetic
CAD export, native DWG verification and fixed-scale PDF workflow, use the
[framed CAD quickstart](docs/framed-cad-quickstart.md).

## Workflow entry points

| Task | CLI entry points | Contract and evidence |
| --- | --- | --- |
| Preserve and inspect inputs | `inventory`, `verify`, `drawing-convert`, `drawing-inspect`, `drawing-extract-boundary` | [Boundary extraction](docs/cad-boundary-extraction.md) |
| Create geometry | `room-create`, `rooms-create`, `stf-inspect`, `desktop-import-stf` | [Multiroom](docs/multiroom-import.md), [obstacles](docs/obstacle-exchange.md) |
| Discover native state | `desktop-status`, `desktop-project-tree`, `desktop-read-arrangement`, `group-inspection-checkpoint`, `group-inspection-verify` | [Group inspection](docs/group-inspection-checkpoints.md) |
| Place and verify fixtures | `desktop-import-luminaire`, `desktop-arrange-room`, `desktop-edit-arrangement`, `desktop-edit-fixture`, `layout-apply-grid`, `layout-verify-observed` | [Room creation](docs/journalled-room-creation.md), [grid application](docs/grid-application.md), [large array](docs/large-array-translation.md) |
| Calculate and compare | `calculation-checkpoint`, `layout-candidates-generate`, `layout-candidates-run`, `layout-offset-search` | [Calculation checkpoints](docs/calculation-checkpoints.md), [candidate runs](docs/layout-candidates.md) |
| Read and evaluate results | `report-read-all`, `report-workplane-read`, `report-layout-read`, `report-arrangements-read`, `report-check`, `criteria-check` | [Scoped summaries](docs/scoped-report-reading.md), [mixed products](docs/mixed-product-report-reading.md), [workplane extrema](docs/workplane-extrema.md), [applicability](docs/profile-applicability.md) |
| Produce independent CAD | `drawing-export-observed`, `schedule-build`, `drawing-export-scheduled`, `layout-verify-native`, `layout-plot-native` | [Observed layouts](docs/observed-layout-cad.md), [schedule](docs/luminaire-schedule.md), [sheets](docs/cad-sheets.md) |

`report-read` is the single-summary adapter; use `report-read-all` for multiple
supported summaries. `report-check --summary-id ...` selects exactly one summary.
Report export uses stored results unless a fresh calculation was explicitly run.

Native reads/edits qualify coordinates as `active_storey`. Runtime IDs are
session-local and must be rediscovered after reopening. Operation journals retain
pending actions and partial failures. A timeout does not prove that no write
occurred; inspect fresh state before deciding what to do next. There is no generic
automatic resume or rollback.

The offline [rigid-array preflight](docs/array-transform-preflight.md) checks whether
a complete observed array can reach a target grid by one translation/rotation.
It does not execute that movement. The separate
[native 5° rotation test](docs/native-array-rotation.md) has scoped readback,
calculation and reopen evidence.

## MCP and AI skill

The stdio MCP server exposes the same backend functions as the CLI. Configure an
MCP client with absolute paths, adjusting these for another checkout:

```json
{
  "mcpServers": {
    "dialux-agent": {
      "command": "C:/Users/lyuml-win/Desktop/DIALux-agent/.venv/Scripts/python.exe",
      "args": ["C:/Users/lyuml-win/Desktop/DIALux-agent/src/server.py"]
    }
  }
}
```

[skills/dialux-agent/SKILL.md](skills/dialux-agent/SKILL.md) describes workflow,
evidence and failure handling. It is repository-local, not globally installed.
The tools are a trusted local prototype, not a remotely exposed service.

Desktop workers use a session-local mutex to reject overlapping cooperating
operations. They can change foreground focus and do not exclude human input.
Do not run another desktop workflow concurrently with a candidate search.
See the [standalone desktop guide](docs/standalone-desktop.md).

The launcher applies a process-local ASCII TEMP/TMP workaround for the reproduced
ZeroMQ failure on this machine. It changes no installed DLL or global environment;
an already-running DIALux process retains its existing environment.

## Sources, reuse and development

The pinned MIT [MCP_Dialux backend](docs/upstream-review.md) is retained under
`vendor/MCP_Dialux` with its license. Room/obstacle serialization and shared-wall
splitting reuse that work. CLI-Anything informs the CLI/JSON/shared-backend design.
The [acceptance matrix](docs/current-acceptance.md) compares reviewed upstream
modules without claiming to outperform every upstream feature or release.

Regulation profiles remain separate from geometry and desktop control. Consult the
[Hong Kong source register](docs/hk-source-register.md),
[BEC office LPD scope](docs/hk-office-lpd.md) and
[Labour desk-lighting advisory](docs/hk-desk-lighting.md).
The separate [office automatic-control numerical module](docs/hk-automatic-control.md)
requires control-zone evidence; illumination results cannot establish control operation.
An empty or inapplicable evidence set does not pass. A supplied `verified` profile
label is not independent verification of its authority or project applicability.
Refresh cached official PDFs with `python scripts/cache_hk_sources.py`; downloading
sources does not activate criteria.

See [requirements](docs/requirements.md), [module boundaries](docs/modules.md)
and [test plan](docs/test-plan.md). Commit convention:
`YYYY-MM-DD English change description`. Preserve assignment originals; never
publish private source files, generated local evidence or credentials.
