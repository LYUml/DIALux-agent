# Desktop adapter

`desktop/dialux-session.mjs` reuses the installed Computer Use `sky` client. It does not bundle a second automation engine or expose a remote desktop server. Run it from the authorized `node_repl` environment after reading the computer-use skill:

```js
globalThis.sky = (await import('@oai/sky')).sky;
globalThis.DialuxSession = (await import('file:///C:/Users/lyuml-win/Desktop/DIALux-agent/desktop/dialux-session.mjs')).DialuxSession;
globalThis.session = new DialuxSession(sky);
globalThis.observed = await session.connect();
```

Inspect the returned screenshot and accessibility state. In a separate call, `observed = await session.save(observed)` requests save and returns fresh state. Each observation can authorize only one action in this session. Reobserve after manual input, other tool actions, errors or changed UI; the module cannot detect every out-of-band change.

Window selection requires exactly one returned DIALux_x64.exe window. It ignores controls nested in unrelated/secondary windows. A missing, ambiguous or disabled control causes refusal. The caller still checks screenshots for modal dialogs, because accessibility alone is incomplete. Save uses Ctrl+S after confirming the observed Save control is enabled. This path was tested in real evo 14.1 and a new save notification was observed on 2026-11-08. The initial accessibility-index click failed despite a returned index; it was replaced with the application's observed shortcut.

`calculate(observed)` uses the observed CalculationButtonStart control; this accessibility-index path remains unverified in the live app. The explicit screenshot path described below **has been live-verified through this module**. No import, placement or export methods are implemented in this adapter yet. The Python MCP does not host this module: AI uses the MCP for file/result operations and the desktop skill for these session operations. A standalone unattended CLI/MCP driver remains unfinished.

## Stale accessibility recovery

Live testing on 2026-11-08 showed a stronger limitation: even a new capture can retain an old InformationBox and disabled controls after the screenshot has visibly updated. Repeated captures alone did not fix this. Do not infer completion from the accessibility tree or silently retry a failed input.

`clickObserved(observed, {action, screenshotId, x, y})` is an explicit screenshot-guided path for `save` or `calculate`. First inspect the current screenshot for the intended enabled control and blocking dialogs; in the next call supply that screenshot's ID and the point located in it. The module checks current observation identity, screenshot membership and finite in-bounds coordinates. It cannot verify the semantic meaning of the chosen pixels; `action` is a caller declaration, not visual recognition. No coordinates are stored as defaults. Capture results identifying a different app/window are rejected.

In `local/adapter-calculation-v2.evo`, a separate Save As copy, the test luminaire X coordinate was changed from 2.800 to 3.000 m. DIALux displayed its results-invalidation confirmation. After confirmation, direct screenshot-guided Computer Use started calculation and observed the progress panel followed by the results overview (uniformity displayed 0.22). The new module's visual **save** path was then exercised and DIALux displayed the notification naming this copy. The second PDF export and native reopen were subsequently verified; see `live-validation-2026-11-08.md`. This is still not a live verification of the module's calculation path. Both PDFs are report-reader regression baselines.

## Module calculation gate

A subsequent test changed X to 2.900 m through the visible field. Before calculation, the results overview explicitly displayed an obsolete-results warning. Calling `clickObserved` with action `calculate` and the inspected screenshot's Calculation button point removed that warning and produced a new overview: 104 lx and Uo=0.21. The result was saved using File > Save As to `local/adapter-module-calculation-v3.evo` (852106 bytes, SHA256 `dcc02b6bc993fe30230a9a6d00fe35f14d563e86aa5f381badd4af6ec79e21a8`). The v2 native file retained its recorded hash. No third PDF or reopen gate is claimed.

The same visual path is available as `calculate(observed, {screenshotId, x, y})` and `save(observed, {screenshotId, x, y})`. Select the point from the **current** screenshot, never copy coordinates from this document or a prior run. These methods submit input and return observations; they do not autonomously classify completion. Inspect the obsolete-results banner, result values and subsequent report evidence before declaring success.

DIALux's save reminder and results-invalidation prompts expose a window with ID `InformationBox`, not a dialog role. The accessibility path now refuses this observed window before filtering foreign windows. Because this tree can itself be stale, recovery requires visual inspection; the adapter never automatically answers Yes/No. The live test encountered and handled a periodic save reminder before editing.

Run `node --test desktop/dialux-session.test.mjs` for state-consumption and selection tests. These use a fake client and do not prove live input succeeds. Successful calls are not enough: verify visible completion plus saved files or exported results. The original native project's hash in `live-validation-artifacts.json` identifies the earlier gate checkpoint; subsequent save tests can change that local project's bytes.
