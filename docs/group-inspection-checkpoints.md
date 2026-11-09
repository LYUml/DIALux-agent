# Durable native group inspection

Tool-development capability; no assignment design is produced.

```powershell
.venv/Scripts/python.exe -m src.dialux_agent group-inspection-checkpoint --expected-project <existing.evo> --group-id '<exact native group ID>' --expected-count 168 --evidence-directory <new-directory>
```

MCP exposes the same operation as `inspect_group_checkpoint`. The operation uses a standalone Windows UIA worker, not Codex Computer Use. The expected native project must be open. It uses the shared interactive desktop and changes selection/view; do not concurrently edit the project or run another desktop operation.

The worker retains native ItemContainer COM references across all pages, addressing identity churn observed with independent per-page worker processes. Every continuation checks retained runtime and automation identities, and each selected fixture is materialized and checked before XYZ/rotation/name readback. Counts, coordinate frame, project/group, ordered inventory token, page offsets, finite geometry and unique identities are validated before accepting a page. Invalid evidence stops the run; guards are not relaxed to force completion.

The new evidence directory contains `journal.json`, hashed `page-NNNN.json` files and, only after complete collection and an unchanged saved-source hash, `observed.json`. The journal records partial failure. Existing directories are refused: there is no automatic retry, resume or rollback. A timed-out/killed process may leave `state: reading`; determine liveness from the actual process or execution handle, never the journal alone. The desktop transport allows up to 3600 seconds, then reports an unknown outcome. Large groups can exceed this bound. A successful collection does not prove planned geometry, product identity, whole-project inventory or an atomic snapshot; unsaved concurrent changes are not ruled out by the source file hash.

The ordinary `desktop-group-fixtures` paged API remains available for bounded reads. Its token can become stale across fresh worker processes on virtualized WPF content; this is a rejection, not permission to ignore token changes. Use the checkpoint for complete group collection. Native large-group validation is recorded separately in `large-project-validation.md`.

## Independent offline verification

`group-inspection-verify --evidence-directory <completed-directory> --layout <planned-layout.json>` / MCP `verify_group_checkpoint` checks the completed journal, every page hash/path/offset/identity, and exact assembly of `observed.json` before applying the existing all-fixture geometric matcher. It rejects partial journals, missing pages, duplicate runtime identities, changed bytes and a separately rehashed combined observation that differs from its pages. Position tolerance is 1 mm and rotation tolerance 0.05 degrees, matching native displayed precision. Fixture assignment is spatial and unambiguous, not list-order matching.

This is offline evidence validation. It neither authenticates the producer nor inspects the current DIALux project. Hashes can expose inconsistent or accidentally changed evidence but are not signatures. A collected checkpoint and a successful geometry verification are distinct outcomes. The verifier does not change the checkpoint or its state; callers may save its JSON result separately.
