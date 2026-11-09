# Bounded native candidate runs

## Generate explicit offset candidates

`layout-candidates-generate --request request.json` / MCP
`generate_offset_candidates` accepts a baseline `spec`, `x_offsets_m`,
`y_offsets_m`, and optional `max_candidates` (default 20). Each axis has 1–20
unique finite offsets; the domain has at most 400 combinations. It reuses
`plan_grid` for full-envelope/exclusion checking and only retains the baseline
fixture count. Baselines must contain 1–2000 zero-rotation fixtures.

It preserves caller order (X outer, Y inner), deduplicates physical XYZ grids to
1e-9 m arithmetic precision, and records count exclusions, duplicate grids and
budget exclusions. Returned `candidates` can be passed directly to the native
runner. A truncated candidate budget is explicit, not a complete or optimal
search. Products, fixture counts, room geometry and criteria are not generated.

The public CLI was exercised on the six-fixture synthetic specification with
X offsets [0, 0.1, 2] and Y offsets [0, 0.1]: four distinct candidates remained;
the two one-spacing shifts were correctly identified as duplicates. This is
geometric generation evidence only. The existing native two-candidate test used
explicit grids; a new generated-domain native search is still pending.

`layout-offset-search --request request.json` / MCP `run_offset_search` joins
generation and native execution without duplicating either implementation.
Supply `expected_project`, `group_id`, baseline `spec`, both offset axes, `checks`,
`objective`, `policy`, a new `evidence_directory` and optional `max_candidates`.
It writes `generation.json` before the native call, then uses a `native/` child
directory for candidate evidence. Successful completion writes `result.json`
with the generation-file hash and runner result. Failures retain the generation
plan and whatever native journal exists, without retry. Generation and iteration
budgets remain distinct and may explore fewer candidates than the supplied domain.
The joined interface is covered by transport/order/failure tests; its own native
generated-domain acceptance is pending.

CLI: `layout-candidates-run --request request.json`. MCP: `run_layout_candidates`.
The request has `expected_project`, `group_id`, `candidates`, `checks`, `objective`,
`policy`, and a new `evidence_directory`. Use a synthetic test project already
open in DIALux. This interface is implemented and unit-tested; multi-iteration
native acceptance is pending. It is not an accepted autonomous lighting designer.

`candidates` contains 1–20 complete grid specifications. Only `grid` may differ;
room, product assumptions, fixture count and all other inputs remain fixed.
Native movement currently requires zero fixture rotation. Candidate generation,
fixture-count/product changes and semantic room validation are not supplied by
this runner. Geometry assumptions must already describe the native test project.

`checks` uses the existing calculation-checkpoint format. `objective` contains
exact `summary_id`, `metric`, `unit`, `calculation_surface` and `direction`
(`minimize` or `maximize`). Its summary must also have a scoped check. The
measurement is read from the freshly exported report and its hash must agree with
the calculation checkpoint; missing or ambiguous evidence stops the run.

`policy` contains:

- `max_iterations`: integer 1–20; never exceeds the supplied candidate count.
- `no_improvement_limit`: integer 1–20 consecutive candidates.
- `minimum_improvement`: finite nonnegative threshold in the objective's units;
  improvement must strictly exceed it to reset the stopping counter. Smaller
  cumulative improvements are compared to the last value that reset this counter.
  Best-candidate ranking still records every strictly better measured value,
  independently of this stopping threshold. This is not statistical significance.
- `stop_on_pass`: boolean; stop when all selected checks pass if true.

Each iteration saves a new `candidate-NNN.evo`, applies the explicit grid with
native readback, recalculates, exports scoped evidence and saves the calculated
copy. No illuminance formula substitutes for DIALux. The original file hash is
checked between candidates. Earlier candidates are retained; no winner is
automatically reopened or installed. The active project is the last attempted
copy. `best_candidate` ranks the objective among measured candidates, while
`best_feasible_candidate` includes only candidates passing all selected checks.
Neither is a whole-project approval.

