# Native luminaire symbol verification

`verify_layout_native` now compares the definitions of every block referenced by `LUMINAIRES` inserts before and after the native AutoCAD DWG save/reopen. Previously it verified insertion records and block names but explicitly did not verify block shapes.

The supported agent symbol grammar is LINE, LWPOLYLINE and one FIXTURE_ID ATTDEF. Evidence includes block base points, line endpoints, polyline vertices/start-end widths/bulges, closed state, elevation, constant width, extrusion and thickness, plus the ID attribute definition. Unknown entity types, missing shapes or unexpected attribute definitions fail closed. Nested blocks and arbitrary manufacturer symbols are not supported. Appearance such as fonts, colors, linetypes and lineweights is not established by this geometric comparison.

The native manifest records both sets of block definitions and the verified block names. Geometry uses absolute 1e-8 tolerance; records are compared independently of block entity ordering. Existing insertion/rotation/scale/label, dimensions, table and sheet checks remain in place. Plotting is a separate gate.

## Native validation, 2026-11-09

A fresh headless AutoCAD save/reopen of the existing six-fixture synthetic combined sheet passed the new shape check, along with its two dimensions, 28 schedule entities and 12 sheet entities. Local evidence: `local/symbol-verification-native-v2/manifest.json`.

- Source DXF SHA-256: `e91988aedda64b12343d038359b61c2d5b30f4abef8290c18f15872ed8be2ee6` (unchanged).
- Native DWG SHA-256: `ef363b8a2b458427ff14fd7efd5588507eae26f59c50418ef6aef39b519cfd78`.
- Verified block: `DIALUX_AGENT_PANEL`.

Negative tests keep insertion records identical while changing the block's width, diagonal line, closed state, bulge, base point, attribute size, entity count or thickness. Each is detected. Tests also cover two differently sized symbols, tiny native floating-point roundoff and rejection of unsupported entities. The native case above is a single symbol; mixed-product CAD generation and native validation remain outstanding.
