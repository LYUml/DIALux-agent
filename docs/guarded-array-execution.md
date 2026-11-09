# Guarded rigid-array execution

CLI `layout-apply-array --request request.json` and MCP `apply_array_transform` expose an independent Windows worker. The request contains `expected_project`, target grid `spec`, exact `group_id` and a new `evidence_directory`.

The worker holds the existing cross-process desktop lease throughout this operation. It collects every fixture into hashed inspection pages, reads the native array, reuses the rigid-transform preflight to reject count/spacing changes or independently displaced fixtures, and persists the requested transform before mutation. The selected arrangement's runtime identity and complete display vector must match the fresh readback before cached results are cleared.

Each XYZ/rotation edit records pending intent before writing, uses UIA SetValue and a known numeric field's focus to commit, and checks the complete vector, including untouched counts/name/coordinates. The adapter rechecks the selected runtime identity and project. After edits, a new complete inspection must match every target position/angle and preserve all original fixture runtime identities and names. Saved-file hashes must remain unchanged. Existing evidence directories are refused rather than resumed.

Success is explicitly `geometry_verified_unsaved`. The operation does not save, calculate, export, optimize, inspect other groups, prove an atomic snapshot or verify persistence. The caller must separately run a calculation checkpoint and save/reopen verification. It supports only the same-count rigid arrays accepted by `plan_array_transform`, not arbitrary fixture movement or creation/deletion.

Failure retains the outer journal plus inspection pages and any pending field event. A crash or timeout can leave partially changed native geometry. A failed status is never evidence that nothing was changed, and there is no automatic retry or rollback. The lease excludes cooperating workers, not human input or unrelated software.

## Verification status

The full suite passed 543 tests after the native-selection fix. Five execution tests cover complete before/after checkpoints, rejected nonrigid input, a failed write, unchanged geometry and changed fixture identities. Fourteen field-commit tests cover intent ordering and unexpected field changes. Three additional adapter tests reject stale runtime IDs/counts and absent runtime evidence before results clearing.

The second native execution passed the six-fixture combined translation/rotation case described below. Broader array sizes, other transformations and failure recovery remain separate acceptance gates. This is bounded native evidence, not general whole-project acceptance.

## Initial native execution failure

The first combined executor run (`local/guarded-array-native-v1`) stopped after clearing stored calculation results, before any `pending_field` event. It attempted to locate `FilterTreeListBox` after switching to the luminaire parameter tab, where that tree is no longer visible. This is a failed native gate, not successful array execution.

The adapter now retains the uniquely selected native item reference obtained by `read_arrangement`, and continues checking its runtime ID and selection state through that reference. It does not switch panels or use a first-match fallback. A regression test simulates the hidden tree and fails if the adapter tries to query it; all 23 targeted array-execution/commit/adapter tests pass. The retained reference does not exclude external user changes, so every write still rechecks identity and the complete field vector.


## Combined native acceptance, 2026-11-09

Revision `cd1be34` ran on a separate copy of the synthetic obstacle room. The independent worker moved the array centre from (3,2,3.035) m to (3.1,2.1,3.035) m and rotated it from 0 to 5 degrees. Its complete six-fixture before/after inspections passed the rigid preflight and target geometry comparison. The three changed fields each retained pending and verified events in order; unchanged Z was skipped. Fixture runtime identities and names were preserved. The executor returned `geometry_verified_unsaved` as specified.

A separate calculation checkpoint saved and recalculated the result. An independent artifact audit rechecked source-code snapshot hashes, request/preflight hashes, complete post-edit inspection pages, runtime IDs, write-event ordering, source preservation and all six report XYZ positions against UI readings. The synthetic WP1 result was average 496 lx, Uo 0.060 and reported LPD 6.5 W/m². These are smoke-test results, not a compliant design claim.

A separate persistence run closed and reopened the saved project, fully inspected all six positions/rotations/names again, and exported another report. Product, report coordinates and all parsed scoped summary measurements matched. The saved native file hash remained unchanged. Documentation-session changes were saved to a separate copy and closed. The original source remained unchanged throughout.

Hashes and bounded claims: [guarded-array-v2.json](evidence/guarded-array-v2.json). Local evidence: `local/guarded-array-native-v2/{execution,calculation,independent-audit.json,reopen-v1}`. The first failed execution remains under v1; subsequent live field inspection matched its original preflight values and its cleared-results session was saved separately before the new run.

This accepts the full independent API chain for one six-fixture regular array, with 0.1 m XY translation and 5-degree rotation. It does not establish arbitrary transformations, large-array execution through this API, preservation of other groups, automatic recovery, manufacturer dimensions, design compliance or assignment readiness.

The executor now also saves the complete native array readback as `arrangement.json` before preflight, with its file SHA-256 in the journal. Together with the hashed full before-inspection and request, this allows an auditor to reconstruct `plan_array_transform` exactly, including its input hashes. A regression test performs that reconstruction. This is additional evidence retention, not a change to geometry or an authentication claim.

## Independent offline replay command

`python -m src.array_audit --evidence-directory <completed-execution-folder>` reads the evidence without desktop access. It replays the geometry preflight from the request, before inspection and raw array snapshot, verifies both full inspection checkpoints, checks project/group/source bindings, and compares every expected pending/verified field event and final field value. Changed fixture identities, missing events, tampered pages and mismatched hashes are rejected. It returns no live-state, persistence, simulation or authenticity claim.

This reader requires the newer `arrangement.json` capture; older execution folders are not silently upgraded. Ten focused tests include independent reconstruction and corruption/identity/commit rejection. General CLI/MCP registration is separate; the module command is available now. The 168-fixture native run under `local/guarded-large-array-v1` is still in progress, so large-array acceptance is not claimed.

Count fields require exact equality during offline replay, matching the live committer. Coordinate display tolerances must not admit fractional count changes. Regression cases for both count fields failed before the correction and pass afterward.
