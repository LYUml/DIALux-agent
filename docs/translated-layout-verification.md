# Shared layout/native position verification

2026-11-09 synthetic test only. A new `position-probe-v1.evo` copy was made from the four-fixture test project. Public CLI `desktop-edit-arrangement` changed PolygonPosition_X/Y from (3,2) to (3.2,2.1). Public group inspection then observed all four positions at (1.7,1.1,3.035), (4.7,1.1,3.035), (1.7,3.1,3.035), (4.7,3.1,3.035), with zero rotation.

`examples/synthetic-translated-grid.json` independently specifies those expected fixture centres via the shared grid planner. CLI `layout-verify-observed` matched all four observations, without relying on their ordering. The comparison allows 1 mm per coordinate for displayed precision and 0.05 degrees per rotation axis, treating angles cyclically. Ambiguous nearby candidates, duplicate use, count contradictions, invalid numbers and tilted fixtures fail verification.

This comparison authenticates neither input provenance nor whole-project completeness. It does not verify product photometry identity. The inputs are hashed in the result so the supplied evidence can be tracked. Scope flags explicitly remain false for whole-project, photometry and simulation verification.

The same planned fixture data was exported through `layout-export-dxf` and `layout-verify-native`:

- DXF SHA256 `5b7040e44c01bf27fb0c06e222878e9c739d95ab864f7bf767fcb75ac0fe0603`.
- Native DWG SHA256 `90da799cf6ff3ddaa74e9c7d7e5eca58298edf964ed8e46e127908f872866f68`.
- Separate AutoCAD reopen verified four fixture records and metre units. Printed appearance and block-shape fidelity remain unverified.

Fresh DIALux calculation after translation displayed 362 lx average and 0.40 uniformity, compared with 364 lx and 0.48 before translation. This shows a changed geometric arrangement was calculated, not that this test layout is acceptable lighting design. No assignment work was produced.

140 automated tests passed, including wrong position, duplicate matching, tilt, count mismatch and nonfinite input cases. Native observations are recorded separately from unit-test evidence. Full arbitrary layout application, independently controlled individual fixtures, native CAD plotting, multi-room reports and large-project scalability remain development work.
