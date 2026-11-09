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
