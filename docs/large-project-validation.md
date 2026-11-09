# Large-project scalability and virtualized fixture reading

Synthetic tool test only. `examples/synthetic-large-room.json` is a 30 × 34 m rectangle (1020 m²), unrelated to traced assignment geometry. The same tested manufacturer ULD was imported. Native automatic placement created a 14 × 12 arrangement with 168 luminaires.

## Native calculation evidence

Public STF import, native save-as, luminaire import, placement, calculation and PDF export completed. `local/large-report-v1.pdf` has 35 pages, 2,491,395 bytes and SHA256 `d6983b5309b8415bca24945070de73c4899e63f63503f99d21c363348eba7f42`. Summary pages 14–15 state 1020 m², 510 lx average perpendicular illuminance, Uo 0.43 and 4.28 W/m². Native luminaire-list text records 168 units. These are outputs of a synthetic software test, not adopted design criteria or a compliance conclusion.

Saved `local/large-native-v1.evo`: 4,657,199 bytes, SHA256 `68be0e4bee9cad65132b3ff76841414496c2bdf7ecf133940d538f6ef22218b9`. STF SHA256: `9c82a0f6790147cddd6d35131f8b69cbdc436aece376e74a35a0a0c178fa0b2b`. A separate reopen gate remains outstanding.

## Virtualization defect and implementation

The old `descendants(ListItem)` approach observed only 19 realized fixture nodes (18 visible), later 18 after changing mode, despite the native 168 count. This is WPF UI virtualization, not evidence of missing luminaires. `--expected-count 168` initially rejected this subset before fixture reads. The optional count guard remains available in CLI/MCP.

The adapter now reuses Windows UIA ItemContainer/VirtualizedItem patterns exposed by the existing pywinauto dependency. ItemContainer enumeration returned 182 total tree entries, including all 168 fixture children with unique runtime identities. Each requested row is realized/scrolled into view before selection and readback. Group nodes are likewise materialized so scrolling to the bottom does not make the next request unable to expand/find the group. Enumeration rejects repeated runtime IDs and more than 10,000 tree entries; filtered fixture inventories are refused.

Public readback successfully reached index 167: (28.929, 32.583, 3.035) m. Returning to index 0 read (1.071, 1.417, 3.035) m with the same inventory token. This proves first/last/back navigation and token continuity, not all intermediate fixture coordinates. `container_node_count` is the current inventory size; the legacy `realized_node_count` field is retained as a compatibility alias. `complete_inventory` remains false because the whole project and collapsed content are not inventoried.

Related coordinate/name fields now use one UIA Edit traversal rather than seven repeated searches, retaining uniqueness checks. A real one-fixture comparison returned identical evidence before/after. Observed times were 12.594 s and 10.984 s, but UI starting states differed; these are not a controlled performance benchmark.

The first full scan, `local/large-full-scan-v1`, terminated after 20 records with `Tree inventory identity/order changed`. Its saved progress file is stale, not evidence of a live process. Releasing UIA references between fresh worker processes is the suspected cause; the identity guard correctly refused to combine changed inventories. Earlier first/last/back samples did not expose this failure.

The new `group-inspection-checkpoint` CLI / `inspect_group_checkpoint` MCP runs all pages inside one standalone Windows worker and retains the native COM element references throughout. It validates retained runtime IDs and automation IDs before each continuation, then verifies materialized identity and selection before reading coordinates. Native regression is running in `local/large-full-scan-v2`; full 168-record acceptance remains pending until the completed observation is independently compared with the synthetic grid. The implementation checkpoint passed 264 tests, including persistence, failure evidence and identity-change refusal.

253 tests passed at this checkpoint, including single-traversal uniqueness, expected-count refusal, complete item-container enumeration and repetition rejection. Whole-project inventory, obstacles, arbitrary project sizes and large-project edit/recovery acceptance are not established by this test.

## Completed persistent scan, 2026-11-09

The subsequent `local/large-full-scan-v2` run completed normally through the public `group-inspection-checkpoint` CLI. It collected all 168 fixtures in 42 hashed pages in 1061.719 seconds (about 17.7 minutes). This supersedes the pending full-scan status above. Its observation file SHA256 is `6d2828bf5cb64d9cf88ad48dc144675ef328611548f8870bb75200e7b261932d`; the saved source project hash remained unchanged.

The independent public `group-inspection-verify` command rechecked every page hash, count, identity, continuation and exact combined assembly, then matched all 168 XYZ positions and rotations to the explicit 14-by-12 synthetic grid within the established 1 mm / 0.05 degree tolerances. All 168 UI XYZ triples also matched the independently parsed native PDF coordinate table with zero displayed-coordinate difference. Report order differs from UI order, so matching used unique spatial correspondence, not row order. Report coordinates do not provide rotation; that gate is supplied by the UI observations.

Evidence is retained in `local/large-full-scan-v2/verification.json`, `cli-verification.json`, `report-crosscheck.json`, `journal.json` and the 42 page files. The failed v1 directory is preserved. Retaining the native COM references across pages resolved the observed fresh-process identity churn for this full test. This is one complete large synthetic group, not proof of atomic snapshots, hidden project content, every DIALux version or arbitrary-size projects. Large-group editing/recovery and separate saved-project reopen gates remain outstanding.

## Saved large-project reopen gate

Public CLI close/open/export operations reopened `local/large-native-v1.evo` and generated `local/large-report-reopened-v1.pdf` (35 pages, SHA256 `4465036d5e7aa3cf5a9d8aba9838bfea8e6bb17e352e2ca8b020cf4075ac6ee7`). Parsed room identity, area, heights, all three summary measurements, all 168 coordinate-table entries and product metadata matched the prior report. The original native project remained SHA256 `68be0e4bee9cad65132b3ff76841414496c2bdf7ecf133940d538f6ef22218b9`. Export-related session changes were saved separately as `local/large-reopen-session-v1.evo`; the original was not overwritten. This verifies preserved report content after native reopen, not a second 168-item live UI scan or fresh recalculation.
