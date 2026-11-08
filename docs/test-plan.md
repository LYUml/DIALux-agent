# Prototype test plan

Before implementation of adapter tests: verify valid room round-trip, reject invalid polygons and non-finite dimensions, reject missing assumptions and newline injection, and refuse existing output replacement. Test CLI subprocess JSON and real MCP discovery/call separately. File generation tests do not prove DIALux import or simulation.

Live gate pending: import a 6 x 4 x 3 m synthetic room, verify workplane and reflectances, assign real photometry, calculate, save native project, export results and compare against actual UI. Synthetic room is not assignment geometry.

A manufacturer ULD/IES/LDT candidate is now cached. Follow `docs/validation-luminaire.md`, including its unresolved source discrepancies, for the live gate. The asset manifest records exact bytes; a successful download does not satisfy the gate.

The user authorized shared desktop operation on 2026-11-08. The first live gate has now completed; see `live-validation-2026-11-08.md` and its hashed artifacts. Further work must distinguish this observed agent-directed run from an implemented unattended CLI/MCP driver.
