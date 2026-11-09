# Guarded rigid-array execution

CLI `layout-apply-array --request request.json` and MCP `apply_array_transform` expose an independent Windows worker. The request contains `expected_project`, target grid `spec`, exact `group_id` and a new `evidence_directory`.

The worker holds the existing cross-process desktop lease throughout this operation. It collects every fixture into hashed inspection pages, reads the native array, reuses the rigid-transform preflight to reject count/spacing changes or independently displaced fixtures, and persists the requested transform before mutation. The selected arrangement's runtime identity and complete display vector must match the fresh readback before cached results are cleared.

Each XYZ/rotation edit records pending intent before writing, uses UIA SetValue and a known numeric field's focus to commit, and checks the complete vector, including untouched counts/name/coordinates. The adapter rechecks the selected runtime identity and project. After edits, a new complete inspection must match every target position/angle and preserve all original fixture runtime identities and names. Saved-file hashes must remain unchanged. Existing evidence directories are refused rather than resumed.

Success is explicitly `geometry_verified_unsaved`. The operation does not save, calculate, export, optimize, inspect other groups, prove an atomic snapshot or verify persistence. The caller must separately run a calculation checkpoint and save/reopen verification. It supports only the same-count rigid arrays accepted by `plan_array_transform`, not arbitrary fixture movement or creation/deletion.

Failure retains the outer journal plus inspection pages and any pending field event. A crash or timeout can leave partially changed native geometry. A failed status is never evidence that nothing was changed, and there is no automatic retry or rollback. The lease excludes cooperating workers, not human input or unrelated software.

## Verification status

The full suite passed 539 tests after CLI/MCP integration. Five execution tests cover complete before/after checkpoints, rejected nonrigid input, a failed write, unchanged geometry and changed fixture identities. Fourteen field-commit tests cover intent ordering and unexpected field changes. Three additional adapter tests reject stale runtime IDs/counts and absent runtime evidence before results clearing.

A separate real native test is in progress under `local/guarded-array-native-v1`: it requests a 0.1 m XY translation plus 5-degree rotation of the six-fixture synthetic obstacle room. The original source is preserved and a new copy is used. No native execution or persistence acceptance is claimed until the run and independent checks finish. This API is experimental while that gate is pending.
