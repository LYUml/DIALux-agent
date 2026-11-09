# Agent development only

The user clarified on 2026-11-09 that BSE3125 assignment production is not currently authorized. The active objective is to make the agent capable enough for that future task. A separate user instruction is required to begin assignment design and deliverables. This supersedes any earlier goal description that could be read as authorizing assignment completion now.

## Capability targets

1. Native DWG survey/conversion with original preservation, entity handles and unit evidence; independent native CAD plotting/readback.
2. Geometry validation for nonrectangular rooms, offsets, boundaries and obstacles, with source/assumption traceability.
3. Explicit luminaire positioning and grid alignment rather than only DIALux's automatic room arrangement.
4. Repeatable simulation iterations, metric extraction and stop conditions, tested on synthetic fixtures.
5. A shared design-data schema linking simulated fixtures, CAD symbols, schedules and result evidence.
6. Replaceable sourced criteria, with clear applicability and no fabricated compliance claims.
7. Reproducible CLI/MCP acceptance scenarios and documented comparison with upstream MCP_Dialux capabilities.

Acceptance of these capabilities is not acceptance of an assignment design. Generic sample drawings/reports must be clearly labelled tool tests.

## Read-only CAD inspection checkpoint

The original assignment DWG was copied into ignored local survey directories and processed by AutoCAD 2027 Core Console. No original was modified. Public `drawing-convert` exported a native DXF and recorded variables/hashes; `drawing-inspect` inventoried geometry using the already installed ezdxf library. This follows the native Core Console verification pattern from BSE3124, without importing its electrical design assumptions.

Observed source metadata: INSUNITS=4 (millimetres); 2829 lightweight polylines, 889 lines, 146 arcs, 29 texts and one insert. The `Ceiling Grid` layer contains 2786 closed straight four-vertex candidates, each with 600 × 600 drawing-unit extents. The text annotation states office area 1022 m². Neither the annotation nor the grid inventory has been adopted as a verified room boundary or design area. No assignment lighting layout has been created.

Current CAD commands only support survey and inventory. A DXF export or entity count does not prove visual fidelity, a valid room polygon, or correct print output. Those gates remain tool-development work using generic test fixtures.
