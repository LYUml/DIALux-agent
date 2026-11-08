---
name: dialux-agent
description: Use the DIALux-agent repository to preserve design inputs, prepare room geometry, check sourced lighting criteria, and verify DIALux evo workflows. Use for DIALux lighting tasks with this local tool; geometry generation alone is not lighting simulation.
---

# DIALux-agent

Locate the user's DIALux-agent checkout. This skill is distributed inside it at `skills/dialux-agent`; the repository root is two directories above this file. If installed elsewhere, locate the checkout from user workspace context rather than assuming the skill directory contains the backend.

Read the checkout's `README.md` for current commands and verified capabilities. Use its Python environment (`.venv/Scripts/python.exe` on Windows) and absolute paths when the working directory differs. CLI and MCP share a backend; select the available interface rather than reimplementing STF serialization. Do not describe unsupported commands as implemented.

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

For BSE3125, read `docs/requirements.md` before producing assignment outputs. Build and verify the tool first; preserve assignment originals and do not publish local project files or personal data merely because repository pushing is authorized.
