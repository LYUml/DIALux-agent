# Room/scene-scoped report reading

`report-read-all --path <report.pdf>` / MCP `read_report_pdf` extracts recognized English two-page room summaries as separate records. Each record carries its normalized full room/scene header, a SHA256-based header identity, original page numbers and measurements with exact PDF-byte hash evidence. No metric averaging or room aggregation is performed.

Pairing is strict: pages must be adjacent, both full headers must match, pairs must be complete and room/scene headers must not repeat. A reused room name in a different light scene remains a separate identity. Repeated headers in the same document are ambiguous and rejected. Unknown report formats and unrecognized sections do not establish project coverage; `complete_project_coverage_verified` remains false.

`report-check --summary-id <id> ...` / MCP `check_report_summary` applies a supplied criteria profile and context only to the exact selected summary. Missing IDs fail instead of falling back to another room. Context applicability remains caller-evidenced for that room/scene. The whole-project assessment flag stays false. Existing single-summary `report-read` and `report-check` without an ID retain their strict rejection of multiple summaries.

Verification on 2026-11-09:

- Synthetic text tests exercise three independent room/scene records, differing values, original page numbers, duplicate headers, missing pages, nonadjacent pairs and cross-room mismatches.
- Each of two existing native test PDFs was read through the new PDF backend. A separate read-only combined-text test of those files produced two distinct summary pairs at pages 14/15 and 42/43, preserving their separate 531 lx and 104 lx values. This is not a native multi-room export and is not presented as one.
- Public scoped criteria checking of the acceptance PDF with the HK BEC profile and no applicability facts returned `unverified`; it did not infer office applicability or claim whole-project compliance.
- 161 automated tests passed, including verification that the criteria engine receives only the selected room's measurements and explicit context. MCP discovery includes both new tools.

## Native three-room checkpoint

On 2026-11-09, independent desktop CLI calculation and PDF export completed for the synthetic `three-room-B-v1.evo` project. Public `report-read-all` reads the resulting 39-page `local/three-room-B-report-v1.pdf` (2,475,915 bytes; SHA256 `86159502dd89c02c69c510f3746b6fb6639eb86171fcc05443e34e7ed10f8b43`). Its summaries are:

| Room | Pages | Average lx | Uniformity | LPD W/m² |
| --- | --- | --- | --- | --- |
| Synthetic A | 15–16 | 0 | unavailable (`-`) | 0 |
| Synthetic B | 20–21 | 693 | 0.57 | 9.75 |
| Synthetic corridor | 28–29 | 0 | unavailable (`-`) | 0 |

The parser now recognizes custom building names in the native building/storey/room header. A numeric uniformity is retained as a measurement; an explicit dash is recorded separately in `unavailable_measurements`, with surface identity, original page and PDF hash. Missing rows, conflicting surfaces and ambiguous pairs still fail. The criteria engine receives no fabricated numeric uniformity and returns unverified when a criterion requires it. Raw calculation monitor values now explicitly advertise that room/surface scope is unverified.

This verifies native multi-room report separation, not complete multi-room placement: only B contains luminaires. The public automatic arrangement guard still prevents adding another room's arrangement after existing calculation-ready content; that capability remains unfinished. The parser does not extract minimum illuminance or glare. No assignment report was produced.
