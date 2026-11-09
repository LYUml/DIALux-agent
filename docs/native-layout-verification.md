# Native synthetic layout verification

2026-11-09: public CLI `layout-verify-native` completed with AutoCAD 2027 Core Console, using `local/synthetic-grid-v1.dxf` and new output directory `local/native-layout-v3`. This is an agent test, not assignment work.

- Source SHA256: `4deb284a202f92d31b511c9e02bd6eae2d60933fe581327ad6a2d035904d2f80`; unchanged after both native processes.
- Saved DWG SHA256: `669e53df47fac8786443299bbc9ca94e75a8384e0586334b9013b8009449908f`.
- A separate process reopened a copy of the saved DWG and exported DXF. All 23 fixture IDs, insertion XYZ coordinates, rotation angles, scales and block names matched. Native INSUNITS=6 (metres).
- This does not verify block-shape fidelity, printed appearance, DIALux placement or lighting performance.

Default product selection stalled twice before the survey script executed. Explicit `/product ACAD` opened the same saved DWG successfully, and the complete public command then passed. Both save and survey commands now select ACAD. Timeout failures preserve captured console output and never emit a success manifest. The evidence identifies a working launch configuration; the underlying startup fault has not been conclusively diagnosed.

An exploratory isolation invocation also opened a separate saved drawing, but its arguments were interpreted as an isolation key/folder rather than language options. It is not used by the backend. The validated implementation needs no isolated profile or global configuration changes.

Autodesk documents the Core Console `/product` and `/isolate` switches in [AutoCAD Automation training](https://blog.autodesk.io/wp-content/uploads/2025/09/APS-Training-AutoCAD-Automation-1.pdf). It also recommends testing a vanilla AutoCAD profile for toolset-specific opening problems in [drawing freeze troubleshooting](https://help.autodesk.com/view/ACADWEB/ENU/?caas=caas%2Fsfdcarticles%2Fsfdcarticles%2FFreeze-or-crash-when-opening-drawings-in-AutoCAD.html).

Automated suite: 114 tests passed, including actual stdio MCP DXF export, duplicate-ID rejection and timeout-log preservation. Native acceptance is recorded separately above; unit tests do not substitute for it.
