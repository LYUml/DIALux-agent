# Reproduce a framed synthetic CAD drawing

Run from the repository root after installing the Python dependencies. DXF export
uses ezdxf; the native verification/plot steps require the installed AutoCAD 2027
Core Console at the CLI default path. This does not control DIALux or create an
assignment. All output paths must be new; existing files/directories are refused.

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent layout-export-dxf --spec resources/examples/synthetic-framed-layout.json --output local/example-sheet.dxf
.\.venv\Scripts\python.exe -m src.dialux_agent layout-verify-native --path local/example-sheet.dxf --output-directory local/example-sheet-native
$fixtureIds = 1..23 | ForEach-Object { 'L{0:D4}' -f $_ }
.\.venv\Scripts\python.exe -m src.dialux_agent layout-plot-native --path local/example-sheet-native/layout.dwg --output-directory local/example-sheet-plot --fixture-ids $fixtureIds --scale-denominator 100 --scale-outline resources/examples/synthetic-framed-outline.json --paper A3
```

The example contains an L-shaped room, keep-out region, 23 synthetic panel
symbols, two actual linear dimensions, bounded label placement and a fixed-paper
titleblock. It contains no photometry or simulated lighting claim. The outline
file is the same explicit room contour used for independent PDF vector-scale
verification; keep these files consistent when adapting the example.

Review the JSON results and `local/example-sheet-plot/preview.png`. Successful
native verification checks fixture IDs/geometry/label anchors, dimensions and
sheet entities across DWG reopening. Plot checks include one-page paper size,
all expected IDs and the room outline's physical scale. They do not replace
visual review or establish engineering compliance.

These three public CLI commands were exercised on 2026-11-09 with separate
`portable-sheet-*-v1` output paths. All completed successfully. This example uses
only repository inputs; no ignored local report or project is needed.
