# Journalled room arrangement creation

`desktop-arrange-room --expected-project <project.evo> --spec <request.json>` and MCP `desktop_arrange_room` share one independent Windows worker. This is a creation primitive; it does not claim that a lighting design is accepted.

Request fields:

- `room_name`: exact label in the native room context menu.
- `group_name`: new name, 1–40 plain ASCII letters/digits/spaces/._-.
- `product_id`: expected visible active luminaire product identifier; import photometry separately.
- `parent_id`: exact native storey `_Luminaires` tree node.
- `expected_groups`: exact IDs of existing realized expandable groups under that parent.
- `evidence_directory`: new directory for the durable journal; existing paths are refused.

The worker recovers Lighting mode, expands the parent, rejects filtered or unexpected realized inventories and visible reused names, selects the exact room label, and verifies the active product. Before clearing results or invoking placement it persists `pending_native_creation`. After placement it requires exactly one new realized group runtime identity while retaining every previous group identity. It selects that new runtime identity, assigns the requested name, and verifies the same identity under the new name.

A successful return is `created_unverified`. Read the new group's fixture coordinates in active-storey context and compare against the intended room geometry. Reinspect previous groups for unwanted geometry changes. Save, reopen and calculate separately. The room menu has no verified selected-state readback; realized UI nodes are not a complete native inventory. Neither room containment, fixture photometry identity nor existing-group geometry is proved by the creation return.

Failures retain the journal, including `failed_at` when the worker catches the exception. Worker termination can leave a pending state. Never automatically retry creation after failure or timeout, even with a different evidence directory; inspect the live project and journal first. An existing evidence directory is rejected before UI access. This is not automatic rollback, resume or cross-process locking. Do not run desktop mutations concurrently.

The original `desktop-arrange-space` keeps its conservative existing-content guard. The new command is an explicit, journalled multi-room alternative, not a relaxation of that guard.

## Native checkpoint, 2026-11-09

Public CLI creation was exercised on the separately saved synthetic `local/multiroom-public-api-v1.evo`. Starting with the two previously verified A/B groups, it added `Synthetic-corridor` and retained the new runtime identity through naming. The run journal is `local/corridor-creation-v1/journal.json`; the command returned `created_unverified` as designed.

Subsequent public paginated inspection found six corridor fixtures at X = 1.667, 5, 8.333 m, Y = 4.5 and 5.5 m, Z = 3.035 m, all zero rotation. A separate Shapely check confirmed that synthetic 0.6 m square envelopes at these coordinates fit the supplied corridor polygon (0,4)–(10,6). This checks the fixture against the supplied synthetic boundary, not a complete native boundary audit or manufacturer's physical dimensions.

The automated tests exercise intent persistence before a failing native creation, retention of failed-at state, same-directory retry refusal before UI access, changed-inventory refusal, invalid input guards and actual MCP tool discovery.

Post-creation inspection also compared all twelve A/B fixtures with `local/multiroom-two-groups-v1.json`: displayed positions, rotations and product names matched exactly. These checks cover the supplied realized groups; hidden objects and photometry internals remain outside the comparison.

The same public creation request was issued again with the original evidence directory and was refused without creating another group. Native recalculation and scoped export then completed for all three lit rooms:

| Room | Average lx | Uo | LPD W/m² |
| --- | --- | --- | --- |
| A | 531 | 0.56 | 6.5 |
| B | 695 | 0.59 | 9.75 |
| Corridor | 497 | 0.51 | 7.8 |

`local/three-lit-public-api-v1.pdf`: 45 pages, 2,975,307 bytes, SHA256 `1737f192c63b2f2867d2d86accde21f5351d5c09338770d0dc19177c2e77efa0`. Summary pairs are pages 15–16, 23–24 and 31–32. These are simulation outputs, not adopted regulatory targets or a compliance conclusion. The calculated native file was saved: 903,286 bytes, SHA256 `35848d89d1cda13bcca334577b84fe8a1ce3de2caecfb729b7bc2950c453c77b`. This new three-lit-room file has not yet undergone a separate reopen/readback gate. All 200 automated tests passed at this checkpoint; general large-project reliability remains unverified.
