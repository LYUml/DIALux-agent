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
