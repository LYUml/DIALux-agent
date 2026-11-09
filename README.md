# DIALux-agent

Experimental Windows tooling for DIALux evo, driven by the BSE3125 lighting-design workflow. Development precedes assignment production.

## Current capabilities

`python src/dialux_agent.py inventory --source <assignment-folder>` hashes PDF/DWG inputs without modifying them and reports the DWG header. `verify --manifest <json>` checks that originals remain unchanged. `room-create` generates a single-room STF through the vendored backend, and `stf-inspect` reads it back. `criteria-check` evaluates supplied sourced criteria against evidence-bearing measurements. All commands emit JSON.

The independent Windows CLI/MCP prototype has passed a fresh-process single-room workflow: STF import, manufacturer ULD import, automatic placement, real calculation, native save, PDF export, reopen and result comparison. It uses pywinauto and does not depend on Codex Computer Use. The v9 fixture produced 531 lx, Uo 0.56 and 6.50 W/m²; this is tool validation, not a compliant assignment design. See [acceptance evidence and limitations](docs/acceptance-2026-11-09.md). A process-local TEMP/TMP workaround resolves the reproduced ZeroMQ crash on this machine; no installed DLL or global environment was changed. The older [Computer Use adapter](docs/desktop-adapter.md) is historical research.

The MIT-licensed MCP_Dialux geometry backend is incorporated under `vendor/MCP_Dialux`, with its license. CLI-Anything informs the CLI/JSON/shared-backend approach. See [upstream review](docs/upstream-review.md) for pinned revisions and license decisions. Research checkouts remain local-only under `upstream/`.

## Setup and commands

Python 3.12 is the tested runtime. From this repository in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe src/dialux_agent.py room-create --spec examples/validation-room.json --output local/demo-room.stf
.\.venv\Scripts\python.exe src/dialux_agent.py stf-inspect --path local/demo-room.stf
.\.venv\Scripts\python.exe src/dialux_agent.py criteria-check --profile profiles/hk-office.template.json --measurements local/measurements.json
```

`room-create` refuses to overwrite existing output: choose a new version name. The example is a synthetic 6 x 4 m room, not assignment geometry. STF round-trip tests prove serialization, not successful evo import. Latin-1 room names are required by the upstream format. Invoking the script by absolute path works from another working directory.

Create `local/measurements.json` as an array containing `metric`, `unit`, `calculation_surface`, numeric `value`, and `evidence` on each item. The Hong Kong template has no adopted criteria and returns `unverified`, including with an empty measurement array `[]`. A profile's `verified` label is a caller assertion, not independent verification of the document or project applicability.

Exit codes: `0` successful operation / supplied criteria pass; `1` source mismatch or criteria fail; `2` invalid input or I/O error; `3` criteria unverified. Missing evidence is never passing. The engine does not certify the entire project.

Profiles can include evidence-bearing applicability conditions; pass `--context <facts.json>` to the CLI or `context` to the MCP evaluator. See [applicability schema](docs/profile-applicability.md). Missing context remains unverified, and an empty applicable scope does not pass.

Available Hong Kong modules are [BEC 2024 office LPD](docs/hk-office-lpd.md) and the separately adopted [Labour Department desk-lighting recommendation](docs/hk-desk-lighting.md). They retain different authority and measurement semantics. The latter requires a directly evidenced task minimum that the current Summary reader does not extract.

## MCP configuration

Independent desktop CLI commands are `desktop-launch`, `desktop-status`, `desktop-import-stf`, `desktop-import-luminaire`, `desktop-arrange-space`, `desktop-save-as`, `desktop-save`, `desktop-open`, `desktop-calculate`, and `desktop-export-pdf`. MCP exposes the same names with underscores. Use `--help` for each command and [the standalone guide](docs/standalone-desktop.md) for preconditions and evidence. These operations can take foreground keyboard focus; they do not provide a private desktop or separate mouse. A worker timeout or unexpected dialog means the outcome is unverified: inspect before retrying. Export uses stored results and does not prove a fresh calculation.

The repository also includes an AI workflow skill at [skills/dialux-agent/SKILL.md](skills/dialux-agent/SKILL.md). It describes the actual commands, provenance checks and live verification boundary. It is not globally installed and does not add desktop control by itself. PyYAML in the locked environment supports the skill validator.

Configure a stdio MCP client with these absolute paths (adjust the checkout location on other machines):

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

Non-desktop tools: `inventory`, `verify`, `create_room`, `inspect_stf`, `evaluate_profile`, `read_summary_pdf`, `check_report`. The MCP test exercises initialization, discovery, geometry creation and readback through real subprocess transport, plus report assessment when the local exported PDF is present. Paths are caller-specified: this is a trusted local prototype, not a remotely exposed service.

`report-read --path <summary.pdf>` extracts average perpendicular illuminance, uniformity and LPD from the tested English two-page single-room Summary, either standalone or embedded in a complete report containing exactly one Summary. It retains the room/scene header, surface identifier, page and PDF SHA-256 for traceability. Its `measurements` array can be passed to the criteria evaluator after checking scope. Unsupported/ambiguous text layouts are rejected; scanned PDFs and reports containing multiple room/scene summaries are rejected. Original document page numbers are retained. Reading values does not establish compliance or authenticate a report. The local real evo export is tested when present; that test is skipped on fresh checkouts without the private artifact.

`report-check` combines extraction and criteria evaluation without copying values between files:

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent report-check --path local/validation-summary-v2.pdf --profile profiles/hk-bec2024-office-lpd.json
```

