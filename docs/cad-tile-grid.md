# Explicit CAD tile grid reading

`drawing-read-tile-grid --request request.json` and MCP `drawing_read_tile_grid`
read all modelspace entities on a caller-selected DXF layer. The request contains
`path`, `expected_sha256`, `layer`, `storey_origin_m` (drawing WCS metres), and
`storey_rotation_deg`. DWG must first be converted through the existing native
conversion tool. Original files are read only.

The reader uses the existing ezdxf and Shapely dependencies. It requires explicit
supported INSUNITS, 2–10000 closed straight four-vertex LWPOLYLINE tiles, common
rectangular size/orientation/elevation, and unique integer lattice cells. Curves,
widths, extrusion changes, thickness, extra entity types, duplicate cells and
off-grid centers fail instead of being silently filtered. Linear tolerance is
0.01 mm. Units are not inferred. Source SHA-256 is checked before and after reading.

The returned `grid` has the same origin/spacing/rotation keys consumed by
`plan_grid`. Its origin is a selected tile center, not a room corner. Orientation
is canonical within 0–90 degrees; the corresponding X/Y dimensions follow those
axes. Missing cells are permitted and each present tile retains its entity handle
and integer cell. A rectangular lattice is geometric evidence only: it does not
establish that the layer represents a ceiling, validate ceiling coverage, infer a
room boundary, or choose a fixture layout. Extending this grid across a room may
include missing cells; placement still requires explicit geometry and constraints.

Validation uses synthetic millimetre DXF tiles rotated 23 degrees in drawing WCS
and transformed to a storey rotated 13 degrees. Tests check the resulting 10-degree
0.6 by 0.3 m grid, omitted cells, unchanged source bytes and rejection paths.
Both CLI invocation forms and a real stdio MCP call exercise the public interface.
No assignment design or native DIALux placement is performed by this reader.

Regression coverage also rewrites all eight start-vertex/winding combinations
at three storey rotations, including axis-aligned quarter-turn boundaries.
The original implementation failed three of these cases because floating-point
noise changed the selected bottom-row anchor or canonical axes. The reader now
treats bottom-row coordinates within its linear tolerance as one row and snaps
quarter-turn angle round-off below 1e-12 radians. A synthetic 2800-tile layer
checks complete handle-to-cell coverage. Full suite after this repair: 625 passed.

## Native AutoCAD round trip

On 2026-11-09, AutoCAD 2027 Core Console saved a synthetic 70 by 40 tile DXF
as a native DWG. The existing `drawing_convert` tool reopened a copy of that DWG
and exported DXF. Each tile was 600 by 300 mm, rotated 23 degrees in drawing WCS;
the explicit storey transform used origin (10,20) m and rotation 13 degrees.
Both extracted grids had the same 2800 integer cells, metre spacing and origin,
and 10-degree rotation (numeric comparisons within 1e-8). Native INSUNITS was 4.
The original DXF hash remained unchanged. Core Console used no desktop pointer.

Local evidence: `local/tile-grid-native-v1/evidence.json`, SHA-256
`ed01f42409293a99570c4ac0b3073bc76fe5224b30041a28cb76147bbbb19815`.

| Artifact | SHA-256 |
| --- | --- |
| Original synthetic DXF | `ee9ef63067d7974ed08424888e4c5a48c276413ba9cd939bae110b196c222e62` |
| Native DWG | `70bcc63bb9c151230daa4270b4e3d41fda59adb4249065b8f34cc98d9c2061b6` |
| Reopened/exported DXF | `b534c66c134fda7b63ce3126329e39b79dfa1e1509d5518be6e09fe48c773550` |

This closes the bounded native serialization/readback check for this tile case.
It does not prove visual plotting, arbitrary ceiling geometry, semantic layer
selection or fixture placement. No assignment source was used in this test.

The source generator and native round-trip checks are now reproducible from the
repository root using:

```powershell
.venv/Scripts/python.exe -m scripts.validate_native_tile_grid --output-directory local/tile-grid-fresh-run
```

Requires installed AutoCAD Core Console (2027 default; override `--executable`).
The script creates only synthetic geometry, uses a copy for native writes, refuses
existing output directories and retains failure journals/logs. It does not touch
DIALux or the shared pointer. A fresh run of this checked-in script passed all
2800 cells/parameters; local `tile-grid-reproducible-v1/evidence.json` hash is
`497a597a38a10664e9e2cd052bddd50bd33a3e460af0b80458cc42472e0e2b40`.
Repeating against the same directory was rejected and the evidence hash stayed
unchanged. File hashes vary with generated CAD metadata; compare geometry and
the hashes recorded by each run rather than requiring identical bytes across runs.

## Fixture coverage against present cells

`layout-verify-tile-coverage --request request.json` / MCP
`verify_layout_tile_coverage` accept `{ "layout": ..., "grid_request": ... }`.
The grid request is the source-pinned extraction request above; the tool rereads
the DXF rather than trusting a supplied extracted grid. The layout is metre-unit
`layout/v1` with unique fixture IDs, XYZ positions and explicit `footprint_m`
polygons. Footprint centroids must match supplied XY positions.

The tool reconstructs the verified canonical tile rectangles and checks each
complete footprint against their union, allowing the reader's 0.01 mm geometric
tolerance. Missing cells remain holes. Results retain uncovered area before
tolerance, per-fixture coverage and a layout hash. `all_supplied_footprints_covered`
is the decision field: CLI exit zero means the audit ran, not that every footprint
passed. Invalid source or layout evidence is rejected.

This is a separate, explicit check after planning. `plan_grid` still extends a
lattice across the supplied room and does not silently apply this filter. The
check does not authenticate product dimensions, ceiling suitability or native
positions. Tests include missing cells, partial overhang, footprints spanning a
hole, stale source hashes and both CLI forms plus real stdio MCP execution.

The coverage adapter was additionally exercised against the native round-trip
DXF above: 168 synthetic 0.58 by 0.28 m footprints at known interior cell centers
passed, while a deliberately overhanging 169th footprint failed with 0.028 m²
uncovered area. The fixture geometry was independently constructed at 10 degrees
in storey coordinates. Local `coverage-request.json` reproduces this check through
the CLI; `coverage-audit.json` SHA-256 is
`f8558b920b0e1a85fca814627e416614b8f15281be76cc28916d5508640c39de`.
These are synthetic supplied envelopes, not observed DIALux fixtures. Two further
regressions distinguish a present cell and a missing cell with a translated,
37-degree drawing and 12-degree storey transform; all 11 coverage tests pass.
