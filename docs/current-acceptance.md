# Current agent acceptance and remaining gates

Updated 2026-11-09. **Agent development only**: no BSE3125 design/submission work is authorized until a separate user instruction. This map supersedes broad readings of the earlier assignment-oriented goal and links the evidence rather than treating passing tests as complete product acceptance.

| Capability requirement | Evidence inspected | Current conclusion / remaining gate |
| --- | --- | --- |
| Independent CLI/MCP desktop execution | `acceptance-2026-11-09.md`, `standalone-desktop.md`, `src/server.py`, `src/windows_worker.py` | Native import, real ULD, arrangement, calculation, save, PDF export and reopen observed through independent workers. No private mouse; interactive Windows session required. |
| Preserved source DWG survey and geometry | `agent-development-scope.md`, `cad-boundary-extraction.md`, `concave-room-validation.md` | Native conversion, unit metadata, entity inventory and hash-bound explicit boundary extraction verified. Original assignment geometry is not adopted as a design boundary. General automatic CAD semantic interpretation is not established. |
| Nonrectangular/multiroom/obstacle geometry | `multiroom-import.md`, `concave-room-validation.md`, `obstacle-exchange.md` | Concave native room and adjacent synthetic rooms imported; ground-supported boxes read back and retained after reopen. General meshes, rotated/elevated boxes, apertures and arbitrary room topology remain unsupported/unverified. |
| Controllable positions and grid alignment | `grid-application.md`, `individual-fixture-verification.md` | Six-fixture shift, all-coordinate readback, recalculation, persistence and observed CAD chain verified. 168-fixture movement is actively under test; it is not passed yet. Native grid rotation and fixture creation/deletion workflows are incomplete. |
| Large native inventory | `large-project-validation.md`, `group-inspection-checkpoints.md` | All 168 fixtures read across 42 hashed pages; coordinates/rotation matched plan, XYZ matched report, saved project report preserved after reopen. One group, not whole-project completeness. |
| Independent CAD printing | `fixed-scale-plots.md`, `large-native-plots.md`, `observed-layout-cad.md`, `cad-dimensions.md` | Native DWG save/reopen, fixture/label geometry, explicit linear dimensions and PDF vector scales checked; A3 1:50 and A1 1:100 sheets inspected. Bounded fixture-label collision avoidance verified on concave, rotated and 168-fixture synthetic CAD cases. Engineering titleblock, full sheet composition and general annotation collision handling remain unfinished. |
| Shared positions, IDs and product schedule evidence | `luminaire-schedule.md`, `src/schedule.py` | Single-product report section spatially linked to observed CAD IDs with explicit transform and hashes. Native example proves different row orders handled. Single-product aggregate CAD table passed independent native reopen and PDF inspection. Mixed-product aggregation remains unfinished; product/dimension authentication remains explicit. |
| Scoped simulation results | `scoped-report-reading.md`, `workplane-extrema.md`, `report-layout-reading.md` | Exact room/scene/surface summaries and direct minimum/maximum on supported English tables; unavailable values retained. General glare/task-area/vertical-surface extraction and other languages remain incomplete. |
| Repeatable design iterations and stop conditions | `calculation-checkpoints.md`, `layout-candidates.md`, `src/iterations.py` | One native calculation checkpoint verified. Bounded explicit candidate orchestration completed two actual six-fixture native iterations, independent report/position/hash/ranking checks and save/reopen comparison. Other stop-policy branches remain unit-tested rather than all exercised natively. Automatic candidate generation and varying fixture-count/product searches remain unimplemented. |
| Replaceable official-source Hong Kong profiles | `modules.md`, `hk-source-register.md`, `hk-office-lpd.md`, `profile-applicability.md` | Region-independent evaluator and scoped sourced BEC office LPD / Labour advisory packs implemented. Not comprehensive legal compliance. Project applicability and international task-standard selection remain explicit; no assignment criterion has been silently adopted. |
| Failure handling / long operations | `grid-application.md`, `src/desktop_lock.py`, `src/inspection.py` | Unknown dialogs, stale identities, duplicate/partial evidence and overlapping cooperating workers rejected; journals retained. No general automatic resume/rollback. Large interrupted-mutation recovery is not yet accepted. |
| Reuse and upstream improvement | `upstream-review.md`, vendored pinned MIT sources | STF geometry, box serialization, reading and shared-wall splitting reused unchanged. Added independent native execution, guarded movements and stronger output evidence. The comparison below is scoped to reviewed pinned sources, not an assertion about every upstream branch or future release. |

