# Position-linked luminaire schedule data

`schedule-build --request <request.json>` / MCP `build_luminaire_schedule(layout, report_spec, alignment)` connects the observed drawing-data schema to one complete native PDF product/coordinate section. This produces structured schedule JSON; a formatted drawing table and multi-product assembly remain separate work.

- `layout`: `dialux-agent/layout/v1`, origin `supplied_native_observations`, explicit metre/active-storey coordinates, unique drawing IDs and observation snapshot hash.
- `report_spec`: PDF `path`, `first_page`, `last_page`, exact `expected_header`. The builder rereads the actual PDF with the existing coordinate-table adapter and requires its product quantity to equal the observed fixture count.
- `alignment`: explicit report-to-storey `translation_m: [x,y,z]`, `rotation_deg` about Z and nonempty `evidence`. Even an identity transform must be supplied and explained. This is caller evidence/assumption, not independent validation of the transform or mounting-height origin.

Every observed position must match exactly one transformed report position within 1 mm, and no report record may be reused. Matching is spatial, not list order. The schedule retains drawing IDs, native observation identities where available, actual observed positions/rotations, report numbers/pages, reported manufacturer/article/label/wattage/flux, the PDF byte hash and input-layout/observation hashes. Rotation comes from the native observation, not the report. Total reported fixture power is a transparent quantity-times-wattage calculation; it is not automatically BEC fixed-lighting power, which requires its separate complete-load evidence.

Scope flags explicitly leave live photometry identity, manufacturer dimensions and independently verified coordinate alignment unproven. A PDF product association does not authenticate the live project's photometric asset or establish project completeness/compliance. Only one complete product section is supported, matching the current PDF adapter.

## Native regression

The six moved/observed fixtures from `local/persistent-grid-cad-chain-v1.json` were linked to page 17 of `local/persistent-grid-reopened-report-v1.pdf` (SHA256 `1a5378ecf738071f26676a70b9207df0768ff52d867d01e41356a66277c3eb0d`). The explicit identity transform cites the prior six-position UI/report cross-check on this zero-elevation synthetic room. CAD IDs L0001-L0006 map to report numbers 4,5,6,1,2,3 respectively, demonstrating that row-order matching would be wrong.

Reported product: Philips RC132V G6 36S/840 PSD W60L60 OC ELB3, article 910505102817, six units at 26 W / 3602 lm each; derived reported fixture power 156 W. Public CLI and backend returned the same schedule. Files: `local/schedule-request-v1.json`, `local/persistent-grid-schedule-v1.json`. No assignment schedule was produced.

330 tests passed at this checkpoint, including explicit rotated/translated coordinate correspondence, duplicate IDs, wrong frame/position, non-observed layouts, missing evidence, nonfinite values, count mismatch and missing observation hash.
# Report-linked CAD table

CLI `drawing-export-scheduled --request request.json` and MCP
`export_scheduled_layout_dxf` accept `spec`, `observed`, `fixture_ids`,
`report_spec`, `alignment` and a new `output` DXF path. The tool builds the
observed layout and rereads the PDF through the existing schedule adapter before
drawing anything. All positions must match under the explicit alignment. It
returns both the observed layout and full per-ID schedule alongside the drawing.

The drawing includes a single-product aggregate table (quantity, reported W and
lm per luminaire, total reported W), reported article/product, source hashes and
limits on identity and power-basis claims. It uses editable line/text entities,
not an AutoCAD TABLE object. Native verification compares schedule text and line
geometry after independent DWG reopen. Multi-product tables, flexible sheet
composition and automatic pagination remain pending.

Native synthetic acceptance: `local/scheduled-evidence-v1.json` links six
observed fixtures to the reopened report, yielding 26 W / 3602 lm each and 156 W
total. AutoCAD reopened all fixtures and schedule entities; the A3 1:50 PDF
retained all six labels and the expected physical outline scale. Rendered output
was inspected: the table, product line and source hashes are visible below the
room, without clipping. PDF SHA256:
`6ab49dd4e745a0c1f01e200162c28b8f4d34d446d6ea2a738cceeb8b4367ad72`.
This is a tool-test sheet, not an assignment or complete electrical load schedule.

