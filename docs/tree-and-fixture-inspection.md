# Native project-tree and fixture inspection

The standalone CLI/MCP now exposes `desktop_project_tree(expected_project, expand_id=None)` and `desktop_group_fixtures(expected_project, group_id)`. CLI equivalents are `desktop-project-tree --expected-project ... [--expand-id ...]` and `desktop-group-fixtures --expected-project ... --group-id ...`.

The tree tool activates the native project-tree tab and reports realized nodes, names, visibility and expansion state. An exact visible node can be expanded idempotently. It does not claim the whole project is enumerated: filters, collapsed branches and UI virtualization can hide objects. It does not clear a user's search filter.

After reopening a project, ancestor branches may be collapsed. First inventory the tree, expand the returned Luminaires node, then use the returned group ID for fixture reading. Do not synthesize IDs by splitting display names on underscores or assume the previous expansion state persisted.

Observed in the synthetic `placement-probe-v1.evo` on 2026-11-09: the four individual fixture nodes had identical automation IDs. The tool retains every record and includes its session-local UIA runtime ID. Unique-ID edit operations still reject ambiguous matches; they do not silently pick the first duplicate.

The group reader expands an exact group, selects each realized leaf by runtime identity and reads its native XYZ position and XYZ rotation fields. Runtime identities are checked anew after switching tabs; they must not be reused across project reloads. The operation changes UI selection, not geometry. Native display rounding applies. It is bounded by the desktop worker timeout and does not promise large-project enumeration.

The reader now returns at most four fixtures per operation (`limit` 1–4, default 4). Continue using its `next_offset` and `inventory_token`; CLI exposes `--offset`, `--limit` and `--inventory-token`. Missing/stale continuation tokens fail if realized node identities or order changed. The token does not prove geometry remained unchanged between calls, and paging does not discover virtualized/offscreen objects. Avoid concurrent editing during inspection. `realized_node_count` describes only the current UIA inventory; `complete_inventory` remains false.

Native pagination check on 2026-11-09 read the saved four-fixture bulk test in two pages of two fixtures. Both pages returned the same identity token; the second returned no next offset. The four coordinates matched the saved grid. Automated coverage includes changed order, missing tokens, bounded page sizes and collection of all pages before bulk application. 163 tests passed.

Public CLI readback of the synthetic four-fixture group returned `(1.5,1,3.035)`, `(4.5,1,3.035)`, `(1.5,3,3.035)`, `(4.5,3,3.035)` metres, each with zero XYZ rotation. This provides individual native position evidence for the previous count-edit test, not proof that arbitrary generated layouts can already be applied.

Persistence gate also passed: opened another native project, then reopened the saved test project, rediscovered/expanded its Luminaires branch and read the same four positions through the public desktop backend. Evidence is in ignored `local/reopened-fixtures-v1.json`. The test project's saved SHA256 remains `e7e30faa39da768ff000c1ee24085bf284bc8409d9e616a287296315569b33fc`. The older acceptance project remains unchanged at `e43c9e75083d11e7c777c2b534cc3910853c047e3a5b4251d6cacf9debc70cad`. Its automatic modified-on-open state was saved to a new transit copy, not over the acceptance file.

133 automated tests passed, including quoted identity transport without shell interpretation, invalid group-identity rejection and stdio MCP discovery. Real native readback was tested separately; no assignment design was produced.
