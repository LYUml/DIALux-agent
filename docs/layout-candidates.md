# Bounded native candidate runs

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
