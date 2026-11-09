# Same-level multiroom import checkpoint

`rooms-create --spec <room-array.json> --output <new.stf>` / MCP `create_rooms` validates and serializes multiple rooms through the unchanged MIT upstream MCP_Dialux writer. It reuses the upstream insertion of neighbouring wall junction vertices. Inputs require unique Latin-1-compatible room names, explicit metre geometry and assumptions; overlapping interiors are rejected while shared edges are allowed. It supports one common geometric level, not multiple storeys or inferred wall thickness.

`desktop-close-project --expected-project <project.evo> [--save-current]` / MCP `desktop_close_project` closes only the expected active project and refuses unsaved changes unless saving is explicitly requested. It verifies the empty DIALux workspace before reporting success. This permits a subsequent public STF import without relying on manually clearing the workspace.

`desktop-read-space --expected-project <project.evo> --tree-item-id <exact-visible-space>` / MCP `desktop_read_space` selects one native space and reads its name, height, working-plane name/height/margin and maintenance factor. It does not claim full boundary verification.

Native test on 2026-11-09:

- `examples/synthetic-three-rooms.json` defines rooms A (24 m²), B (16 m²) and a corridor (20 m²) sharing boundaries. The upstream writer inserts the junction (6,4) into the corridor's originally four-vertex contour; serialized readback shows five vertices and unchanged area.
- Public CLI closed the saved bulk test, imported the three-room STF and saved a new native project. STF SHA256 `01b08188ed5e556ed461548a08231085377ad72021d6aed7368389a548837e16`; native saved SHA256 `1e0c7d157109c62fba44dc1dd6790855c046de1a4e322152a5241adcf2ed4eea`.
- Native tree inspection found three distinct rooms in one STF building/storey. Public space readback returned each correct room name, height 3.000 m, working-plane height 0.800 m, margin 0.000 m and maintenance factor 0.80.
- Independent pywinauto floor-plan capture `local/three-room-native-view-v2.png` was visually inspected: two lower rooms and the full-width upper corridor appeared as intended, with no observed diagonal crossing the corridor. This is visual topology evidence, not a complete native boundary/area measurement audit. No Codex Computer Use dependency was used.
- 167 tests passed, including adjacent-room serialization, overlap/duplicate rejection and unsaved-project close protection. Public tool discovery includes the three new operations.

No luminaires have been placed in this multiroom test yet. Multiroom simulation/report export, native boundary measurement, openings, obstructions and multi-storey placement remain pending. No assignment geometry or deliverable was created.
