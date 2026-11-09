# Multi-room placement development checkpoint

Synthetic projects only. No assignment design or submission artifact is produced.

## Native evidence, 2026-11-09

The calculated three-room B-only project was saved as `local/multiroom-placement-v1.evo` before experimentation. A guarded direct worker probe selected Synthetic A, cleared old calculation results and invoked native arrangement-from-space once. It created another six-luminaire arrangement, with the same default name as B. This demonstrated that default group names cannot identify two same-product groups reliably.

The new group was renamed and independently inspected. The public `desktop_edit_arrangement` API now supports `ArrangementObjectName`; CLI JSON values and the existing MCP tool expose the same capability. Names are limited to 1–80 plain ASCII letters, digits, spaces, dots, underscores and hyphens. Realized-tree duplicate labels are rejected before mutation. This is not an exhaustive hidden/virtualized-node uniqueness check. A successful rename changes the tree ID; callers must refresh their inventory. Exact field readback is mandatory, and failure may leave a partial edit.

Native text entry initially lost characters at default speed; the working path focuses the name field and paces input. The public API changed `Synthetic-A-grid` to `Synthetic-A` and read it back successfully. The separate two-group inspection (`local/multiroom-two-groups-v1.json`) found:

- A: six fixtures, X = 1, 3, 5 m; Y = 1, 3 m; Z = 3.035 m.
- B: six fixtures, X = 6.667, 8, 9.333 m; Y = 1, 3 m; Z = 3.035 m.
- All twelve displayed rotations were zero. B's six positions exactly matched its earlier `local/three-room-B-fixtures-v1.json` readback.

Coordinates were normalized to active-storey context. This verifies the observed fixtures, not a complete hidden-object inventory or a native room-boundary audit. The two-lit-room project has not yet been recalculated/exported or reopened for persistence verification.

## Report-to-edit mode recovery

Native PDF preview switches DIALux into Output mode, where ProjectTreeTool is absent. Project-tree reading, space reading and arrangement editing now select the exact native LightingDesignMode when their required tree tool is absent. A live PrintPreview → public project-tree worker sequence recovered 29 realized nodes. Unknown or ambiguous modes still fail.

## Remaining work

Public `desktop_arrange_space` retains its existing-content guard. The successful A placement was a development probe, not a completed repeatable multi-room placement API. That API still needs a persistent operation journal, verified target scope, new-group identity/readback, duplicate/retry handling and post-placement checks of existing groups. DIALux's five-minute save reminder also interrupted two checkpoints; it was inspected and dismissed explicitly, and generic operations still refuse unknown dialogs.
