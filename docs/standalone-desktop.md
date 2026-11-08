# Standalone Windows desktop backend

The user explicitly requires CLI/MCP desktop operations independent of Codex Computer Use. This is an acceptance requirement, not an optional future enhancement. The earlier sky-based adapter remains research evidence; it does not satisfy this requirement by itself.

`src/desktop.py` runs a fresh, time-bounded `src/windows_worker.py` process. It reuses pywinauto 0.6.9 (BSD-3-Clause) and its Windows UI Automation backend, with psutil process discovery. It does not import sky, call Codex or expose a desktop network service. Public CLI/MCP share this implementation.

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-status
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-save --expected-project local/adapter-module-calculation-v3.evo
```

The MCP tools are `desktop_status()` and `desktop_save(expected_project)`. The latter requires an existing `.evo` file matching the active document title. Multiple processes, unknown secondary windows, mismatched files and unavailable controls are refused. A recognized energy tachometer overlay is distinguished by its observed control IDs. Save uses UIA Invoke rather than coordinate input. DIALux can disable commands while inactive, so save activates the verified DIALux window and rechecks state. It can take foreground focus; this is not a separate desktop or second mouse.

Save success requires an observed file modification and several stable file-size/time samples. The returned hash describes those saved bytes; it is not a reopen test. A 30-second worker timeout reports unknown outcome, never retries automatically. Read status and inspect the artifact before deciding how to recover.

## Live checkpoint, 2026-11-08

- Independent process discovered evo 14.1, MainWindow, the exact native project and Save/Calculation controls.
- UIA Invoke saved `adapter-module-calculation-v3.evo`, with subsequent independent CLI save succeeding after explicit window activation.
- Requesting v2 while v3 was open was rejected before save.
- Latest saved v3: 852116 bytes, SHA256 `f0fd47cd68e13c21de28a5a11da3c0714a9310da0dfea6c8577dda4d306f3eaf`. Earlier sky checkpoint hashes remain historical records.

Standalone import, luminaire placement, calculation, PDF export and end-to-end reopen are **not implemented or validated yet**. The goal remains active. Unit tests cover worker transport/error semantics, and MCP discovery covers registration; neither replaces those remaining live gates.

## Reused sources

- [pywinauto UIA control documentation](https://pywinauto.readthedocs.io/en/latest/code/pywinauto.controls.uia_controls.html): Invoke-based button click and edit operations.
- [pywinauto 0.6.9 license](https://github.com/pywinauto/pywinauto/blob/0.6.9/LICENSE): BSD-3-Clause. Installed package reused, not copied into the repository.

Use `python scripts/check_local_evidence.py` to compare the current local artifacts and official caches with recorded hashes. This read-only check does not replay DIALux, authenticate sources or establish compliance. Exit 0 means matching bytes, 1 changed, 2 malformed input/I/O error, 3 missing local files. The separate input-manifest verifier checks assignment originals.
