# Larger native plotting paper and annotation sizes

`layout-plot-native --paper A1 ...` / MCP `plot_layout_native(..., paper='A1')` selects ISO landscape paper. A3 remains the default; A2, A1 and A0 have explicit allowed dimensions and PDF media-size verification. The generated scale note names the selected sheet. The native gate below verifies A1; A2/A0 are implemented options, not separately demonstrated native gates.

Drawing specifications may set `annotations: {fixture_height_m: 0.25, note_height_m: 0.35}`. Heights are finite model-space metres, 0.02 to 2. Defaults remain 0.12 and 0.18 m. At 1:100 the test's intended printed heights are 2.5 and 3.5 mm. This setting does not automatically prove collision-free labels or readability for arbitrary geometry; inspect the plot.

## Native synthetic gate

A separate *planned*, not UI-observed, 30 x 34 m / 168-symbol test drawing exercised native DXF-to-DWG save, independent DWG reopen/readback, and A1 1:100 PDF output. All 168 IDs, coordinates, rotations and scales survived reopening. PDF text checks found every ID once. The rendered full sheet showed the 14-by-12 grid, separate labels and notes without clipping. It remains a synthetic tool sheet without a titleblock/dimension system or assignment design.

- DXF `local/large-planned-drawing-v1.dxf`: `d8c42af6bc531843f8850184b19f0ea76a17e4682bdcfc2c1a2aaabcfa63c78a`.
- DWG `local/large-planned-native-v1/layout.dwg`: `c4276274862ff3cf1d0473940a3f8098ec6bd900248e428ba5995d3710f3b22c`.
- PDF `local/large-planned-A1-v2/layout.pdf`: `8096d374b0271f5f1cd5959f73db106262e999129e6880055454d7a45030bf88`.

The 30-by-34 m room outline matched 1:100 physical vector dimensions with maximum deviation 0.05953 PDF points. The first run preserved in `local/large-planned-A1-v1` failed verification because pdfplumber classified the rectangular outline as a rectangle rather than a curve. The verifier now includes native rectangle paths with implicit closure while retaining straight-edge, unique-match, scale and tolerance checks. No success manifest was written for the failed first run.

This verifies native plotting capacity for a larger planned set. The long DIALux UI observation checkpoint and its geometry verification are separate; this drawing must not be presented as its readback output. Original files are preserved, and the tested output is not a submission artifact.
