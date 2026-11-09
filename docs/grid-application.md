# Journalled native grid application

`layout-apply-grid --spec <grid.json> --expected-project <copy.evo> --group-id <exact-group-id> --evidence-directory <new-directory>` and MCP `apply_grid_layout` connect the existing planner, fixture inspector, guarded movement and geometric comparison.

The command validates target footprints against the supplied room/exclusions, then inspects the existing realized group. Counts must agree, runtime identities must be unique and native rotations must be zero. Existing fixtures are assigned to target positions in Y/X/Z spatial order. This is an explicit geometric assignment, not a product-identity match or lighting optimization. It creates and deletes no fixtures.

Each movement's intent is recorded before invoking the independent native backend. Successful calls are marked committed. An exception leaves the overall run failed with previous committed steps and the pending step intact, and stops further operations. There is no automatic retry, rollback or resume. A new output directory is required, preserving previous evidence. An atomic file replacement updates only this run's journal.

After all moves, a fresh native group inspection is matched one-to-one against the plan. The journal reaches `verified` only after that comparison passes. This means the supplied realized group's geometry matches; it does not imply whole-project completeness, correct photometry, native persistence or lighting performance. Save/reopen and calculation remain separate steps. Cached results are cleared by movement operations.

Current limits: nonempty zero-rotation grids, equal existing fixture count, realized/visible group nodes and bounded per-operation desktop timeouts. Collapsed ancestor branches must be expanded through `desktop-project-tree` first. Do not run concurrent desktop commands while an application is active. The synthetic example is `examples/synthetic-apply-grid.json`; no assignment layout is included.

Tests cover write-before-mutation journal ordering, failed second movement with no third call or rollback, refusing an existing evidence directory, and count mismatch before mutation. These tests are distinct from native end-to-end acceptance.

Native acceptance on 2026-11-09: public CLI applied the four-point example to a new `bulk-probe-v1.evo` copy. The initial positions included the individually displaced lamp from the prior test. All four movement steps committed, and independent final readback matched the target set (1.5,1,3.035), (4.5,1,3.035), (1.5,3,3.035), (4.5,3,3.035). Journal `local/bulk-application-v1/journal.json` SHA256: `b5c5cf728467813eab741625f73809e6b46c6a51c3605257ef7829e5afb9bf3d`. Fresh public calculation displayed 364 lx average and 0.48 uniformity. This is a synthetic tool test, not a compliance result. Save/reopen of the complete bulk workflow remains a separate acceptance gate.

150 automated tests passed, including rejection when all edit calls succeed but final native geometry differs. Spatial assignment keys round only sub-nanometre arithmetic noise to prevent nominally equal rows from being reordered; actual movement targets are not rounded.