## Comparison with reviewed pinned upstream modules

The baseline is MCP_Dialux commit `4489032e67cabe0d409819fad24f091128620a9d`, with MIT license retained. This is not a timed head-to-head benchmark or a claim to dominate every upstream capability.

| Reviewed module | Preserved/reused work | Additional capability with evidence |
| --- | --- | --- |
| `dialux/stf.py`, `leer_stf.py` | Existing room/box serialization, independent STF reading, adjacent-wall vertex splitting | Validated inputs and independent native import/save/reopen/readback gates; no duplicate serializer. |
| `dialux/luminarias.py:reticula` | Upstream bounding-box subdivision and centre clipping remain vendored | Explicit external lattice origin/spacing/rotation and complete fixture-footprint/exclusion tests in the planner; guarded native movement and full observed geometry comparison. Native zero-rotation movement is the verified scope. |
| `dialux/cad/convertir.py` | Upstream ODA-based conversion retained as upstream code | Installed AutoCAD Core Console copy-only conversion, independent native reopen and physical PDF vector-scale verification. |
| `dialux/corregir.py`, `norma.py` | Upstream reading of DIALux-exported DWG result tables and Spanish standard logic retained for research | Separate source-bearing Hong Kong profiles and exact-scope PDF adapters. Upstream already reads minima/maxima from exported CAD: direct PDF extrema are an added input path, not a claim that upstream lacks extrema. |

## Next acceptance order

The bounded explicit candidate runner is now exposed through CLI/MCP; see
`layout-candidates.md`. Unit tests cover its stop/comparison/failure policy.
Two-candidate native execution and reopening now pass on the synthetic obstacle
case. Automatic candidate generation and broad search acceptance remain pending.

The first large movement attempt (`local/large-grid-run-v1`) terminated during
initial inspection after 88 recorded fixtures, before any movement. Native status
identified an English 10-minute unsaved-project reminder. The worker previously
recognized only the observed 5-minute form. Both exact forms are now supported;
unknown prompts still fail closed. Mid-page reminder handling rechecks project,
selection and displayed values before accepting evidence. Unit suite: 334 passed.
The independent CLI retry (`local/large-grid-run-v2`) subsequently failed as described below; neither run establishes successful large movement.

Retry v2 also terminated before movement, after 40 recorded fixtures. Native
status showed the same reminder with 20 elapsed minutes. Recognition now accepts
only a positive integer duration in the otherwise exact reminder text, retaining
the window/control signature and project guard. Retry v3 finished initial
inspection but failed at the third movement. A fresh read found a corrupted X
coordinate; the interrupted native file was preserved and an independent copy
was repaired with guarded atomic UIA replacement. See `grid-application.md`.
Full large mutation remains pending. The two-candidate native test has now
started on the separate six-fixture case. CAD dimensions and bounded
fixture-label collision avoidance have separate native evidence in
`cad-dimensions.md`; drawing composition remains incomplete.

1. Finish the currently running 168-fixture native movement gate from its actual process result; inspect before/after pages and every committed step, then independently calculate/export/save/reopen if geometry passes. Preserve any failure and do not restart from a stale progress file.
2. Complete engineering titleblock and full sheet composition, then verify dimensions, labels and report-linked schedules together on translated/concave/large cases. Existing individual dimension and single-product table gates do not prove arbitrary sheet composition.
3. Run the prepared two-candidate native acceptance through the implemented bounded orchestrator. Verify both actual calculations, preserved candidates, selected metrics and stopping reason, then extend candidate generation/search capabilities. Do not substitute a guessed illumination formula for DIALux simulation.
4. Exercise mixed products/room scope, actual interruption recovery and independent artifact consistency checks. Retain unsupported cases as explicit refusal until evidence exists.
5. Review the complete agent acceptance matrix again. Assignment production remains outside this goal's current authorized scope.
