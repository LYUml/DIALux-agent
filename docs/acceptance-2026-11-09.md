# Independent single-room prototype acceptance

The v9 run on Windows / DIALux evo 14.1 completed through public CLI commands using the independent pywinauto backend. No Codex Computer Use client performed the acceptance workflow. The initial cleanup of the previous test instance used direct pywinauto; all v9 operations from launch onward used the public CLI.

## Observed run

1. Generated `local/acceptance-v9.stf` from a synthetic 6 × 4 × 3 m room, named `CLI acceptance v9`, and read it back.
2. `desktop-launch` created a new DIALux process, PID 10108, with the implemented process-local TEMP/TMP workaround. Startup activation-email toast disappeared before import; no login action was automated.
3. `desktop-import-stf` loaded the room; `desktop-save-as` created `local/acceptance-project-v9.evo`.
4. `desktop-import-luminaire` loaded the traceable Philips 910505102817 ULD and read back 3602 lm / 26 W.
5. `desktop-arrange-space` created a 3 × 2 array of six luminaires, center (3, 2, 3.035) m. `desktop-save` saved placement before simulation.
6. `desktop-calculate` completed a fresh calculation: **531 lx**, **Uo 0.56**. `desktop-save` preserved the calculated native project.
7. `desktop-export-pdf` produced `local/acceptance-v9.pdf`, 28 pages. Pages 14–15 were rendered and visually checked. Area 24 m², height 3 m, workplane 0.8 m, reflectances 70/50/20%, maintenance factor 0.80, six luminaires and the result table match the inputs/observations. Report LPD is **6.50 W/m²**.
8. `desktop-open` switched to the saved v5 geometry fixture, saving v9's documentation settings, then reopened v9. Export to `local/acceptance-v9-reopened.pdf` retained the identical extracted room/scene, area, heights and three lighting values. PDF byte hashes differ; numerical/geometry comparison, not byte equality, proves this gate.
9. A separate real stdio MCP session discovered all ten desktop tools, queried the actual v9 project through `desktop_status`, and read 531 / 0.56 / 6.50 from the reopened report through `read_summary_pdf`.

Current artifact hashes and byte sizes are recorded in `acceptance-artifacts.json`. Native/PDF files and screenshots remain ignored local files, not redistributed in Git. The original two assignment files are separately covered by `local/input-manifest.json`.

## Acceptance scope and limits

This is a working single-room tool prototype, not the completed BSE3125 assignment or a general unattended building-design system. The public functions, shared MCP backend, usage skill, upstream license records and interchangeable criteria profiles are present. The saved native project and two PDFs provide reviewable real DIALux output.

- The fixture is synthetic. Assignment DWG scale/geometry and the independent CAD drawing remain assignment-phase work.
- Uo 0.56 fails the report's preset 0.60 target. This is correctly reported; no design compliance is claimed. The tool's success is execution and faithful evidence, not making every simulated design pass.
- Hong Kong BEC office LPD and Labour Department desk-lighting advice are distinct, source-backed modules. Applicability requires evidence. Other official references are registered but not automatically adopted. International/assignment criteria still need project-specific selection.
- Desktop control requires Windows, the tested English UI, an interactive logged-in DIALux session and foreground focus. It does not provide a private mouse or desktop. Unexpected dialogs and timeouts stop with an unverified outcome.
- Existing DIALux processes do not inherit newly configured temporary paths. New launches use an ASCII directory; the workaround avoids the independently reproduced ZeroMQ failure without changing installed DLLs or system environment settings. This is not a claim of stability on every machine/version.
- Automatic arrangement targets the current space of a single-room fixture. Arbitrary multi-room placement, geometry editing and optimization are not implemented.
- PDF export uses the current documentation selection. The reader accepts one adjacent English two-page room Summary in a larger report and refuses multiple room/scene summaries. It does not extract minimum illuminance or all glare metrics.

## Reproduce with new filenames

Use the commands in `README.md` and `python -m src.dialux_agent <command> --help`. Start from an empty workspace. Generate a fresh STF with `room-create`, then run `desktop-launch`, `desktop-import-stf`, `desktop-save-as`, `desktop-import-luminaire`, `desktop-arrange-space`, `desktop-save`, `desktop-calculate`, `desktop-save`, `desktop-export-pdf`, and `report-read` in that order. Pass the exact active `.evo` path as `--expected-project`, use product ID `910505102817` only with the documented validation asset, and choose unused destinations. Each CLI command emits JSON; the MCP tools expose the same backend. Do not retry a mutation merely because its observation timed out.

## Final checks

102 Python tests passed, including real MCP subprocess discovery and backend calls; 8 tests for the retained historical Node adapter passed. The local artifact/source verifier matched all 21 recorded files. The original assignment manifest reported no changed/missing files. The workflow skill validator passed. These checks supplement, rather than replace, the observed desktop workflow above.