Stops distinguish list exhaustion, iteration budget, no improvement, selected
conditions met and incomplete evidence. Errors retain pending stages and stop
without retry or rollback. Desktop locks protect individual native operations,
not the entire multi-command run; external edits are not excluded. Do not run
another desktop workflow concurrently. A completed runner means its stopping
policy executed, not that a feasible design was found.

Tests cover budget, minimization, passing/incomplete stops, no-improvement,
source preservation, unsupported changes and missing objective evidence. Full
suite: 354 passed. Real multi-candidate evidence remains required before native
acceptance, once the separate 168-fixture desktop task releases its worker.

The next native test request is prepared in ignored
`local/candidate-native-request-v1.json`: two explicit six-fixture offsets in the
existing synthetic obstacle-room copy, unchanged product and geometry, maximizing
reported WP1 uniformity with a two-iteration budget. The check requires only
positive mean illuminance and explicitly labels itself an orchestration smoke
test, not an engineering design standard. Both grids and the existing report
summary identity were checked offline. Native execution has not started; its
future report values must be obtained from new calculations.

Failure evidence distinguishes pending copy, layout, calculation and report
comparison. Exceptions set `active_project` to null and retain
`last_expected_project`; the UI may have changed even when an operation did not
return successfully. `native_outcome_verified` remains false on failure. Tests
inject each failure stage, replaced report hashes and external source changes,
and verify no later candidate starts. These are failure-path tests, not evidence
of native interruption recovery or automatic resume.

## First native run

`local/candidate-native-v1` completed candidate 0: six-fixture geometry verified,
real calculation/report/save completed, reported average 496 lx and Uo 0.060.
Report SHA256: `ccc94e479819e792ffdb0e875c750405548f63f7fff43e003974f3b9b02c202a`.
The positive-illuminance smoke criterion passed; this is not design acceptance.
Candidate 1 stopped before copying because preparation observed an unknown
secondary window. The old error did not retain window details, and a fresh status
call found no dialog. Its identity/cause therefore remains unknown.

Preparation errors now retain observed dialog details. After verifying the active
project and absence of dialogs, a separate v2 run was started from the saved
candidate-000 copy with new evidence paths; the failed v1 remains preserved.
This is a diagnosed manual retry, not automatic resume or a passed two-round gate.

Run v2 completed its first candidate and captured the repeated transition failure:
the secondary window was the native save-success Popup, with the exact current
project path plus Show in the Explorer / Delete buttons. No button was clicked.
Preparation now waits at most eight seconds for that narrowly matched current-
project notification to disappear, rechecks the project title, and still rejects
other or additional dialogs. A persistent notification remains a failure. Run v3
has started with new copies/evidence to test the repaired transition end to end.

## Completed two-candidate native orchestration

Run v3 exited successfully through the public CLI. Candidate 0 required no
coordinate writes but passed both group inspections; candidate 1 moved all six
fixtures through atomic UIA value replacement and passed final group inspection.
Both then completed real calculation, PDF export, scoped assessment and native
save. The runner stopped with `candidate_list_exhausted` and ranked candidate 1
highest by the explicitly requested Uo objective. Neither its smoke threshold nor
this ranking establishes a satisfactory lighting design.

| Candidate | Mean lx | Uo | W/m2 | Saved native SHA256 | Fresh PDF SHA256 |
| --- | --- | --- | --- | --- | --- |
| 0 | 496 | 0.060 | 6.5 | `41f3a7cd0cb45cfe9c44de3bd065daa8215b8fdf68ddffde6d148f741d43a072` | `ed0d8ef58fbaa742279a374d630f06aa0920315f4198ad35227effd0e30c3a0f` |
| 1 | 493 | 0.062 | 6.5 | `a3e2aca96017b04147a8a71574c795b6fdd412a73e851451045cc83fcb7f7918` | `2c1dc06ac35d9892eefdb208220882c7fb2d8e81ecaf31b89f840d0e04ddf2d4` |

`local/candidate-native-v3/independent-audit.json` independently rereads both
reports, matches each complete coordinate table against its native UI snapshot,
checks saved-file/PDF hashes and unchanged source, and recomputes the ranking.
The coordinate page uses its explicit room-only header; the summary uses its
separate room/light-scene identity. A native reopen/export check of both saved
copies is in progress; no reopening claim follows merely from matching hashes.
Automatic candidate generation, different products/counts, comprehensive project
criteria and large interrupted recovery remain outside this accepted small case.

