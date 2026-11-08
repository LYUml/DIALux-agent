# DIALux-agent

Experimental Windows tooling for DIALux evo, driven by the BSE3125 lighting-design workflow. Development precedes assignment production.

## Current capabilities

`python src/dialux_agent.py inventory --source <assignment-folder>` hashes PDF/DWG inputs without modifying them and reports the DWG header. `verify --manifest <json>` checks that originals remain unchanged. `room-create` generates a single-room STF through the vendored backend, and `stf-inspect` reads it back. `criteria-check` evaluates supplied sourced criteria against evidence-bearing measurements. All commands emit JSON.

The real evo 14.1 workflow has been verified through agent-directed computer use: STF import, manufacturer ULD import, single-luminaire placement, calculation, native save/reopen and PDF export, followed by a second edit/recalculate/export/reopen cycle. The CLI/MCP does not yet automate those desktop operations. The [desktop session adapter](docs/desktop-adapter.md) supports inspected actions through the existing Computer Use client. See [live evidence](docs/live-validation-2026-11-08.md). This is not a completed CLI-Anything harness.

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

Tools: `inventory`, `verify`, `create_room`, `inspect_stf`, `evaluate_profile`, `read_summary_pdf`, `check_report`. The MCP test exercises initialization, discovery, geometry creation and readback through real subprocess transport, plus report assessment when the local exported PDF is present. Paths are caller-specified: this is a trusted local prototype, not a remotely exposed service.

`report-read --path <summary.pdf>` extracts average perpendicular illuminance, uniformity and LPD from the tested English two-page single-room Summary. It retains the room/scene header, surface identifier, page and PDF SHA-256 for traceability. Its `measurements` array can be passed to the criteria evaluator after checking scope. Unsupported/ambiguous text layouts are rejected; scanned PDFs and complete multi-room reports are not supported yet. Reading values does not establish compliance or authenticate a report. The local real evo export is tested when present; that test is skipped on fresh checkouts without the private artifact.

`report-check` combines extraction and criteria evaluation without copying values between files:

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent report-check --path local/validation-summary-v2.pdf --profile profiles/hk-bec2024-office-lpd.json
```

This example returns exit code **3 / unverified**, because no project applicability facts have been supplied. Add `--context <facts.json>` only after reviewing the [HK module scope](docs/hk-office-lpd.md). The output retains both the report evidence and criterion-by-criterion assessment. The PDF bytes hashed are exactly the bytes parsed. The MCP equivalent is `check_report(path, profile, context)`; `profile` and `context` are JSON objects. Region-specific rules remain outside this workflow module. No calculation is launched, report targets are not adopted, and a profile pass is not whole-project certification.

## Evidence and remaining work

| Capability | Current evidence |
|---|---|
| PDF/DWG integrity | SHA-256 inventory and tamper test; no DWG geometry interpretation |
| Single-room STF exchange | Reused serializer, parameter validation and round-trip tests |
| CLI / MCP | Real process tests; common backend |
| Hong Kong sources | Eight official PDFs cached locally with hashes, editions and review register |
| Hong Kong rules | Source-reviewed BEC 2024 office LPD module with evidenced applicability; other criteria pending, no whole-project certification |
| DIALux import, real luminaires, calculation, save/reopen, report export | Synthetic-room initial run and edited second cycle verified through computer use; unattended driver pending |
| BSE3125 assignment | Requirements extracted, originals preserved; design not produced |

See [requirements](docs/requirements.md), [test plan](docs/test-plan.md), [module boundaries](docs/modules.md), and [Hong Kong source review](docs/hk-source-register.md). Refresh local official PDF caches with `python scripts/cache_hk_sources.py`; caching does not activate rules.

Commit convention: `YYYY-MM-DD English change description`, matching polyu_bse3124. Do not publish assignment originals, credentials, logs containing personal data, or generated local projects.
