# Assignment-driven tool requirements

Source: BSE3125 DIALux Assignment 2627.pdf, pages 1–2. Text extracted and both pages rendered and visually reviewed locally on 2026-11-08. The 10-page main report limit, 10 MB combined PDF, independent layout plan, ceiling-grid alignment and rubric weights were confirmed. Project layout.dwg is the supplied geometry. Subsequent read-only native survey verified INSUNITS=4 metadata; physical dimensions, semantic room boundaries and design interpretation remain unadopted. See agent-development-scope.md.

- Open-plan office on a typical floor; international lighting guidance and local building energy code.
- Explicit assumptions for surface reflectances and other necessary parameters.
- Explain DIALux functions and simulation procedures, justify luminaires and lighting system, compare criteria and actual results in a table, and interpret performance.
- Proper lighting layout plan, not merely a DIALux CAD-window export; luminaire schedule and legends; align layout with ceiling grids.
- Electrical circuits and switches are not required on the drawing. The rubric still asks for explanation of lighting control.
- One combined PDF: main report at most 10 pages, simulation appendix unrestricted in page count, total size within 10 MB.
- Rubric: functions 20%, selection 20%, summary 15%, discussion 25%, layout 20%.

## Development sequence

1. Preserve and fingerprint inputs; verify DWG units and scale in AutoCAD.
2. Probe live DIALux state and stable control identifiers; detect login and modal barriers.
3. Demonstrate a single-room create/import, save, real photometry, calculation and export workflow.
4. Expose verified operations through a shared CLI/MCP backend, with JSON status and failure evidence.
5. Add source-backed rule profiles for international guidance and Hong Kong requirements; no default compliance thresholds until editions and clauses are verified.
6. Coordinate fixture IDs, locations, electrical power and schedule with the independent CAD drawing; check real simulation results and rendered report.

## Lessons retained from BSE3124

Keep originals immutable; one shared source of project facts; distinguish assumptions from measurements; verify a small real sample before batch placement; check active document before writes; never infer print quality from command success or DWG fidelity from DXF parsing; preserve user documents; keep temporary evidence outside Git.

The old course's specific regulations and cooling-load assumptions are not automatically applicable here.
