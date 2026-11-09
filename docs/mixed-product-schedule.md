# Mixed-product position-linked schedule

CLI `schedule-build-mixed --request request.json` and MCP `build_mixed_luminaire_schedule` build data for a mixed-product drawing schedule. Rendering is available through the separate [mixed-product CAD exporter](mixed-product-cad.md).

The request contains:

- `groups`: objects containing `report_group` and `layout`. Each layout must be the existing observed active-storey metre layout, with unique drawing IDs, an observation hash and a distinct `source_group_id`.
- `report_request`: the explicit native arrangement-report request documented in [mixed-product report reading](mixed-product-report-reading.md).
- `alignment`: `translation_m`, `rotation_deg` and a nonempty statement of coordinate-correspondence evidence/assumptions, as in the single-product schedule API.

The report is read once. Every declared report group must have exactly one supplied observed group. Product association uses the report group and unique spatial correspondence; the existing single-product spatial linker and observation validators are reused. Duplicate drawing IDs or observation groups, swapped group mappings with mismatching coordinates, coincident report positions across groups, missing/invalid evidence and incomplete counts are rejected. The output keeps group-level schedules and a flattened fixture list with drawing ID, report ID, article number, group, position and rotation. Totals use the report's per-luminaire power.

Group mapping, manufacturer dimensions, live photometry identity and BEC fixed-lighting load remain unauthenticated. Source hashes bind supplied data, not its authenticity. Fixtures that share coincident reported positions are conservatively rejected; the tool does not infer which product occupies the position.

## Native synthetic validation

For the independently verified five-fixture mixed case, the public CLI linked:

| Drawing ID | Native report number | Report article |
| --- | --- | --- |
| L001 | 3 | 910505102817 |
| L002 | 4 | 910505102817 |
| L003 | 1 | 910505102817 |
| L004 | 2 | 910505102817 |
| L005 | 5 | 910505102802 |

Quantity is five and reported fixture power is 4 × 26 + 1 × 32 = 136 W. This demonstrates that drawing order is not assumed to be report order. The explicit identity transform was checked against all five active-storey UI coordinates. Local request/result: `local/mixed-products-native-v1/mixed-schedule-request.json`, `mixed-schedule.json`, `mixed-schedule-cli.json`. Physical dimensions remain synthetic assumptions. No assignment design or submission artifact was produced.

The full test suite has 498 passing tests, including negative mixed-group/ID/position/evidence cases and MCP discovery. Mixed-product CAD rendering and a native round-trip checkpoint are documented in [mixed-product CAD](mixed-product-cad.md).
