# Current agent acceptance and remaining gates

Updated 2026-11-09. **Agent development only**: no BSE3125 design/submission work is authorized until a separate user instruction. This map supersedes broad readings of the earlier assignment-oriented goal and links the evidence rather than treating passing tests as complete product acceptance.

| Capability requirement | Evidence inspected | Current conclusion / remaining gate |
| --- | --- | --- |
| Independent CLI/MCP desktop execution | `acceptance-2026-11-09.md`, `standalone-desktop.md`, `src/server.py`, `src/windows_worker.py` | Native import, real ULD, arrangement, calculation, save, PDF export and reopen observed through independent workers. No private mouse; interactive Windows session required. |
| Preserved source DWG survey and geometry | `agent-development-scope.md`, `cad-boundary-extraction.md`, `concave-room-validation.md` | Native conversion, unit metadata, entity inventory and hash-bound explicit boundary extraction verified. Original assignment geometry is not adopted as a design boundary. General automatic CAD semantic interpretation is not established. |
| Nonrectangular/multiroom/obstacle geometry | `multiroom-import.md`, `concave-room-validation.md`, `obstacle-exchange.md` | Concave native room and adjacent synthetic rooms imported; ground-supported boxes read back and retained after reopen. General meshes, rotated/elevated boxes, apertures and arbitrary room topology remain unsupported/unverified. |
| Controllable positions and grid alignment | `grid-application.md`, `individual-fixture-verification.md` | Six-fixture shift, all-coordinate readback, recalculation, persistence and observed CAD chain verified. 168-fixture movement is actively under test; it is not passed yet. Native grid rotation and fixture creation/deletion workflows are incomplete. |
| Large native inventory | `large-project-validation.md`, `group-inspection-checkpoints.md` | All 168 fixtures read across 42 hashed pages; coordinates/rotation matched plan, XYZ matched report, saved project report preserved after reopen. One group, not whole-project completeness. |
| Independent CAD printing | `fixed-scale-plots.md`, `large-native-plots.md`, `observed-layout-cad.md` | Native DWG save/reopen, IDs/geometry and PDF vector scales checked; A3 1:50 and A1 1:100 synthetic sheets rendered and inspected. Dimension system, engineering titleblock, full schedule/legend composition and layout-collision gates remain unfinished. |
| Shared positions, IDs and product schedule evidence | `luminaire-schedule.md`, `src/schedule.py` | Single-product report section spatially linked to observed CAD IDs with explicit transform and hashes. Native example proves different row orders handled. Formatted schedule table and mixed-product aggregation remain unfinished; product/dimension authentication remains explicit. |
| Scoped simulation results | `scoped-report-reading.md`, `workplane-extrema.md`, `report-layout-reading.md` | Exact room/scene/surface summaries and direct minimum/maximum on supported English tables; unavailable values retained. General glare/task-area/vertical-surface extraction and other languages remain incomplete. |
| Repeatable design iterations and stop conditions | `calculation-checkpoints.md`, `src/workflow.py` | One durable calculation/export/check/save checkpoint with explicit met/not-met/incomplete decisions. Autonomous bounded candidate generation, objective comparison and stopping-policy acceptance are not implemented. |
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

The first large movement attempt (`local/large-grid-run-v1`) terminated during
initial inspection after 88 recorded fixtures, before any movement. Native status
identified an English 10-minute unsaved-project reminder. The worker previously
recognized only the observed 5-minute form. Both exact forms are now supported;
unknown prompts still fail closed. Mid-page reminder handling rechecks project,
selection and displayed values before accepting evidence. Unit suite: 334 passed.
The independent CLI retry (`local/large-grid-run-v2`) has started; this is pending
native acceptance, not a successful large movement claim.

1. Finish the currently running 168-fixture native movement gate from its actual process result; inspect before/after pages and every committed step, then independently calculate/export/save/reopen if geometry passes. Preserve any failure and do not restart from a stale progress file.
2. Complete reusable engineering drawing composition: explicit dimensions, titleblock, legends and formatted evidence-linked schedule, tested on synthetic translated/concave/large cases with native plotting.
3. Add bounded simulation iteration orchestration with explicit objectives/criteria, candidate budgets, no-improvement/failure stops and preserved source/evidence; verify multiple actual native iterations. Do not substitute a guessed illumination formula for DIALux simulation.
4. Exercise mixed products/room scope, actual interruption recovery and independent artifact consistency checks. Retain unsupported cases as explicit refusal until evidence exists.
5. Review the complete agent acceptance matrix again. Assignment production remains outside this goal's current authorized scope.
