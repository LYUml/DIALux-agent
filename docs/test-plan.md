# Prototype test plan

Before implementation of adapter tests: verify valid room round-trip, reject invalid polygons and non-finite dimensions, reject missing assumptions and newline injection, and refuse existing output replacement. Test CLI subprocess JSON and real MCP discovery/call separately. File generation tests do not prove DIALux import or simulation.

Live gate: import a 6 x 4 x 3 m synthetic room, verify workplane and reflectances, assign real photometry, calculate, save native project, export results and compare against actual UI. Completed evidence is recorded below. Synthetic room is not assignment geometry.

A manufacturer ULD/IES/LDT candidate is now cached. Follow `docs/validation-luminaire.md`, including its unresolved source discrepancies, for the live gate. The asset manifest records exact bytes; a successful download does not satisfy the gate.

The user authorized shared desktop operation on 2026-11-08. The first live gate has now completed; see `live-validation-2026-11-08.md` and its hashed artifacts. Further work must distinguish this observed agent-directed run from an implemented unattended CLI/MCP driver.

The second edit/recalculate/export/reopen gate also completed. The desktop module's screenshot-guided save and calculation paths were exercised separately in the live app; see `desktop-adapter.md`. The calculation gate observed an obsolete-results banner before input and new values with the banner removed afterward. Accessibility-index calculation remains unverified. Eight Node tests cover observation consumption, foreign controls, message boxes, window identity and visual-point validation; fake-client tests alone are not live evidence.


## Independent backend acceptance, 2026-11-09

The v9 gate now replays public CLI commands from a new DIALux process through room/ULD import, automatic placement, fresh calculation, native saving, PDF export, switching projects, reopening and exporting again. A real stdio MCP session verified desktop tool discovery, live project status and report extraction. See `acceptance-2026-11-09.md`; historical Computer Use gates above are not the acceptance evidence for independence.
