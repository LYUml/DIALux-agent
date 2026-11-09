# Reused upstream obstacle exchange

Room specifications may include `obstacles`, an explicit list of axis-aligned, ground-supported rectangular boxes. `room-create` and `rooms-create` use the unchanged MIT-licensed upstream `Obstaculo`/`escribir` implementation. No second STF serializer was introduced.

Each box requires exactly `name`, `center_m: [x,y]`, `size_m: [width,depth,height]` and `reflectance_pct: 40`. Width/depth/height must be positive finite metre values, height may not exceed room height, the full footprint must lie inside the room, and box interiors may not overlap. Reserved opening names (`win`, `door`, `skylight`), duplicate names and serialization-control characters are rejected before writing. Rotation, nonzero base elevation, arbitrary meshes and other reflectances are not supported by this adapter; they must not be silently ignored.

The upstream implementation writes centre Z at half box height and `Poly.Color=40 150 150 150`. The explicit 40 percent input acknowledges that fixed material assumption; it is not native material readback. No claim of optical obstruction or furniture import is made from file generation alone. Upstream prose contains conflicting historical descriptions of furniture import, so native validation is required.

`examples/synthetic-obstacles-room.json` contains a 0.6 x 0.6 x 3 m column at (3,2) and a 1.2 x 0.6 x 0.75 m desk box at (1,1). Independent upstream STF reading returned both sizes and centres, including Z=1.5 and 0.375 m. `local/synthetic-obstacles-v1.stf` is prepared for a separate native import/calculation/reopen gate after the active large-group scan. It is a synthetic tool fixture only. Neither the assignment DWG nor assignment design was changed.

## Native import, calculation and reopen gate

The synthetic STF was imported through the independent CLI and saved as `local/obstacles-native-v1.evo`. Both named items appeared under the native Furniture and objects tree. New CLI `desktop-read-furniture --expected-project <project.evo> --tree-item-id '<exact ID>'` / MCP `desktop_read_furniture` selects the exact materialized object, establishes storey context and reads its name, prototype label, reference XYZ, rotation and dimensions. It does not equate a prototype label with verified material or mesh geometry.

Native readbacks were:

| Object | Reference XYZ (m) | Size XYZ (m) | Rotation |
| --- | --- | --- | --- |
| Test column | 3, 2, 0 | 0.6, 0.6, 3 | 0, 0, 0 |
| Test desk box | 1, 1, 0 | 1.2, 0.6, 0.75 | 0, 0, 0 |

The STF uses the box centre Z, while native furniture properties expose its bottom reference point for these imported boxes. The API therefore names the field `reference_position_m`, not centre position. General furniture origins remain model-dependent.

The documented real manufacturer ULD was imported and six luminaires were automatically placed. A real calculation completed. Native report `local/obstacles-report-v1.pdf` has 28 pages and SHA256 `f29ea1c2a1eb8da132405c02b0f035cbc9384c50f18435713374a305b105a3ef`; the exact Synthetic obstacles room summary on pages 14-15 reports 24 m2, 497 lx average perpendicular illuminance, Uo 0.063 and 6.5 W/m2. Rendered page 14 visibly includes the column and desk outlines and a low-value region around the central column. This is observed native test behaviour, not a compliance claim or a controlled proof isolating each object's optical contribution.

The calculated native file was saved (551,566 bytes, SHA256 `9007f05d9f063de6828d93818f15ae3c7fc7f2abdf316e331453cdff74291d27`), closed and reopened. Both objects' names, prototype labels, reference coordinates, sizes and rotations matched their prior readings. The first reopen read correctly stopped because FurnitureTool was unavailable in the current mode; the adapter now explicitly restores native building-construction mode before reading. The repeated public-backend read passed. Local evidence: `obstacles-native-readback-v1.json`, `obstacles-reopened-readback-v1.json`, `obstacles-results-v1.json` and rendered summary. 308 tests passed, including wrong-identity rejection and mode recovery.

These gates establish this imported box case. Arbitrary furniture meshes, openings, rotated/elevated boxes, verified material properties and large-scale obstacle editing remain separate development work.
