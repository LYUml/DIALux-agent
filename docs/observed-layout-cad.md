# CAD export from native fixture observations

`drawing-export-observed --request <request.json>` / MCP `export_observed_layout_dxf` exports the supplied native fixture coordinates directly. It reuses the existing editable block writer, DXF readback checks, native DWG verification and plotting tools. It does not rebuild a lattice or snap observed positions.

The request contains `spec`, `observed`, `fixture_ids`, and a new `.dxf` `output` path. `spec` requires metre units, active-storey frame, contour, explicit fixture product/dimensions/mounting height, clearance and source assumptions; exclusions are optional. No grid specification is required. `fixture_ids` is a unique list of `L` followed by 1–12 digits, corresponding exactly to observation order. IDs are assigned by the caller, not inferred as persistent native object identities.

The returned `observed_layout` uses the shared layout schema and carries each ID, XYZ, Z rotation, observation index, optional session-local runtime ID and observed display name. It also carries the specification and observation hashes. Those two hashes are included in the drawing notes. Geometry is checked using the existing room-envelope verifier before any output is written. Product identity, manufacturer dimensions and optical performance are not inferred from the supplied coordinates.

This is a 2D plan drawing: CAD insertion Z is zero while the shared layout retains actual observed mounting Z. Native CAD reopening compares CAD records, not a full 3D luminaire model. Planned-grid export remains strict: a caller cannot use its optional layout argument to bypass matching the grid specification.

## Native evidence, 2026-11-09

The five fixture readings from the synthetic concave DIALux case were exported with IDs L0001–L0005. Their actual XY positions were (1,1), (3,1), (5,1), (1,3), (3,3) m, with Z=3.035 m. The observation snapshot hash is `6311d86905e9676388c793ad5b95afd3d526c4772e636a86d1fee74784c9f341`.

- DXF `local/concave-observed-layout-v1.dxf`: SHA256 `7910e2a9f7f3c99ca5c683b7809f7c6d827a4b558b6da96722766bb6083af08a`.
- Native AutoCAD saved/reopened DWG `local/concave-observed-native-v1/layout.dwg`: SHA256 `14dd7234465993fa13d0be693635b1349ef42406a6761dfcad96a2cd73322402`; all five fixture IDs, CAD positions/rotations/scales and block names matched through the independent reopen/readback workflow.
- Native PDF `local/concave-observed-plot-v1/layout.pdf`: SHA256 `e1d9000be63aaade28fbcb5df026b0c2c1cd40b51c63bd59dc54885abd1cb089`, one A3 page. Text checks found every expected ID once; rendered preview showed the concave outline, five symbols and readable IDs/notes without clipping.

The plot is fit-to-page and clearly labelled SYNTHETIC TOOL TEST / NOT FOR SUBMISSION OR CONSTRUCTION. This is not an engineering-scale titleblock/dimensioned deliverable, does not authenticate the observation source, and does not establish whole-project or simulation correctness. No assignment drawing was produced.

245 automated tests passed at this checkpoint, including arbitrary non-grid positions/rotations, explicit ID order, rejection before writing of bad geometry/partial evidence/invalid IDs, and real MCP discovery.
