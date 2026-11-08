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

`calculate(observed)` is implemented using the observed CalculationButtonStart control but is **not yet live-verified through this module**. The earlier real calculation was direct agent-controlled Computer Use. No import, placement or export methods are implemented in this adapter yet. The Python MCP does not host this module: AI uses the MCP for file/result operations and the desktop skill for these session operations. A standalone unattended CLI/MCP driver remains unfinished.

Run `node --test desktop/dialux-session.test.mjs` for state-consumption and selection tests. These use a fake client and do not prove live input succeeds. Successful calls are not enough: verify visible completion plus saved files or exported results. The original native project's hash in `live-validation-artifacts.json` identifies the earlier gate checkpoint; subsequent save tests can change that local project's bytes.
