# Native CAD plot checkpoint

2026-11-09 synthetic tool test. `layout-plot-native` / MCP `plot_layout_native` plots a copy of an agent-generated DWG through installed AutoCAD Core Console, with explicit ACAD product selection, foreground plotting, A3 landscape, extents fit and monochrome output. It never saves page-setup changes to the original DWG. This reuses the native plotting approach from BSE3124, with an explicit model-space setup for the synthetic fixture rather than its course-specific saved layouts.

The command requires a new output directory and expected unique fixture IDs. It verifies process completion, source-file hash preservation, a single A3 page, extracted test labels and the exact fixture-ID multiset. It renders a preview and rejects blank pages or content touching the paper edge. Automated checks do not set `visual_review_verified`; inspection remains independent.

The first native plot exposed two real output issues: SHX text was not extractable, and the one-line specification hash unnecessarily widened the plot. The CAD exporter now uses Arial TrueType, splits the hash into two lines, describes layers without relying on colour, and explicitly labels fit-to-page as not to scale. The paper uses printable margins rather than full bleed.

Public CLI acceptance: exported the synthetic translated grid, saved/reopened it through native DWG, then plotted it. All four fixture labels were extracted exactly once. Source DWG SHA256 `b5abeb18da21d5aa76f044320fda7698dc1fe30ba8e44ed69f31809b456278df`; PDF SHA256 `b6831cd70bbc9ad28f9a1ca6d7aef3b7c33fb34d2ee6f422118bc06ba5ee931d`. Output is ignored `local/native-plot-v3/layout.pdf` with manifest and preview alongside it.

Visual review: independently rendered this final PDF with system Poppler at 120 dpi and inspected `poppler-preview.png`. The room outline, four fixture symbols/IDs, test disclaimer, units, mounting height, non-scale note and hash are visible with no observed overlaps or clipping. This is evidence for this test file only, not an automatic assertion for future plots. Engineering title blocks, dimensions, selected scales, complex layouts and submission drawing acceptance remain incomplete.

155 automated tests passed. Tests include existing-output preservation and rejecting ambiguous expected IDs; the native execution and visual check above are separate evidence.

Command prompts follow Autodesk's [-PLOT command reference](https://help.autodesk.com/view/ACD/2027/ENU/?caas=caas%2Fdocumentation%2FACD%2F2014%2FENU%2Ffiles%2FGUID-625E395D-143A-494F-A1EA-1BF119B927DC-htm.html). No assignment drawing was made.