This example returns exit code **3 / unverified**, because no project applicability facts have been supplied. Add `--context <facts.json>` only after reviewing the [HK module scope](docs/hk-office-lpd.md). The output retains both the report evidence and criterion-by-criterion assessment. The PDF bytes hashed are exactly the bytes parsed. The MCP equivalent is `check_report(path, profile, context)`; `profile` and `context` are JSON objects. Region-specific rules remain outside this workflow module. No calculation is launched, report targets are not adopted, and a profile pass is not whole-project certification.

## Evidence and remaining work

| Capability | Current evidence |
|---|---|
| CAD inputs | Native DWG conversion, hash-bound explicit DXF boundary extraction and coordinate transforms; no automatic semantic room inference |
| STF exchange | Reused upstream serializer; adjacent multiroom and concave native import/report tests |
| CLI / MCP | Real process tests; common backend |
| Hong Kong sources | Eight official PDFs cached locally with hashes, editions and review register |
| Hong Kong rules | Source-reviewed BEC 2024 office LPD module with evidenced applicability; other criteria pending, no whole-project certification |
| Independent DIALux desktop operations | Fresh-process v9 public CLI workflow passed, including placement, save/open and export; real MCP status/report calls verified |
| Fresh calculation | Process-local TEMP/TMP workaround; v8 recovery and independent v9 replay both produced 531 lx / Uo 0.56 |
| BSE3125 assignment | Requirements extracted, originals preserved; design not produced |

See [requirements](docs/requirements.md), [test plan](docs/test-plan.md), [module boundaries](docs/modules.md), and [Hong Kong source review](docs/hk-source-register.md). Refresh local official PDF caches with `python scripts/cache_hk_sources.py`; caching does not activate rules.

Commit convention: `YYYY-MM-DD English change description`, matching polyu_bse3124. Do not publish assignment originals, credentials, logs containing personal data, or generated local projects.

## Initial independent acceptance checkpoint

2026-11-09: 102 Python tests and 8 historical adapter tests passed; 21 local artifact/source hashes matched; both assignment originals were unchanged; the distributed skill passed validation. The final native fixture is `local/acceptance-project-v9.evo`, with report `local/acceptance-v9.pdf` and reopened comparison `local/acceptance-v9-reopened.pdf`. Read the acceptance document before applying the prototype to other projects or DIALux versions.

## Agent-only capability expansion

The current development phase is agent-only; assignment production requires a separate user instruction. See [scope](docs/agent-development-scope.md). `drawing-convert --path <source.dwg> --output-directory <new-directory>` uses installed AutoCAD Core Console on a copied input and verifies the original hash. `drawing-inspect --path <export.dxf>` inventories units, entities, text and candidate grid polygons without inferring room boundaries.

`desktop-edit-arrangement --expected-project <test.evo> --tree-item-id <exact-expanded-item-id> --values <parameters.json>` / MCP `desktop_edit_arrangement` edits native arrangement fields and reads them back. It clears cached results before editing and does not save automatically. Partial edits are possible on failure. Count changes have passed native edit/save/recalculate verification; full positioning remains under development. See [evidence and limitations](docs/arrangement-edit-verification.md).

`desktop-project-tree` discovers realized native tree items and optionally expands an exact node. `desktop-group-fixtures` reads individual native XYZ positions and rotations from a specified group. Repeated automation IDs are retained and distinguished by session-local runtime IDs; neither command claims a complete project inventory. See [native inspection evidence](docs/tree-and-fixture-inspection.md).

`desktop-edit-fixture --expected-project <project.evo> --parameters <request.json>` / MCP `desktop_edit_fixture` moves one inspected fixture with runtime-identity and prior-position guards. It clears cached results, does not save automatically and requires inspection after partial failure. Native tests confirmed one moved fixture, three unchanged neighbours and fresh recalculation; see [evidence and boundaries](docs/individual-fixture-verification.md).

