# Prototype test plan

Before implementation of adapter tests: verify valid room round-trip, reject invalid polygons and non-finite dimensions, reject missing assumptions and newline injection, and refuse existing output replacement. Test CLI subprocess JSON and real MCP discovery/call separately. File generation tests do not prove DIALux import or simulation.

Live gate pending: import a 6 x 4 x 3 m synthetic room, verify workplane and reflectances, assign real photometry, calculate, save native project, export results and compare against actual UI. Synthetic room is not assignment geometry.

Desktop interaction paused on user request: user needs their mouse. Continue background development; do not resume shared UI input without a suitable user-authorized window.
