# Native notification transitions and query measurements

Observed 2026-11-09 on DIALux evo 14.1. These are synthetic agent tests; no
assignment design was produced.

## Interrupted generated search

`local/offset-search-native-v3/native/journal.json` ended at candidate 3's
`pending_copy`, before a fourth copy was accepted. Candidates 0, 1 and 2 completed
layout readback and real calculation, with WP1 Uo 0.060, 0.060 and 0.066.
`partial-independent-audit.json` independently matched all six report coordinates
against each completed UI observation and checked that the source was unchanged.
This is partial evidence, not acceptance of the four-candidate search.

The error identified one untitled, empty Popup. A subsequent independent status
read found no dialog and the saved candidate-002 project. That candidate's SHA256
was `c10d3966bd1557b02beea2c9b0110db5b6d8007a95d27139edd0a86bf8a9ebbb`;
its report SHA256 was `0870347db152024107a298301b3aa649fa1dd466603c529fbc720d0ac25aa73d`.
There was no automatic retry or completion claim.

## Observed save-notification transition

An instrumented standalone worker saved a separate copy and recorded native
snapshots in `local/save-popup-trace-v1.json`. During Save As it observed a Popup
with nine descendants at 15.44 seconds, an empty Popup at 19.22 seconds, and no
dialog at 21.98 seconds. These are snapshot completion times, not precise native
event times; snapshots are sequential and not atomic. The source remained intact.

The previous preparation sequence waited for an initially empty Popup, then for
a recognized current-project save notification. The latter wait ended immediately
if the notification became empty, leaving the following dialog guard to reject
that transitional state. The trace establishes that the state sequence can occur;
it does not prove this was the sole cause of the earlier search failures.

The recognized-notification wait now includes its empty transition within the
same eight-second polling deadline. A transition never resets that deadline.
Initially empty windows are not promoted to recognized notifications; they retain
their separate three-second observation rule. Unknown content, another project's
notification, additional windows or a persistent popup still prevent the action.
No buttons are clicked. Project identity is rechecked after observation.
UIA calls themselves can outlast the polling deadline; the worker also has its
outer operation timeout.

Tests cover disappearance, persistent emptiness, named unknown content, additional
windows and another project's notification. The full suite passed 414 tests.
The subsequent four-candidate native run and reopening passed; see
[scoped generated-search acceptance](generated-search-acceptance.md).

A subsequent standalone native Save As, save and preparation sequence completed
without errors (`local/save-popup-trace-v2.json`), preserving its source. This
sequence sampled the populated notification followed by no dialog; it did not
sample the empty intermediate frame, so it is not direct native execution
evidence for that newly tested branch.

## Query measurements

`local/native-control-query-benchmark-v1.json` compared the current enumeration
with native `FindAll` conditions on control type plus AutomationId, for five keys
and three repetitions. Visible runtime-ID sets matched in this one native state.
Total measured query time was 5.107 versus 3.757 seconds, with individual variance;
the coordinate Edit field was absent, so this is not a placement-panel benchmark.
Production lookup was not replaced on this evidence.

The implementation instead removes three repeated button-tree enumerations in
each status snapshot by collecting that list once. Duplicate/disabled-control
checks are retained. `local/snapshot-batch-benchmark-v1.json` compares the preserved
old function and new function on the same live project: all three complete status
dictionaries matched. Old/new durations were 2.382/2.017, 2.348/1.841 and
2.205/1.215 seconds. This is a small read-only measurement, not an end-to-end
speedup guarantee or an atomic-state guarantee.

Microsoft documents that AutomationId is not globally unique, so future native
query filtering must retain scope and runtime-identity ambiguity checks:
[AutomationId guidance](https://learn.microsoft.com/en-us/dotnet/framework/ui-automation/use-the-automationid-property).
Native [FindAll](https://learn.microsoft.com/en-us/windows/win32/api/uiautomationclient/nf-uiautomationclient-iuiautomationelement-findall)
can return all elements matching a condition; selecting the first result would
not preserve the existing uniqueness guard.