`layout-verify-observed --layout <planned.json> --observed <native-readback.json>` / MCP `verify_observed_layout` checks one-to-one geometric agreement between planned fixtures and supplied native observations, with fixed display-rounding tolerances. It rejects ambiguous matches and makes no whole-project or photometry claim. A translated synthetic layout passed native DIALux readback, fresh calculation and native CAD record verification using the shared plan; see [evidence](docs/translated-layout-verification.md).

`layout-apply-grid` / MCP `apply_grid_layout` applies a validated zero-rotation grid to an existing equal-count native fixture group and verifies fresh coordinate readback. It journals every attempted movement, stops on failure and leaves save/calculation explicit. See [workflow and current limits](docs/grid-application.md).

`layout-plan --spec examples/synthetic-grid-layout.json` / MCP `plan_grid(spec)` generates explicit fixture positions and footprints on a rotated, anchored grid inside a supplied polygon, excluding keep-out regions. It reuses Shapely geometry operations. The example is a synthetic L-shaped tool test, not an assignment design. Output provides fixture IDs, grid indices, source-spec hash and rejection counts; it performs no lighting simulation.

`layout-export-dxf --spec examples/synthetic-grid-layout.json --output <new.dxf>` / MCP `export_layout_dxf(spec, output, layout=None)` exports the same fixtures as editable blocks with ID attributes, metre units, boundary/keep-out layers and explicit synthetic-test labels. Optional `--layout <plan.json>` must match the specification. The exporter refuses existing files and verifies fixture identities, XY positions and rotations by reopening the DXF. This is a 2D plan; mounting height is documented separately. Applying these positions to DIALux, opening in native AutoCAD and validating printed output remain separate development gates.

`layout-verify-native --path <synthetic.dxf> --output-directory <new-directory>` / MCP `verify_layout_native` saves a copy as DWG using installed AutoCAD, reopens the saved DWG in a separate process, and compares fixture IDs, XYZ insertion coordinates, rotations, scales and block names. It preserves the source and fails closed on native timeouts. Block-shape fidelity and plotting are not covered by this gate.

`layout-plot-native --path <test.dwg> --output-directory <new-directory> --fixture-ids L0001 L0002 ...` / MCP `plot_layout_native` produces a native A3 fit-to-page test PDF, verifies expected labels and renders a preview. It preserves the source; visual review remains separate. The synthetic acceptance output passed independent Poppler inspection. See [plot evidence and limitations](docs/native-plot-verification.md).

`report-read-all` / MCP `read_report_pdf` keeps recognized room/light-scene summaries separate with original page and PDF hash evidence. `report-check --summary-id ...` / MCP `check_report_summary` checks only the explicitly selected summary. Duplicate or incomplete pairs fail; complete project coverage is not inferred. See [scope and validation](docs/scoped-report-reading.md).

`rooms-create` / MCP `create_rooms` reuses the upstream multiroom STF serializer with name, geometry and overlap validation. `desktop-close-project` preserves unsaved work unless saving is requested; `desktop-read-space` reads native room parameters. Three adjacent synthetic rooms passed import, native tree/property checks and visual topology review. See [multiroom evidence](docs/multiroom-import.md).

Coordinates are now explicitly qualified as `active_storey`: native position fields change with view context, so fixture reads/edits normalize to storey context. Regenerate older unqualified readbacks before applying/comparing layouts. `desktop-room-context` lists or invokes exact room labels but does not claim selected-state verification; actual fixture positions must confirm scope. See [coordinate-frame evidence](docs/coordinate-frame-verification.md).

`desktop-arrange-room --expected-project <project.evo> --spec <request.json>` / MCP `desktop_arrange_room` adds one named arrangement with an expected realized-group inventory and durable journal. It identifies the newly created group by runtime ID, including when DIALux assigns duplicate default names. The return is explicitly `created_unverified`; inspect room containment and previous fixture geometry before accepting it. Failed or timed-out creation must not be retried automatically. See [the journalled room-creation contract](docs/journalled-room-creation.md).

