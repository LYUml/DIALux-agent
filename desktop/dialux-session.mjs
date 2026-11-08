/** DIALux-specific actions over an injected, existing Computer Use sky client.
 * Run in node_repl after reading the installed computer-use skill.
 * Each observation is consumed by one action. The caller inspects it first.
 */
export class DialuxSession {
  #sky;
  #window;
  #observation;
  constructor(sky) { this.#sky = sky; }

  async connect() {
    this.#observation = null;
    this.#window = null;
    const windows = (await this.#sky.list_windows()).filter(w =>
      /[\\/]DIALux_x64\.exe$/i.test(w.app));
    if (windows.length !== 1) throw new Error(`Expected one DIALux window; found ${windows.length}`);
    this.#window = await this.#sky.get_window({id: windows[0].id, app: windows[0].app});
    await this.#sky.activate_window({window: this.#window});
    return this.observe();
  }

  async observe() {
    this.#observation = null;
    if (!this.#window) throw new Error('Connect to DIALux first');
    const state = await this.#sky.get_window_state({window: this.#window,
      include_screenshot: true, include_text: true});
    this.#window = state.window;
    this.#observation = state;
    return state;
  }

  async #invoke(observation, automationId) {
    if (!observation || observation !== this.#observation)
      throw new Error('Stale observation; observe and inspect before acting');
    // Consume even when input fails: never retry a mutation with an old snapshot.
    this.#observation = null;
    const tree = observation.accessibility?.tree;
    if (!tree) throw new Error('No accessibility snapshot; observe again');
    const lines = tree.split('\n');
    // The helper may append foreign windows. Never select a control from those.
    let skippingWindow = false;
    const own = lines.filter(line => {
      const depth = line.match(/^\t*/)[0].length;
      if (skippingWindow && depth <= 2) skippingWindow = false;
      if (/^\t\t\d+ window /.test(line)) skippingWindow = true;
      return !skippingWindow;
    });
    if (own.some(l => /\bdialog\b/.test(l))) throw new Error('Modal dialog requires inspection');
    const matches = own.filter(l => l.endsWith(` ID: ${automationId}`) && /\bbutton\b/.test(l));
    if (matches.length !== 1 || matches[0].includes('(disabled)'))
      throw new Error(`Expected one enabled ${automationId} button`);
    const index = Number(matches[0].trim().match(/^\d+/)?.[0]);
    if (!Number.isInteger(index)) throw new Error('Invalid observed control index');
    if (automationId === 'Save') {
      // DIALux's observed File menu exposes Ctrl+S. The helper can return IDs
      // which it then cannot click; use the app shortcut after checking state.
      await this.#sky.press_key({window: observation.window, key: 'Control_L+s'});
    } else {
      await this.#sky.click({window: observation.window, element_index: index});
    }
    // Returned state is evidence for the caller; a click is not proof of success.
    return this.observe();
  }

  save(observation) { return this.#invoke(observation, 'Save'); }
  calculate(observation) { return this.#invoke(observation, 'CalculationButtonStart'); }
}
