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

Standalone luminaire placement, PDF export and full end-to-end verification remain incomplete. Photometry import now has the additional gate below. The goal remains active. Unit tests cover worker transport/error semantics, and MCP discovery covers registration; neither replaces those remaining live gates.

## Reused sources

- [pywinauto UIA control documentation](https://pywinauto.readthedocs.io/en/latest/code/pywinauto.controls.uia_controls.html): Invoke-based button click and edit operations.
- [pywinauto 0.6.9 license](https://github.com/pywinauto/pywinauto/blob/0.6.9/LICENSE): BSD-3-Clause. Installed package reused, not copied into the repository.

Use `python scripts/check_local_evidence.py` to compare the current local artifacts and official caches with recorded hashes. This read-only check does not replay DIALux, authenticate sources or establish compliance. Exit 0 means matching bytes, 1 changed, 2 malformed input/I/O error, 3 missing local files. The separate input-manifest verifier checks assignment originals.


## Independent photometry import gate, 2026-11-09

`desktop-import-luminaire --expected-project local/standalone-validation-v5.evo --path local/luminaires/910505102817.uld --product-id 910505102817` and MCP `desktop_import_luminaire` submit the native file dialog and require the expected identifier plus visible photometry fields. The live CLI returned 3602 lm, 26.0 W, 99.8% and 138.5 lm/W; source SHA256 was `6dc1c0220a9928ce96f7110daf816b9db73b614c8f8ed5041216113d6d40e1fa`. This confirms the active product, not placement, uniqueness of catalog entries, or suitability for the assignment. DIALux may reuse existing catalog entries.

A separate direct UIA exploratory invocation of `aid_ArrangementFromSpace` created a 3-by-2 six-luminaire arrangement. Its reported center was (3, 2, 3.035) m and its estimate was 539.2 lx. It is not yet a public placement command. Dimension annotations appeared as native Popup windows; only exact noninteractive one-text metric labels are exempted from the dialog guard.

The following CLI calculation did **not** complete successfully. DIALux PID 3412 exited; Windows Application Error at 2026-11-09 07:22:42 reported DIALux 5.14.1.0, ntdll.dll and exception 0xc0000374. No cause is established. Placement had not been saved, and no actual result or report is claimed. The saved v5 geometry checkpoint remains the recovery input. The CLI reported completion unverified; no automatic mutation retry was performed.


## Saved arrangement and crash controls, 2026-11-09

Recovered the unmodified v5 geometry, re-imported the same ULD and repeated native automatic placement. Before calculation, `desktop-save-as` successfully created `local/standalone-array-v6.evo`, 421709 bytes, SHA256 `87d4249ea036262c92415dd90d6bbf9119a807586a0f28af1531fa24e8a4c315`. This preserves the six-luminaire reproduction independently of the failed calculation. Its calculation again terminated DIALux with 0xc0000374 (Application Error 07:25:26, PID 20476).

The previously successful single-luminaire v3 project also terminated during a fresh recalculation in this session. A further controlled run opened saved v6 and invoked calculation but did **not** query UIA afterward: process-only monitoring observed DIALux exit after five seconds. This rules out subsequent repeated UIA reads as a necessary trigger in that run, but does not establish the underlying cause or exclude the Invoke operation itself.

New CLI `desktop-arrange-space --expected-project <project.evo> --product-id <active-id>` and MCP `desktop_arrange_space` encapsulate the observed native automatic-placement action. It is scoped to the current space in a single-room fixture, requires visible expected product identity, refuses already calculation-ready content/results to reduce duplicate insertion, and reads back the selected arrangement. The native action was exercised directly; the public command still needs a fresh live end-to-end replay. It neither saves nor asserts lighting-target compliance. Stable calculation and independent PDF export remain unresolved acceptance gates.


## Additional calculation failure controls, 2026-11-09

Two further controlled runs used the saved v6 project. Launching DIALux with its executable directory as `work_dir` still terminated during calculation. A separate run used pywinauto `click_input()` on the freshly resolved CalculationButtonStart rectangle instead of UIA Invoke, then monitored only process existence; DIALux exited after four seconds. No Codex Computer Use was involved. These observations do not support working-directory differences or Invoke alone as the cause. No registry, installed DLL, account or global graphics setting was changed.

The calculation worker now detects disappearance of its original DIALux PID and reports process exit explicitly, rather than spending the remaining observation deadline on stale UI objects. This improves failure reporting; it is not a crash fix. The application stability issue remains open, and completed historical results must not be represented as a successful new calculation.


## Independent PDF export gate, 2026-11-09

CLI `desktop-export-pdf --expected-project local/adapter-module-calculation-v3.evo --path local/standalone-cli-export-v3.pdf` completed through standalone pywinauto; MCP exposes the same implementation as `desktop_export_pdf`. It opens Print Preview, selects native PDF export, chooses all pages of the current documentation selection, disables automatic viewer launch, submits a new destination, waits for stable bytes and parses the PDF page count. Existing output paths are refused. Export settings window creation precedes its child controls; the worker explicitly waits for the page-range control before acting.

Live output: 28 pages, 1518595 bytes, SHA256 `f432e22c88174e64ba6a02d8e507ff7a89c7155a46a1ddbeaca748cb70a60f09`. Page 15 was extracted and rendered at 150 dpi for visual review: 104 lx, Uo 0.21, 1.08 W/m², one Philips 26 W / 3602 lm luminaire. The table and failure marks are legible. This exports the previously saved v3 calculation, **not** a successful new calculation; `fresh_calculation_verified` deliberately remains false. The preset office targets on this report are not the Hong Kong rule pack. Native project settings may become modified when visiting documentation; the export command does not save those settings.

At this export checkpoint, the strict two-page reader did not yet accept the full document. The subsequent integration gate below resolves that reader limitation. Stable fresh calculation and a complete new-project replay remain acceptance work.


## Export-to-reader integration gate, 2026-11-09

`report-read --path local/standalone-cli-export-v3.pdf` now locates exactly one adjacent pair of English Summary pages within the complete report. The observed result identifies pages 14–15 of 28, area 24 m², height 3 m, workplane 0.8 m, and 104 lx / Uo 0.21 / 1.08 W/m². Each measurement cites original PDF page 15 and the exported artifact hash. Existing CLI/MCP report-check uses this same reader; report targets are still not adopted as regional criteria.

Selection rejects multiple summaries, nonadjacent pages, different room/scene headers, missing fields, and calculation-surface mismatches. Tests cover original page-number mapping and those ambiguity cases; the local 28-page exported artifact is also parsed when present. This is report integration, not fresh-calculation evidence.


## Single-CPU diagnostic control, 2026-11-09

After exporting, preserved documentation settings in `local/export-settings-v7.evo` (915352 bytes, SHA256 `6940d1d61f4caf85fbcd76f3e7953ed76e64551d60c490ba2d3a17adfc505d70`) without overwriting the original v3 checkpoint. Set only the running DIALux PID 8220 CPU affinity from 24 CPUs to CPU 0; recorded the original affinity in ignored local diagnostic data. Opened saved six-luminaire v6 and invoked the CLI calculation. DIALux again exited, and the new worker error identified the process exit immediately. Windows Application Error at 07:38:33 reports the same 0xc0000374 / ntdll.dll signature. The process terminated, so this process-only affinity setting no longer exists; no system CPU settings were changed.

This control does not support a requirement for multiple active CPUs to reproduce the failure. It does not identify the faulty component. The machine has an Intel Core Ultra 9 275HX with 24 logical processors. Further troubleshooting needs a crash stack or equivalent diagnostic evidence rather than another identical calculation retry. Native project creation, import, saving and stored-result export continue to have separate positive evidence; fresh calculation remains a failed gate.


## Crash dump captured, 2026-11-09

Downloaded [Microsoft Sysinternals ProcDump](https://learn.microsoft.com/en-us/sysinternals/downloads/procdump) from its official download endpoint, verified its Microsoft Corporation Authenticode signature, and attached version 12.02 to the uniquely launched DIALux PID 14548 with `-e -n 1`. No permanent postmortem debugger registration or WER upload was enabled. Reproducing calculation on saved v6 captured unhandled C0000374 at 07:40:34. ProcDump completed one dump and stopped monitoring. The CLI reported an unexpected dialog and did not claim success. The instrumented process remained observable afterward; it was not treated as a valid completed calculation.

Local-only `local/diagnostics/dialux-calculation.dmp`: 61951228 bytes, SHA256 `912069475210d515cbc2de5080b954a0abc3b53b38342987c073344354dc3e3c`. It is ignored by Git and has not been transmitted. Exception thread ID 9348, address 0x7ffa3169a3b5. [skelsec/minidump](https://github.com/skelsec/minidump), MIT, installed version 0.0.24, was reused for local parsing only; it is not a runtime dependency of the agent. ProcDump binaries are also local diagnostic tools, not redistributed repository dependencies.

An aligned-word scan of the exception thread stack found addresses inside Dialux.PipeStreams.dll, libzmq-mt-4_3_5.dll, Dialux.NMTLib.dll and Dialux.Geometry.dll. This is **not an unwound/symbolized call stack** and does not establish causality. The dump now allows deeper analysis without another blind reproduction. Root cause and stable fresh calculation remain unresolved.


## Shell-launch control and debugger preparation, 2026-11-09

Closed the instrumented test instance without saving its failed-calculation changes; after the main window disappeared, its residual PID 14548 was terminated. Saved v6 remained the reproduction input. Launched DIALux through Windows Shell.Application.ShellExecute and opened v6 through the CLI. Calculation still exited. A 50 ms process-enumeration loop did not observe Dialux.ExtProcCalc.exe; this does not rule out a shorter-lived process. The installed signed executable exists at the installation's x64 subdirectory. This control did not fix the failure and does not prove complete separation from the originating process environment.

Started installation of Microsoft WinDbg 1.2611.4001.0 through the official winget package for offline dump analysis. Winget verified its installer hash and Windows AppX deployment reported Stage operation running. Installation completion and symbolized analysis have not yet been established at this checkpoint. No new calculation result is claimed.


## Process-local TEMP workaround: fresh calculation succeeds, 2026-11-09

WinDbg installation completed. Its bundled CDB expanded the exception stack using cached Microsoft symbols: heap failure during `RtlFreeHeap` / `ucrtbase!free_base`, reached from `Dialux.PipeStreams.dll` during exception unwinding, with ZeroMQ below. DIALux modules have export symbols only; large export-name offsets are not source-level function attribution.

An isolated ctypes probe loaded the **installed** `x64/libzmq-mt-4_3_5.dll` with documented pointer signatures. Under inherited TEMP/TMP (`C:\Users\LYUML-~1\AppData\Local\Temp`) socket creation reproduced `Bad file descriptor ... epoll.cpp:73`, followed by 0x40000015. Ordinary Python Winsock loopback bind succeeded. Setting only the probe process TEMP/TMP to the checkout's resolved `local/tmp` made the identical library create a PAIR socket, bind loopback, close and terminate successfully.

Upstream [libzmq issue 4730](https://github.com/zeromq/libzmq/issues/4730) reports the same epoll failure; [merged fix 4734](https://github.com/zeromq/libzmq/pull/4734) discusses Windows IPC connection failure and temporary-path sensitivity. This supports the workaround but does not prove every underlying Windows failure mechanism on this machine.

Launched DIALux PID 2236 with that process-local directory and opened the unchanged six-luminaire v6 fixture. Public CLI calculation completed with **531 lx, Uo 0.56**. Save As created `local/standalone-calculated-v8.evo`, 457948 bytes, SHA256 `f0fe63ad37b14b04a9a221e0d28c82d0a08fe9617fa0131e34793c61ff2fbdfc`. Independent CLI exported `local/standalone-calculated-v8.pdf`, 28 pages, 1574580 bytes, SHA256 `cbd453922b11d842d8693421d60eb190e1f36bf9fc9b5614db9e749a12dfd033`. The shared reader extracted 531 lx, 0.56 and 6.50 W/m² from page 15. These are fresh results from this run, not the earlier cached single-luminaire baseline. They do not establish compliance; uniformity is below the report's preset target.

`desktop-launch` now scopes TEMP/TMP to resolved checkout/local/tmp when creating a new process, restoring the worker environment afterward. Optional `--runtime-temp` / MCP `runtime_temp` selects another ASCII directory (at most 70 characters). This conservative bound leaves room for IPC filenames; it is a prototype constraint, not a universal Windows rule. Existing running instances are reused without changing their inherited environment, so they do not receive this workaround. No system/user environment setting or installed DIALux DLL was changed.

Export now expands the native Page Range group before selecting All; collapsed saved UI state had hidden that radio control. Summary parsing now accepts the observed line break immediately before `(Light scene ...)`. 102 tests passed. Still required: public launcher fresh-process replay, public arrangement command replay, save/reopen result comparison and final acceptance audit. One successful recovery is not a claim of universal stability.
