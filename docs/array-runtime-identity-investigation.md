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
