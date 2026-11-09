# Native report luminaire coordinate tables

`report-layout-read --path <report.pdf> --first-page 17 --last-page 24 --expected-count 168 --expected-header '<exact building/storey/room header>'` / MCP `read_report_layout` reads an explicitly selected English native DIALux coordinate-table section. This is a tool test, not an assignment design.

The parser locates the X/Y/Mounting/Luminaire column headers by PDF word position and crops the coordinate table. It does not parse the overlapping arrangement-description text to its left. Every cropped row must contain three metre values and a report luminaire number. Pages must have the same explicit room header, and the complete selected section must provide exactly consecutive IDs 1 through N. Unexpected rows, duplicate/missing IDs, a second product section, different room headers or non-metre units are rejected. First-page product metadata retains article number, manufacturer, reported label, wattage and luminaire flux with its source page. Multi-product/multi-arrangement sections and other report languages/layouts are not yet supported.

Coordinates retain `coordinate_frame: report_unspecified`: the table labels mounting height, and this must not automatically be treated as absolute storey Z for arbitrary elevations. Rotation is unavailable. Report IDs are not session runtime IDs. Product metadata is evidence from the PDF, not authenticated per-fixture live product binding or proof of a fresh simulation.

## Native synthetic regression

For `local/large-report-v1.pdf` (SHA256 `d6983b5309b8415bca24945070de73c4899e63f63503f99d21c363348eba7f42`), pages 17-24 yielded 168 complete records, article `910505102817`, quantity 168, 26 W and 3602 lm per luminaire. Page 17 was rendered and visually inspected: the table starts at X=1.071, Y=32.583, mounting height=3.035, ID=1. Its left-side arrangement origin instead states Y=1.417, demonstrating why column-boundary extraction matters.

All 168 report XYZ triples uniquely matched the explicit 14-by-12 zero-offset synthetic grid within 1 mm; maximum coordinate difference was 0.000428571429 m. This is evidence of positional correspondence for this case, not general coordinate-frame or rotation verification. The parsed artifact `local/large-report-layout-v1.json` SHA256 is `241ad2d868a58f838b09c5f0f6ef2dd9dc8528b60e164281791d951493734487`. The independent full native UI inspection remains a separate gate. No report output or assignment material was modified.

285 tests passed at this checkpoint, including explicit ambiguity/incompleteness refusal. Parsing a few sample pages is not evidence of support for every DIALux report format.
