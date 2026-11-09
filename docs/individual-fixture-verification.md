# Individual native fixture movement

2026-11-09 synthetic test, not assignment work. A new native `individual-probe-v1.evo` was saved from the translated-layout test. The independent backend `desktop_edit_fixture` moved one fixture from (1.7,1.1,3.035) to (1.9,1.3,3.035) metres.

The operation requires both the current UIA runtime ID and its expected prior XYZ position. It verifies a unique visible object, native selection and the prior coordinates before clearing cached results. It reselects and rechecks after clearing results, commits writable coordinate fields and rejects unexpected dialogs or mismatched readback. It does not silently choose the first same-name object. A repeated request with the old prior coordinates was rejected before another movement.

Independent public group inspection after the edit observed (1.9,1.3,3.035), (4.7,1.1,3.035), (1.7,3.1,3.035), (4.7,3.1,3.035). The other three fixture positions were unchanged and the group retained four objects. Fresh native calculation returned displayed average 366 lx and uniformity 0.34. These are test results, not compliance assertions. Saved native SHA256: `6c30b078625761041575dfefee80d800a6aa0fc46584098834da99e1b6700c01`.

Save/reopen verification also passed: opened a separate transit project, reopened the edited project, expanded its Luminaires branch and independently reread all four fixture positions. They matched the expected moved fixture and unchanged neighbours exactly at displayed precision. Readback is stored in ignored `local/individual-reopened-v1.json`. A transient save-related secondary window initially blocked switching projects; status was rechecked before continuing, without dismissing an unknown dialog.

CLI: `desktop-edit-fixture --expected-project <project.evo> --parameters <request.json>`. The request contains `runtime_id`, `expected_position_m` and `position_m`. Obtain the runtime identity from a fresh `desktop-group-fixtures` inspection. Runtime IDs are not persistent across reloads. The MCP function takes these as structured arguments.

This low-level operation does not check room containment, optimize a design, save automatically or verify other fixtures. Failures after a partial edit require inspection before retrying. Full layout orchestration must enforce geometry constraints and verify the resulting whole fixture set separately. Arbitrary bulk creation/removal and large-project support remain incomplete.

146 automated tests passed, including invalid identities/nonfinite coordinates and stale-position rejection before result clearing. Native movement, unaffected-neighbour readback and recalculation were tested separately through the independent desktop backend.
