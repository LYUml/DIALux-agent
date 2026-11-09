# Large-array runtime identity investigation

The guarded 168-fixture execution under `local/guarded-large-array-v1` is still
collecting its after-inspection. It has not passed the executor's acceptance gate.
Both requested centre fields were committed and read back; all 168 before records
and the rigid transform preflight were independently verified.

At the first 40 after records, records 24 through 39 had runtime IDs absent from
the complete before inventory. Their positions each matched a translated before
position within the display tolerance, and the matched names agreed. This is
geometry correspondence, not proof that the same native model objects persisted.
The current executor requires identical runtime-ID/name maps and must reject such
evidence after the full scan. It must not be labelled successful retrospectively
by weakening the existing acceptance rule.

Microsoft documents GetRuntimeId as an opaque UI element identifier, unique among
current desktop UI elements, with reuse possible over time. It is not a durable
DIALux model-object identifier:
https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationelement-getruntimeid

The implementation retains native element references during each complete group
scan, but creates a fresh inspection context for the next scan. Releasing the
first scan's references or recreating UI providers is a hypothesis for the ID
changes, not an established cause. A future isolated experiment can retain the
first scan's references while independently enumerating the second scan. That
experiment must still verify every fixture, reject changed identities and retain
failure evidence; it cannot assume reference retention solves the problem.

Current actions: finish the read-only after scan without competing desktop
operations; preserve all pages and the resulting executor status; inspect/save
the interrupted project's state separately if execution fails; investigate
identity continuity on a fresh synthetic copy before repeating large acceptance.
No assignment production or successful large guarded execution is claimed.

## Completed failed execution

The native driver exited with code 1 after all 168 after records were collected.
An independent `verify_group_checkpoint` call rechecked all 42 after pages and
matched every fixture against the requested target grid. The executor rejected
the cross-scan identity map: 27 runtime IDs persisted, 141 were absent and 141
new IDs appeared. No calculation checkpoint ran. The final executor error was
`Fixture identities or names changed during transform`.

All 32 source files were archived while still matching the start-of-run hashes.
Only CLI/MCP entrypoints changed afterward; native execution dependencies remained
unchanged. The independent failure audit retained separate geometry success and
identity rejection claims at `local/guarded-large-array-v1/independent-failure-audit.json`.

After the driver was confirmed terminal, the current session was saved as a new
diagnostic copy and closed. Its SHA-256 is
`c57fa43c752149a177e49769f7db4d527964535a778044b048ffd13f78f23275`.
The original working-copy and baseline-source hashes remained unchanged. This
preserves the failed run; it does not turn it into a successful execution.

A separate read-only experiment is now running under
`local/readonly-identity-probe-v1`. It compares two fresh full native inventories
while sampling four fixture coordinates, first releasing and then retaining scan
contexts. The native worker's project guards and desktop mutex remain in force.
Sampling is for diagnosis only and does not replace full geometry acceptance.

The read-only experiment completed in both modes: each compared 168-node
inventories with zero lost/new IDs; four sampled fixtures retained equal geometry
and names. The original source stayed unchanged, and a separate UI-session copy
was saved and closed. Released-mode evidence SHA-256:
`b8157ff9ad375680aa281eb083e1c33072ca58846de902abe0bb5f6f5d6287d0`;
retained-mode evidence:
`125fa9becf0751f02aa7527bdaafd190b9090684bb93c90b3157c5c70beaa8bd`.
This small read-only sequence did not reproduce the anomaly; it does not explain
the earlier full mutation sequence or prove a retention fix.

The next isolated experiment, `local/cache-clear-identity-probe-v1`, runs on a new
native copy. Between inventories it invokes the guarded field adapter with targets
equal to the current values. It requires exactly a cached-results-clear event and
zero submitted motion fields. This separates result-cache clearing from coordinate
writes; the experiment is still running and no causal conclusion is claimed.

## Cache-clear isolation result

That experiment completed with exactly one `pending_results_clear` event and an
empty `completed_fields` list. Array counts, centre, rotation and name read back
unchanged. Nevertheless, the two 168-node inventories differed by 150 lost and
150 new runtime IDs; the four sampled fixtures retained matching geometry/names.
Evidence SHA-256:
`29cb857ee7ba65e8867f008a28e17c9346b078e9327db39aa2685a765ef6aca3`.
The source stayed unchanged and the cleared-cache UI session was saved separately
and closed. Thus cache clearing alone reproduced runtime-ID discontinuity in this
bounded experiment. This does not prove that it is the only possible cause.

An isolated follow-up now uses a copy of that already-cleared session and submits
only the guarded X/Y centre increments, requiring no results-clear event. It is
under `local/motion-only-identity-probe-v1`. Its outcome will inform whether a
post-cache-clear baseline can preserve identity checks across subsequent movement;
the full executor has not yet been changed or accepted on a large array.
