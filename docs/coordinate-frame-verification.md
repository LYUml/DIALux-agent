# View-dependent native coordinates

2026-11-09 multiroom testing found a material coordinate-frame hazard. After selecting Synthetic B (x=6..10, y=0..4) in the native room-context menu, automatic arrangement reported centre X=2.000. Switching the same selected arrangement to storey context changed its displayed centre to X=8.000, without moving geometry. Numeric position controls are relative to the active view context.

The backend now explicitly activates storey context before reading individual fixture coordinates or editing fixture/arrangement coordinates. Group readback declares `coordinate_frame: active_storey`; planned layouts carry the same declaration. Comparisons reject absent or mismatched frame labels, and batch application rejects unqualified observations before movement. `active_storey` is not a site/world coordinate guarantee: multi-storey transforms and reference-coordinate-system changes still need their own verification.

Existing saved readbacks/plans without frame metadata must be regenerated before comparison/application. Do not add the field to old evidence by assumption. Earlier single-room tests used a room at the storey origin, which concealed this distinction.

New `desktop-room-context --expected-project ... [--room-name ...]` / MCP `desktop_room_context` lists observed room-menu labels or invokes exactly one matching name. Duplicate/unknown names fail. The native menu exposes no reliable selected-state UIA pattern, so the result reports only `selection_invoked`, with `active_room_verified: false`. A successful click alone is not proof of edit scope.

Native evidence: selected Synthetic B by its label, imported the same known local test photometry, and invoked native automatic placement once. Subsequent public paginated readback in storey coordinates found six fixtures at X=6.667,8.000,9.333 and Y=1.000,3.000, Z=3.035. All centres lie in the intended B room. This verifies this placement's resulting location; no claim is made that room-menu invocation alone is sufficient. Recorded in ignored `local/three-room-B-fixtures-v1.json`.

171 tests passed, including missing/room/site frame rejection and room-label validation. Other rooms have not yet been lit, and complete multiroom calculation/report acceptance remains pending. No assignment work was performed.
