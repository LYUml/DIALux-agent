# Calculation checkpoints

`calculation-checkpoint --expected-project <copy.evo> --evidence-directory <new-directory> --checks <checks.json> [--recalculate]` / MCP `calculation_checkpoint` performs one explicit iteration checkpoint. It does not design or optimize the layout.

A check is `{ "summary_id": "<identity from report-read-all>", "profile": { ... }, "context": { ... } }`; context is optional. Supply 1–100 checks with unique summary IDs, combining criteria in one profile per selected summary. Criteria and applicability remain explicitly supplied; native DIALux preset targets are not substituted.

The workflow validates inputs, creates a new evidence directory, and persists pending intent before each native step:

1. Invoke native calculation; `--recalculate` explicitly permits clearing cached results.
2. Export a new `report.pdf` using the native export backend.
3. Parse all supported room/scene summary pairs and select each requested identity exactly.
4. Evaluate only that room's measurements with its supplied profile/context.
5. Save the expected native project, even when criteria fail or remain unverified, preserving the calculated experiment for inspection.

The journal contains requests, ordered operation results, exported PDF identity, assessments and final native save evidence. A failed operation records its stage, stops subsequent steps and is never retried. An existing evidence directory is refused. Failure can leave unsaved native changes; inspect the journal and application before further action. Use a separate test copy when source preservation is required. Desktop mutations must not run concurrently.

The returned decision is `selected_conditions_met`, `selected_conditions_not_met`, or `evidence_incomplete`. CLI exit codes are respectively 0, 1 and 3; operational errors return 2. `state: completed` means the checkpoint workflow completed, not that its criteria passed. Whole-project assessment remains false. The function does not exclude external UI edits or authenticate project/report origin, and does not prove geometry correctness, report coverage or regulatory certification.

This supplies a stopping decision for callers performing iterations; no automatic geometry search, retry, rollback or unbounded optimization loop is implemented.

## Native regression checkpoint

The first real three-room run (`local/calculation-checkpoint-v1`) stopped at `pending_calculate`: DIALux had completed calculation, but Output mode hid monitor rows and the old backend could not observe completion within 45 seconds. The journal recorded failure and no export or save was attempted. Subsequent live inspection found idle calculation controls and all three room result rows; no solver restart was used to diagnose the timeout.

Calculation preparation now selects the native lighting tool and ensures the results-monitor panel is present. In the observed dock layout the ResultsMonitorTool TabItem reports hidden even while its result rows are visible, so tab visibility is not used as the panel's open/closed test. Tests cover already-open and closed panels. A fresh regression run starts explicitly from native Output mode, uses a separate evidence directory, and requests recalculation to test this fix.

The repaired public CLI regression completed all four recorded operations in `local/calculation-checkpoint-v2/journal.json`: calculate, export, read_report and save. Export/read agree on PDF SHA256 `4fd4158c6322fa1ae0a90ac7d7a88f1f620b25123aede6f7b6324e453fec166d`; the final saved native project SHA256 is `0151f175ca7131c14b0498f9178c8d7c7a0920874fbdc31cb38f17ad519abcf3`. Synthetic B was checked against the sourced HK BEC office-LPD profile without applicability context, deliberately producing `completed` plus `unverified` / `evidence_incomplete`. This is the expected absence-of-evidence outcome, not a passed design. The original failed-run journal remains intact. The checkpoint has 225 passing tests, including CLI decision exit codes and MCP discovery.
