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

Consult `docs/test-plan.md` and `docs/validation-luminaire.md` when testing the application. Use the available computer-use skill/tool for native interactions, respecting the user's current shared-desktop availability. Do not assume a separate mouse or an existing automation API.

For reusable session operations, read `docs/desktop-adapter.md`. The adapter injects the existing sky client; observe and inspect in one call, act in the next. Saving is live-verified; other methods must retain their documented validation status. It is not a standalone MCP desktop server.

Verify room inputs in evo, load traceable manufacturer photometry, calculate, save a native project, reopen it, and compare the exported report with application results. Record actual observations and artifact paths. Keep unperformed stages explicitly pending. Source discrepancies must be resolved for design conclusions, not silently overwritten. A catalogue UGR label is not a calculated room UGR.

For BSE3125, read `docs/requirements.md` before producing assignment outputs. Build and verify the tool first; preserve assignment originals and do not publish local project files or personal data merely because repository pushing is authorized.
