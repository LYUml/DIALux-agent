# Reused upstream obstacle exchange

Room specifications may include `obstacles`, an explicit list of axis-aligned, ground-supported rectangular boxes. `room-create` and `rooms-create` use the unchanged MIT-licensed upstream `Obstaculo`/`escribir` implementation. No second STF serializer was introduced.

Each box requires exactly `name`, `center_m: [x,y]`, `size_m: [width,depth,height]` and `reflectance_pct: 40`. Width/depth/height must be positive finite metre values, height may not exceed room height, the full footprint must lie inside the room, and box interiors may not overlap. Reserved opening names (`win`, `door`, `skylight`), duplicate names and serialization-control characters are rejected before writing. Rotation, nonzero base elevation, arbitrary meshes and other reflectances are not supported by this adapter; they must not be silently ignored.

The upstream implementation writes centre Z at half box height and `Poly.Color=40 150 150 150`. The explicit 40 percent input acknowledges that fixed material assumption; it is not native material readback. No claim of optical obstruction or furniture import is made from file generation alone. Upstream prose contains conflicting historical descriptions of furniture import, so native validation is required.

`examples/synthetic-obstacles-room.json` contains a 0.6 x 0.6 x 3 m column at (3,2) and a 1.2 x 0.6 x 0.75 m desk box at (1,1). Independent upstream STF reading returned both sizes and centres, including Z=1.5 and 0.375 m. `local/synthetic-obstacles-v1.stf` is prepared for a separate native import/calculation/reopen gate after the active large-group scan. It is a synthetic tool fixture only. Neither the assignment DWG nor assignment design was changed.
