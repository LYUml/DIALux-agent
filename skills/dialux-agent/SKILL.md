---
name: dialux-agent
description: Use the DIALux-agent repository to preserve design inputs, prepare room geometry, check sourced lighting criteria, and verify DIALux evo workflows. Use for DIALux lighting tasks with this local tool; geometry generation alone is not lighting simulation.
---

# DIALux-agent

Locate the user's DIALux-agent checkout. This skill is distributed inside it at `skills/dialux-agent`; the repository root is two directories above this file. If installed elsewhere, locate the checkout from user workspace context rather than assuming the skill directory contains the backend.

Read the checkout's `README.md` for current commands and verified capabilities. Use its Python environment (`.venv/Scripts/python.exe` on Windows) and absolute paths when the working directory differs. CLI and MCP share a backend; select the available interface rather than reimplementing STF serialization. Do not describe unsupported commands as implemented.

Read the checkout's `AGENTS.md` and `docs/current-acceptance.md` before selecting a workflow. In this workspace the authorized phase is agent development with synthetic test cases; BSE3125 assignment production requires the user's separate instruction. Assignment materials can inform requirements without authorizing a design or submission.

## Prepare inputs and geometry

- Inventory original PDF/DWG files and preserve their hashes. A DWG header identifies format only; it does not prove dimensions, units or room boundaries.
- Room creation needs explicit metre coordinates, height, workplane, reflectances in percent, maintenance factor and nonempty source/assumption descriptions. Read `examples/validation-room.json` for the schema. It is synthetic test geometry, never an assignment-derived plan.
- Generate new versioned STF outputs. Read them back to check the serialized room before import. Do not equate this round trip with successful evo import; the upstream STF route does not transfer real luminaire photometry reliably.

## Regional criteria

Keep criteria in replaceable profiles. For Hong Kong, read `docs/hk-source-register.md` and the applicable source entries in `profiles/hk-sources.json`. Cached PDF hashes are in `profiles/hk-sources.snapshot.json`; full files are local, not distributed with the skill.

Before adopting a criterion, verify its official document edition, clause/table, page, amendments, project scope and exceptions. Keep advisory recommendations, government-contract specifications, normal lighting, energy and emergency-lighting requirements distinct. A source being downloaded does not make its rules active. The Hong Kong template is intentionally unverified.

Measurements must identify units, calculation surface and evidence. `criteria-check` exit code 3 means unverified; code 1 means failed; neither is passing. A profile status flag is only a caller assertion. Do not claim full compliance from a subset of numerical checks.

## Real DIALux work

Use the independent `desktop-*` CLI commands or their underscore-named MCP equivalents. Read `docs/standalone-desktop.md` for verified capabilities and current failures, and `docs/validation-luminaire.md` for the manufacturer's asset discrepancies. The older sky/Computer Use adapter is historical research; do not substitute it for standalone CLI/MCP acceptance.

Start with `desktop-status`. Match the exact expected native project before mutation. Import STF into an empty workspace, then Save As to a new `.evo` path. Import local photometry with an expected product ID; this loads an active luminaire but does not place it. `desktop-arrange-space` is scoped to the current space of a single-room fixture and refuses calculation-ready content to reduce duplicate insertion. Save placement before calculation. Operations may take shared foreground focus, so respect the user's current desktop availability.

A successful command submission is not proof of completion. After a timeout, unexpected dialog or process exit, inspect state and preserve evidence before retrying. DIALux 14.1 has a documented native crash under the inherited temporary path. New processes started by desktop-launch use a process-local ASCII temporary directory; this recovered a fresh six-luminaire calculation. Reusing an existing process cannot apply that environment change. Read the current evidence before claiming stability, and never substitute cached results or synthetic numbers. `desktop-export-pdf` exports the current documentation selection to a new PDF using stored results. `report-read` preserves document page numbers and hashes, supports exactly one adjacent English two-page room Summary inside a larger report, and rejects multiple summaries.

Verify room inputs in evo, load traceable manufacturer photometry, calculate, save a native project, reopen it, and compare the exported report with application results. Record actual observations and artifact paths. Keep unperformed stages explicitly pending. Source discrepancies must be resolved for design conclusions, not silently overwritten. A catalogue UGR label is not a calculated room UGR.

## Choose the evidence workflow

- For rigid same-count arrays, use `layout-array-transform-plan` before `layout-apply-array`; read `docs/guarded-array-execution.md`. Success is unsaved geometry, not completed calculation or persistence. `array-execution-verify` independently replays completed evidence. Read `docs/array-runtime-identity-investigation.md` before relying on large-array acceptance: native UI IDs changed during cache clearing/motion when references were released. The retained-reference fix is under full native validation; do not waive identity checks or relabel the old rejected run as successful.
- For explicit fixture grids, use `layout-apply-grid` and read `docs/grid-application.md`. Its persistent worker collects the full group, journals movements and reads back the group; a pending step can contain a real partial write. Preserve and inspect that project before recovery. Runtime IDs are session-local and can change; never reuse them blindly after reopening or rebuilding UI inventory.
- For multiple supplied grids, use `layout-candidates-run` / MCP `run_layout_candidates` and read `docs/layout-candidates.md`. The runner allows only fixed-product, same-count, zero-rotation grid changes. Keep objective ranking separate from pass/fail criteria. A completed stopping policy does not mean a feasible design was found, and the winning copy is not automatically activated.
- For multiroom reports, use `report-read-all` and explicit summary identities rather than the single-summary reader. Use `report-workplane-read` for directly reported extrema; do not infer a minimum from rounded average and uniformity. Read `docs/scoped-report-reading.md` and `docs/workplane-extrema.md` for supported scopes.
- Use `report-model-parameters` with an exact summary ID to read reported reflectances, fixed maintenance factor and heights. Read `docs/reported-model-parameters.md`; the room summary does not prove individual surface materials or current native settings.
- For observed CAD output, read `docs/observed-layout-cad.md` and `docs/cad-dimensions.md`. Explicit dimension endpoints and product envelopes remain assumptions unless independently evidenced. Native reopen checks and fixed-scale PDF vector checks are separate from visual sheet acceptance.
- For report-linked product tables, use `drawing-export-scheduled` / MCP `export_scheduled_layout_dxf`; read `docs/luminaire-schedule.md`. It rereads one product section and links positions under an explicit transform. It does not authenticate photometry or turn reported fixture power into a verified regulatory load.
- For multiple products, use explicit report sections/groups with `report-arrangements-read`, `schedule-build-mixed` and `drawing-export-mixed`; read `docs/mixed-product-cad.md`. Global report fixture IDs can span product sections. Keep supplied symbol envelopes distinct from authenticated manufacturer dimensions.
- For assembling existing static report pages, use `pdf-bundle-build` and then `pdf-bundle-verify`; read `docs/pdf-bundles.md`. Pin source hashes, explicitly select main/appendix pages and supply page/byte limits. The verifier checks source/output page evidence; it does not author engineering conclusions or verify interactive PDF features. Forms and signed documents are unsupported.

Do not run competing desktop workflows. Poll a live process through its handle; a stale journal alone is not evidence it is alive or stopped. A worker's code does not hot-update when repository files change. After failure, use fresh native state and preserved artifacts to decide the next step; do not repeat a mutation merely because the command returned an error.

For BSE3125, read `docs/requirements.md` before producing assignment outputs. Build and verify the tool first; preserve assignment originals and do not publish local project files or personal data merely because repository pushing is authorized.
