# Rigid array geometry preflight

`layout-array-transform-plan --request request.json` and MCP
`plan_array_transform(spec, observed, arrangement)` perform offline preflight for
a rigid array translation/rotation. They do not edit DIALux, save, calculate or
establish that supplied observations still match a live project.

The target `spec` uses the existing full-footprint grid planner. `observed` must
contain the complete group assembled by native inspection, and `arrangement` must
be the `desktop-read-arrangement` result for the same project/group in active-storey
coordinates. Both must come from the same reviewed state; the function cannot
authenticate that assertion. Verify hashed inspection pages separately.

The preflight requires:

- A complete rectangular array whose native X/Y counts multiply to the unchanged
  fixture count, with complete pagination and unique runtime identities.
- A native centre matching the full fixture centroid, and all individual fixture
  angles matching the array angle within existing display-rounding tolerances.
- A rigid transformation of **every** observed position that matches the target
  plan. Matching only the centroid would incorrectly accept distorted layouts.
- Target fixture footprints satisfying the existing room/exclusion/clearance
  planner; dimensions and semantic room boundaries remain supplied assumptions.

It reuses Shapely rotation, the existing observation validator and full geometry
matcher. It returns centre XYZ/angle parameter values plus input hashes and
predicted matching evidence. A changed fixture count, changed spacing, independent
fixture displacement or inconsistent evidence is refused. No fallback guesses or
automatic edits occur. Tilted fixtures and incomplete/clipped native arrays are
outside this contract.

Before a later native edit, re-read project/group identity and all expected array
fields. After editing, inspect every fixture again, recalculate and verify native
save/reopen. The existing low-level arrangement editor is not a transactional
executor for this plan. A public guarded apply operation is still pending.

## Reproducible synthetic example

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent layout-array-transform-plan --request examples/synthetic-array-transform.json
```

The example contains invented test observations/runtime IDs for `synthetic.evo`;
never send those IDs to a real desktop edit. It plans six fixtures from centre
(3, 2, 3.035) m to (3.1, 2.2, 3.135) m. This is geometry-only test output.

Twenty-one tests cover translation, rotation about a known centre, a nonzero
initial angle and refusal of changed geometry, incomplete/ambiguous identities and
invalid field shapes. Separately, archived native evidence for all 168 translated
fixtures passed the existing hashed-checkpoint verifier and then this preflight
for a further 0.1 m X/Y translation. The predicted centre was (15.2, 17.2, 3.035) m.
`local/large-array-next-transform-preflight-v1.json` records that offline result;
it is not a newly executed native movement.

The separate [six-fixture native 5° test](native-array-rotation.md) subsequently
used this preflight before the low-level array editor. All positions/angles,
calculation and save/reopen passed in that case. It does not turn this planner
into a guarded native apply command.
