# Native arrangement editing checkpoint

This page records the initial count-edit checkpoint. Later native evidence covers
[168-fixture regular-array translation](large-array-translation.md) and
[six-fixture 5° rotation](native-array-rotation.md), with full readback,
calculation and reopening. The historical pending statements below do not
supersede those scoped later results.

2026-11-09, synthetic tool test only. `placement-probe-v1.evo` was created with public Save As from the previous synthetic acceptance project. No assignment project was created or edited.

The standalone worker can select an exact expanded native project-tree ListItem through UIA SelectionItem, switch to the arrangement tool and edit the native count fields with committed keyboard input. Public `desktop-edit-arrangement` changed ElementCountX from 3 to 2 while retaining ElementCountY=2. The operation read back both values and rejected unexpected dialogs. Public save succeeded; subsequent public calculation produced displayed average 364 lx and uniformity 0.48. These are test observations, not compliance or a design recommendation.

During development, editing with stored results exposed a confirmation dialog behind a pending field value. Such values are not accepted as success. The backend now verifies the target exists before clearing stored results, reselects the target, commits edits, checks dialogs and checks the final fields. Failures can leave partial edits: inspect state before retrying. Do not blindly repeat a placement/edit call.

Dimension labels can appear as top-level UIA windows rather than descendants. Both are now recognized only when they have one noninteractive metric Text child. Hover tooltips are exempt only when their descendants are Text, Image or Separator; interactive content remains blocking. Regression tests cover those boundaries.

Supported numeric fields: ElementCountX/Y, PolygonPosition_X/Y/Z, ArrangementRotation_Z. Native acceptance currently covers count changes only; XYZ/rotation paths still need separate native verification. The exact tree ID includes the current object name and may change when counts change. The item must already be expanded; automatic discovery/expansion and stable object identity remain development work. Individual fixture coordinates, full arbitrary layout application, save/reopen persistence and report evidence for this edited project are not yet verified.

128 tests passed, including MCP discovery of `desktop_edit_arrangement`. The native calculation was performed through public CLI calls; no Codex Computer Use dependency was used.

Follow-up: individual fixture position readback and save/reopen persistence for this count-edit scenario are now verified in [tree and fixture inspection](tree-and-fixture-inspection.md). Arbitrary coordinate editing and complete large-project enumeration remain unverified.
