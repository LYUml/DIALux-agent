# Standalone Windows desktop backend

The user explicitly requires CLI/MCP desktop operations independent of Codex Computer Use. This is an acceptance requirement, not an optional future enhancement. The earlier sky-based adapter remains research evidence; it does not satisfy this requirement by itself.

`src/desktop.py` runs a fresh, time-bounded `src/windows_worker.py` process. It reuses pywinauto 0.6.9 (BSD-3-Clause) and its Windows UI Automation backend, with psutil process discovery. It does not import sky, call Codex or expose a desktop network service. Public CLI/MCP share this implementation.

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-status
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-save --expected-project local/adapter-module-calculation-v3.evo
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-calculate --expected-project local/adapter-module-calculation-v3.evo --recalculate
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-open --path local/adapter-module-calculation-v3.evo --expected-current-project local/adapter-calculation-v2.evo --save-current
```

The MCP tools are `desktop_status()` and `desktop_save(expected_project)`. The latter requires an existing `.evo` file matching the active document title. Multiple processes, unknown secondary windows, mismatched files and unavailable controls are refused. A recognized energy tachometer overlay is distinguished by its observed control IDs. Save uses UIA Invoke rather than coordinate input. DIALux can disable commands while inactive, so save activates the verified DIALux window and rechecks state. It can take foreground focus; this is not a separate desktop or second mouse.

Save success requires an observed file modification and several stable file-size/time samples. The returned hash describes those saved bytes; it is not a reopen test. A 30-second worker timeout reports unknown outcome, never retries automatically. Read status and inspect the artifact before deciding how to recover.

## Live checkpoint, 2026-11-08

- Independent process discovered evo 14.1, MainWindow, the exact native project and Save/Calculation controls.
- UIA Invoke saved `adapter-module-calculation-v3.evo`, with subsequent independent CLI save succeeding after explicit window activation.
- Requesting v2 while v3 was open was rejected before save.
- Latest saved v3: 852116 bytes, SHA256 `f0fd47cd68e13c21de28a5a11da3c0714a9310da0dfea6c8577dda4d306f3eaf`. Earlier sky checkpoint hashes remain historical records.

Standalone calculation was subsequently implemented and live-tested through both the direct worker and public CLI. `desktop_calculate(expected_project, recalculate=False)` is also registered with MCP. `recalculate=True` explicitly permits discarding cached results before starting a fresh calculation; without it an unavailable Calculate button is refused. It returned the live 104 lx / 0.21 result controls after resetting and recalculating v3. The native project is not automatically saved. Completion checks look for available results, disabled start, enabled discard, no visible obsolete-results text and no Cancel command; this is UI state evidence, not a PDF comparison or compliance judgment. The worker has a 45-second observation period and a 75-second outer process limit for this operation.

`desktop_open(path, expected_current_project=None, save_current=False)` uses the observed File/Open menu IDs, native filename edit ID 1148 and Open button ID 1. It reads back the literal filename before submitting and waits for the exact requested native project title. Existing projects require their expected path; modified work is refused unless saving is explicitly requested. WPF duplicate menu entries are deduplicated by runtime ID, while genuinely distinct matches are refused. This English-dialog path was live-tested through CLI: v2 was saved and v3 opened. A real stdio MCP `desktop_status` call also read the live v3 project successfully. UIA open verification is distinct from checking the reopened report values.

The latest standalone recalculate/save/open cycle changed local native checkpoint hashes: v2 `af1d6d05318772a2c1cfdab6e5ae294e1900dccf60dc7d7d0e04ca4d6791c602`, v3 `7fc80a915e9c985769dcd965e56bcd19cbd7ffe129371edc858a7d5b200491ff`. The acceptance manifest tracks these new checkpoints; earlier documentation retains historical hashes. Exported v1/v2 PDFs were not changed.

## Startup, STF import and Save As gate, 2026-11-09

After resuming, no DIALux process was running. The independent `desktop-launch` command started the installed executable and observed its main window. It reuses a unique matching existing process rather than spawning a second instance. A missing executable, wrong executable name or multiple running processes is refused.

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-launch
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-import-stf --path local/standalone-room-v4.stf
.\.venv\Scripts\python.exe -m src.dialux_agent desktop-save-as --expected-project local/standalone-room-v4.evo --path local/new-validation.evo
```

Equivalent MCP tools: `desktop_launch`, `desktop_import_stf`, `desktop_save_as`. STF import requires an empty workspace and a parseable room input. It does not close or replace an existing project. The imported fixture is named `Standalone UIA validation`, with source hash `5567bcdf31d727ce46915e06d75b1e3c04fdcd2caaa355b98c37237b3aa32658`. The independent app capture showed the named room and its geometry. Exact dimensions/reflectances have not yet been read back through UIA, so the operation deliberately returns `geometry_verified_in_evo: false`.

Import proposes an `.evo` title before a native file exists. Save As therefore accepts a matching current title even when that proposed path is absent, but requires a **new** destination. Existing outputs are refused. Windows Open used filename ID 1148; the resumed Save dialog used ID 1001. Its ValuePattern alone changed the displayed/read-back value without updating the internal filename: an initial attempt saved the original proposed name and correctly failed the requested-path check. The fixed path commits the field with targeted keyboard events before submission. No user clipboard is used. This can take keyboard focus.

Save notifications also appear as unnamed UIA windows. The worker now waits read-only for those windows to disappear rather than declaring immediate failure or answering an unknown dialog. Success requires the target file to stabilize and the exact requested title without an unsaved marker. The fully successful CLI checkpoint is `local/standalone-validation-v5.evo`, 419865 bytes, SHA256 `019662e5a15e85ec10c5dba558692331d25a26acd6497d758e0f8b0e9ac08ab5`. Earlier v4 attempts remain local for diagnosis. This fixture has no validated luminaires or lighting calculation yet.

Standalone photometry import, luminaire placement, PDF export and full end-to-end verification are **not implemented or validated yet**. The goal remains active. Unit tests cover worker transport/error semantics, and MCP discovery covers registration; neither replaces those remaining live gates.

## Reused sources

- [pywinauto UIA control documentation](https://pywinauto.readthedocs.io/en/latest/code/pywinauto.controls.uia_controls.html): Invoke-based button click and edit operations.
- [pywinauto 0.6.9 license](https://github.com/pywinauto/pywinauto/blob/0.6.9/LICENSE): BSD-3-Clause. Installed package reused, not copied into the repository.

Use `python scripts/check_local_evidence.py` to compare the current local artifacts and official caches with recorded hashes. This read-only check does not replay DIALux, authenticate sources or establish compliance. Exit 0 means matching bytes, 1 changed, 2 malformed input/I/O error, 3 missing local files. The separate input-manifest verifier checks assignment originals.