`room-addition-verify` / MCP `verify_room_addition` checks new fixture envelopes against an explicit room/exclusion specification and compares supplied previous groups before/after creation. It rejects incomplete pagination, overlap, out-of-room footprints and unexpected previous geometry changes. See the [evidence contract and limitations](docs/journalled-room-creation.md#automated-evidence-checking).

`calculation-checkpoint` / MCP `calculation_checkpoint` runs calculation, native report export, exact room/scene criteria checks and native save with a durable stage journal. It returns explicit conditions-met, conditions-not-met or evidence-incomplete decisions; this is one iteration checkpoint, not an automatic layout optimizer. See [workflow preconditions, exit codes and evidence](docs/calculation-checkpoints.md).

`drawing-extract-boundary` / MCP `drawing_extract_boundary` extracts an explicitly selected closed straight DXF modelspace polyline, bound to the expected source hash and an explicit unit/coordinate transformation. It supports concave outlines but does not infer semantic room boundaries. See [input contract and validation](docs/cad-boundary-extraction.md).

The [concave native validation](docs/concave-room-validation.md) exercises offset millimetre CAD extraction, six-vertex STF exchange, native import, five actual fixtures in a nominal 3×2 arrangement, footprint checks, calculation and a plotted 20 m² reentrant room. It is synthetic tool evidence, not assignment work.

`drawing-export-observed` / MCP `export_observed_layout_dxf` exports actual supplied native fixture positions into editable CAD blocks, with explicit drawing-ID mapping and observation hashes. It reuses the native CAD reopen/plot gates; see [the five-fixture concave validation and limitations](docs/observed-layout-cad.md).

Native plotting optionally supports an explicit A3 fixed scale, verified against the exported PDF vector outline rather than its label alone. See [fixed-scale usage, Autodesk references and native 1:50 evidence](docs/fixed-scale-plots.md).

The [large-project checkpoint](docs/large-project-validation.md) exercises a synthetic 1020 m² / 168-luminaire native calculation. Fixture inspection now uses UIA ItemContainer/VirtualizedItem patterns instead of assuming that visible WPF rows are the complete group. A complete persistent-worker scan subsequently collected all 168 fixtures in 42 hashed pages; public offline verification matched every position/rotation to the synthetic grid, and UI XYZ matched the independently parsed native PDF table. This remains one group, not whole-project acceptance.

`group-inspection-checkpoint` / MCP `inspect_group_checkpoint` collects one explicitly counted native fixture group in a single worker, with hashed page evidence and a durable failure journal. See [operation and limits](docs/group-inspection-checkpoints.md).

`report-layout-read` / MCP `read_report_layout` reads an explicitly selected complete native PDF coordinate table, including product metadata and page evidence. It preserves unknown coordinate-frame and rotation status; see [parser boundaries and native 168-fixture regression](docs/report-layout-reading.md).

`room-create` / `rooms-create` can include validated ground-supported obstacle boxes using the licensed upstream STF implementation. See [supported geometry, fixed material assumption and pending native gate](docs/obstacle-exchange.md).

Native plotting accepts an explicit ISO landscape paper (`--paper A3|A2|A1|A0`) and drawing specifications can set fixture/note text heights. The [168-symbol A1 1:100 native test](docs/large-native-plots.md) records actual DWG reopen, PDF vector-scale checks and visual inspection, separately from DIALux observation evidence.

`desktop-read-furniture` / MCP `desktop_read_furniture` reads native object reference positions, rotations and sizes with exact identity checks. The [synthetic column/desk gate](docs/obstacle-exchange.md) includes actual import, calculation, report inspection and persisted readback after native reopen.

`report-workplane-read` / MCP `read_workplane_pdf` extracts direct minimum/maximum illuminance from an explicitly selected native working-plane table, with room/scene/surface identity and PDF evidence. See [scope, native regression and applicability limits](docs/workplane-extrema.md).

`schedule-build` / MCP `build_luminaire_schedule` links observed CAD fixture IDs to native PDF product records using unique coordinate correspondence and an explicit transform. See [schedule evidence, native regression and limits](docs/luminaire-schedule.md).

`drawing-export-scheduled --request <request.json>` / MCP `export_scheduled_layout_dxf` rereads that evidence and exports an observed drawing with a single-product aggregate table. Native reopening checks table text/geometry as well as fixture records. Layout exports also support explicit [linear dimensions and bounded label placement](docs/cad-dimensions.md); these are tested synthetic drawing features, not complete engineering-sheet acceptance.

`layout-candidates-run --request <request.json>` / MCP `run_layout_candidates` runs supplied same-count grid candidates on separate native copies with actual calculation checkpoints, scoped objective comparison and explicit stopping policies. See [request fields and limitations](docs/layout-candidates.md). Multi-iteration native acceptance is still pending; the interface does not generate an optimal design or install a winner automatically.

The [current acceptance matrix and remaining gates](docs/current-acceptance.md) separates observed native capabilities from pending work and compares the reviewed pinned upstream modules without claiming complete agent acceptance.
