# Explicit native CAD dimensions

Both planned and observed layout DXF exports accept an optional `dimensions`
array. Each entry supplies exactly `id` (unique D-prefixed number), `p1_m`,
`p2_m`, `base_m` (XY metre pairs), and `angle_deg` in [0, 180). The length is
the endpoint separation projected along that angle, not necessarily the direct
distance. Projections under 1 mm and nonfinite values are rejected.

The exporter reuses ezdxf's real linear DIMENSION renderer. Dimensions remain
editable native entities, with metre geometry and millimetre labels rounded to
whole millimetres. Text height follows `annotations.fixture_height_m`; choose
the model height for the intended print scale. Explicit endpoints are caller
inputs, not authenticated architectural boundaries. This does not automatically
infer dimension chains or resolve annotation collisions.

`layout-verify-native` now compares dimension IDs retained in XDATA, extension
points, definition point, angle and measured length across native DWG save and
independent reopen. It rejects manual dimension text overrides and changed
millimetre label settings. Visual block fidelity remains a separate gate.

## Synthetic native evidence, 2026-11-09

`local/dimensions-spec-v2.json` uses the generic L-shaped example, 23 fixtures,
explicit 12 m horizontal and 9 m vertical dimensions, 0.25 m fixture/dimension
text and 0.35 m notes. AutoCAD 2027 independently reopened the saved DWG and
preserved both dimension records and all fixtures. Native A3 1:100 plotting
preserved all 23 IDs; outline coordinate error was 0.07749 pt. The rendered PDF
was inspected: 12000 mm and 9000 mm are outside the room, visible and unclipped.
At this scale nominal dimension text height is 2.5 mm. This is a synthetic test
sheet, not an assignment or accepted construction drawing. Visual inspection
also found the L0013 label touches the keep-out outline; annotation collision
handling is therefore a demonstrated remaining issue, not just an untested risk.

- DXF SHA256: `b2ed68764f43bb21974573ce29d65cd25384a9386b57b941a253db6d90366ea3`
- DWG SHA256: `8c677a87818d8097a440cc2a2091414931c421c1d898d08885d241c6c492e407`
- PDF SHA256: `b034fd662ed5f4ab224c3ddc77df0404bb24c83e00526ba1cb816b3441c196cd`

Unit tests include changed endpoints, missing IDs, changed display factor,
manual misleading labels, duplicate IDs and zero projected distances. Suite:
343 passed. Mixed annotation collision handling, titleblocks and formatted
evidence-linked schedules remain pending.
