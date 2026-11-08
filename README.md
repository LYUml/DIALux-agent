# DIALux-agent

Experimental Windows tooling for DIALux evo, driven by the BSE3125 lighting-design workflow. Development precedes assignment production.

## Current capabilities

`python src/dialux_agent.py inventory --source <assignment-folder>` hashes PDF/DWG inputs without modifying them and reports the DWG header. `verify --manifest <json>` checks that originals remain unchanged. Both commands emit JSON and nonzero exit codes on failure.

Live DIALux control and calculation are not implemented yet. A previous desktop probe reached evo 14.1's login screen and exposed UI Automation IDs; project editing and simulation are unverified. This is not a completed CLI-Anything harness.

Upstream research checkouts are local-only under `upstream/`: https://github.com/MarcosCastanedaVentura/MCP_Dialux and https://github.com/HKUDS/CLI-Anything. Their code has not been incorporated into this package.

Commit convention: `YYYY-MM-DD English change description`, matching polyu_bse3124. Do not publish assignment originals, credentials, logs containing personal data, or generated local projects.
