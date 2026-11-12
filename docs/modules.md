# Replaceable modules

The domain boundaries are independent of country:

- Geometry/photometry adapters: source formats, units, fixture identities and geometry; reuse licensed upstream parsers.
- DIALux execution: independent Windows pywinauto worker, shared by CLI and MCP. A fresh-process single-room import/placement/calculation/save/export/reopen run is verified; see acceptance-2026-11-09.md. The earlier Computer Use adapter is historical research.
- Result adapters: normalize measured values, units, calculation surfaces and artifact evidence.
- Regulations: region-independent evaluator consumes versioned criteria profiles. No thresholds embedded in evaluator code.
- Reporting: compares evidence-backed results and produces reviewable outputs; independent from rules and simulation.

First jurisdiction: Hong Kong. `resources/profiles/hk-office.template.json` is deliberately unverified and empty until actual source editions/clauses are reviewed. International lighting guidance, Hong Kong energy requirements and assignment-specific requirements should be distinct profiles. Users select the applicable profile set; conflicting requirements must be reported rather than silently overwritten.

Each criterion carries a stable ID, metric, unit, comparator, threshold, calculation surface and complete source citation. Each measurement carries metric, unit, value, surface and artifact evidence. Unit or surface mismatch, missing sources, missing results and duplicate matching measurements produce `unverified`, never a pass. A verified flag records review; it does not itself prove the source or measurements are authentic.

Future jurisdiction packs use the same schema. New calculation metrics can use result-adapter plugins without changing geometry or desktop control. The evaluator supports numeric comparisons and tested evidence-bearing conjunctive applicability conditions. Complex formulas are not implemented. `workflow.check_report` joins PDF evidence to a supplied profile without embedding regional thresholds. The Hong Kong energy and occupational-advice profiles remain separate.