Both saved candidates have now been independently reopened and exported again.
`local/candidate-native-v3/reopen-check/journal.json` confirms identical metrics,
complete coordinate tables and reported products for both, with unchanged
original native files. Reopened PDF hashes: candidate 0
`272f1ed73f08b731f650e44395a8a5c4b70a363c37193461668b886caef217c6`, candidate 1
`477eb869d32a6fcd6d604030f77aebeceb0e89149962b3dadeeeddaafb3a9fc9`.
Documentation-session changes were saved to separate session copies before
closing. This completes persistence evidence for the two-candidate synthetic case.

## Replay inputs and target identity

New offset-search runs write `request.json` before invoking native operations,
including the source project, target group, base geometry, explicit offset domain,
checks, objective and both budgets. The result hashes this request as well as
`generation.json`. A failed native run retains these inputs and its available
journals. Candidate journals now also record `group_id` directly. This supports
inspection and reproduction on a new evidence directory; it does not authorize
blind replay after partial mutation, supply the original native file, or make
session-local fixture runtime IDs reusable. Existing running processes do not
acquire these changes retroactively.

Search results additionally map every completed native iteration back to its
explicit X/Y offset, objective value and scoped assessment status.
`all_generated_candidates_simulated` means every selected candidate completed;
`all_distinct_same_count_offsets_simulated` additionally requires that the
geometric candidate budget excluded none of the distinct same-count layouts.
Neither flag asserts a global optimum, successful criteria, complete project
coverage or evaluation of count-changing layouts. Early stopping and the native
iteration budget can leave generated candidates unsimulated.

## Generated-domain native run: partial failure retained

`local/offset-search-native-v1` selected four distinct six-fixture offset grids
and excluded two periodic duplicates. Candidates 0 and 1 completed actual
calculations (both reported Uo 0.060). Candidate 2 failed during placement with
`Expected one PositionVectorControl_X, found 0`; candidate 3 never ran. The full
four-candidate search is **not accepted** and no global ranking follows.

The worker ended; fresh status showed the expected candidate project and no
secondary dialogs. The current native state was saved separately to
`local/offset-search-interrupted-v1.evo`, SHA256
`ccb10d676e9e1d83d5638bff99535ab7772328823d6f26edeb33996e1db5d2ba`.
A fresh complete six-fixture inspection found five fixtures at their target
positions and the sixth at its prior position. The movement journal recorded
four committed steps and the fifth pending: pending intent does not prove no
mutation occurred. The observed file hash is
`1948548b2057399d98ef778809ff8bbb3d8746ba23fe93261d2b647e75fd65aa`.

Fixture editing now rechecks the selected runtime identity before each axis
write. Missing-field errors identify initial readback, before-write,
after-reminder or final-readback stage and list axes whose commits were observed.
These changes improve guards and diagnosis; the cause of the disappearing control
is not yet established, and no automatic retry was added. Tests include selection
loss without a dialog and a field disappearing after both coordinate commits.
100 desktop/placement tests passed. A separate recovery copy is under native
verification; it does not overwrite or turn the failed search into a successful run.

The recovery worker also terminated, this time on final coordinate mismatch.
It skipped five already-matching fixtures and attempted only the sixth. A fresh,
read-only UIA snapshot showed XYZ = (5.200, 3.100, 1) m, whereas the requested
position was (5.2, 3.1, 3.035) m. This is evidence of an unexpected displayed Z,
not proof of its cause or of a successful recovery. No calculation was started.
The state was saved separately as `local/offset-search-recovery-interrupted-v1.evo`,
SHA256 `eabc60283044633b5cddf6114733a274ee62953f090975f8fdc7337342037a60`.
`local/recovery-failure-readback-v1.json` preserves the fresh fields and status.
Final mismatch errors now include expected/observed coordinates and completed
axes. Investigating numeric commit/focus behavior remains necessary; neither
failure is being relabelled as a transient refresh or an external-user action.
