# Fixed-scale native CAD plot verification

`layout-plot-native` / MCP `plot_layout_native` retains fit-to-page as its default. For a fixed scale, supply `--scale-denominator 50 --scale-outline <outline.json>` (or MCP `scale_denominator` and `scale_outline_m`). The outline file is an explicit XY polygon in model metres. Supported denominators are 25, 50, 100, 200 and 500. This is still a synthetic-tool-test plot, not a completed engineering sheet.

Autodesk documents custom plot scale as paper inches/millimetres per drawing unit in its [Plot dialog reference](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-Core/files/GUID-264D3513-0D22-4461-82D6-14F391BC5CDE.htm) and [page-size/scale setup guidance](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-setup-page-size-and-scale-for-plotting-in-AutoCAD.html). For a metre model at 1:N, the native custom ratio is `1000=N` (paper mm : drawing metres). The plot script rejects non-metre INSUNITS, replaces the single original fit-to-page note in the copied drawing with `1:N at A3 (print 100%)`, and leaves the original DWG unchanged.

Verification uses the PDF vector paths, not the scale note alone. Exactly one closed straight path must match every vertex of the supplied outline at `1000/N × 72/25.4` PDF points per metre, allowing translation, cyclic start and reversed path direction. Coordinate tolerance is 0.25 pt (about 0.088 mm on paper). Wrong scales, curved candidates and ambiguous duplicate matches fail. Existing A3 paper, fixture-label and rendered-edge checks remain active. The manifest records the matched path index, maximum error, denominator, expected factor and outline hash.

This proves the supplied outline's size in that PDF at its original page dimensions. It does not authenticate the input outline, prove all dimensions, prevent a printer/viewer from rescaling, or guarantee text legibility for every selected denominator.

## Native evidence, 2026-11-09

The five-fixture concave synthetic DWG was plotted at 1:50 to `local/concave-scale50-v1/layout.pdf` (SHA256 `aea579ff5f70d4c260c929be300b61e6f510457044bc652b77830908b507de0c`). Expected factor: 56.6929133858 pt per model metre. Maximum matched outline coordinate error: 0.077480315 pt. All five fixture IDs appeared once. The rendered preview showed the complete concave outline, symbols, labels, evidence hashes and correct scale note without clipping.

A separate native 1:25 attempt using the same drawing did not fit the complete content on A3. It was rejected for missing/duplicated expected plot labels/IDs, and no success manifest was written. The workflow did not silently switch to fit-to-page. The failed PDF/log remain in `local/concave-scale25-rejection-v1` for inspection.

250 tests passed at this checkpoint. Dimension annotations, a standard titleblock and broader engineering-sheet acceptance remain separate work. No assignment drawing was produced.
