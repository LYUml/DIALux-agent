# Explicit CAD boundary extraction

`drawing-extract-boundary --request <request.json>` / MCP `drawing_extract_boundary` extracts one selected DXF modelspace entity. It does not infer a room from ceiling grids or text labels. Convert DWG with the existing native `drawing-convert` workflow first, preserving the original.

Required request fields:

- `path`: DXF file.
- `handle`: explicitly selected hexadecimal entity handle.
- `expected_sha256`: current DXF byte hash, binding selection to a particular source version.
- `storey_origin_m`: `[x,y]` origin of the intended storey frame, expressed in drawing WCS metres.
- `storey_rotation_deg`: counterclockwise orientation of the storey axes relative to drawing WCS.

The transform is `storey_xy = rotation(-angle) * (drawing_wcs_metres - origin)`. It is caller-specified, not inferred or measured in DIALux. The result preserves both coordinate lists, source hash, handle/layer, INSUNITS conversion, elevation, area, perimeter and the transform. Source INSUNITS values 1, 2, 4, 5 and 6 (inch, foot, millimetre, centimetre, metre) are supported. Unspecified/other units are refused.

Only closed straight LWPOLYLINE entities directly in modelspace are supported. Open/self-intersecting polygons, bulges, widths, non-default OCS extrusion, block/paperspace selection and changed source bytes are rejected. No curve approximation or hole discovery is attempted. Nonrectangular concave boundaries are supported. `semantic_room_boundary_verified` and `native_dialux_geometry_verified` remain false: selecting a valid polygon does not prove that it is the intended room or that it matches the DIALux model.

Verification on 2026-11-09:

- Millimetre concave test with a translated origin and 90-degree axis rotation yielded the expected 5 m² polygon; original DXF bytes remained unchanged.
- Negative tests exercise open paths, bulges, widths, reverse extrusion, self-intersection, unspecified units, paperspace and stale source hashes.
- Public CLI extraction from the existing synthetic AutoCAD DWG save/reopen DXF (`local/print-native-v3/reopened/source-copy.dxf`, SHA256 `a7be6c698d5465b4998b54ddc4b2757fe4e7eceff5dd1e5cb3f764acacf500bc`) selected ROOM handle `34`, obtaining (0,0), (6,0), (6,4), (0,4), 24 m² and 20 m perimeter. This uses an earlier native roundtrip artifact; the new concave transform test is programmatically generated, not a new native CAD roundtrip.

No assignment boundary was chosen or assignment design created.
