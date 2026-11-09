# Native six-fixture array rotation

2026-11-09. Synthetic obstacle-room test using the standalone Python CLI/MCP
backend and independent Windows workers, without Codex Computer Use.

The test opened the unchanged `local/obstacles-native-v1.evo` and saved a separate
`local/native-rotation-v1/rotation.evo`. It read native counts 3 × 2, centre
(3, 2, 3.035) m and angle 0°. A complete six-fixture inspection matched the
baseline plan. The array fields were read again and supplied to the
[rigid-transform preflight](array-transform-preflight.md), which matched all
predicted positions for a 5° rotation about that centre.

The low-level arrangement editor submitted 5°. Native array readback retained the
same centre/counts and reported the new angle. A separate complete inspection of
every fixture matched the rotated target: XYZ within 1 mm and orientation within
0.05°, using the existing display-rounding tolerances. The supplied square
footprints remained inside the room and outside the synthetic column exclusion;
those dimensions remain test assumptions, not authenticated manufacturer geometry.

Actual DIALux calculation produced WP1 average 497 lx, Uo 0.070 and space LPD
6.5 W/m². These are synthetic measurements, not adopted design criteria. All six
PDF coordinates matched the UI readings. The calculated project was saved, closed
and reopened. A new complete UI inspection again matched **positions and angles**;
the reopened PDF retained positions, product information and summary metrics.
Documentation changes were saved separately and that session was closed.

The driver exited 0. `local/native-rotation-v1/journal.json` records the steps and
three hashed inspection checkpoints. An independent audit reran the after/reopen
checkpoint verifiers, parsed both reports and checked native/source file hashes.
[Artifact hashes and measured values](evidence/native-rotation-v1.json) are retained
in the repository. The original source remained unchanged.

This accepts this six-fixture 5° case on the tested installation. It does not
establish arbitrary native rotation, clipped/irregular array behavior, tilted
fixtures, changed counts/spacing, general interruption recovery or an automatically
guarded bulk-apply workflow. The public preflight remains read-only. A later
reusable apply operation must recheck expected native fields before writes and
verify the complete group afterward.
