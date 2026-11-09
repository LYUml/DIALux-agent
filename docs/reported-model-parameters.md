# Reported model parameters

CLI `report-model-parameters --request <json>` and MCP `read_model_parameters`
accept `path` and an exact `summary_id` discovered through `report-read-all`.
The reader reuses the existing complete, adjacent English Summary-pair parser
and binds all values to one room/scene, source page and PDF SHA-256.

Returned parameters: ceiling/wall/floor reflection percentages, explicitly fixed
maintenance factor, mounting height, working-plane wall zone, ground area,
clearance height and working-plane height. Values are those rounded in the report.
Missing/duplicate fields, unknown summary IDs, out-of-range reflectances and
unsupported maintenance modes are rejected. No defaults are substituted.

The summary's wall value is not proof of each wall's material; mounting height is
not proof of every fixture's Z. Live settings, calculation freshness and
individual surface materials remain explicitly unverified. This reader does not
compare a design specification, infer applicability or declare compliance.

Ten focused tests use deliberately different synthetic values (72/46/18 percent,
maintenance 0.76) and reject missing/ambiguous/invalid fields and wrong scopes.
The main CLI also read the native mixed-product synthetic report, SHA-256
`0460dfefe9bf1ea397be1cfc8da8f82f0835beaeb6818b8d36f42f644e482fcf`,
summary `3837d1f7d66cf857a136131a7287babde530ed18370c4d0be3fc09252c7b6d7d`.
Page 15 was rendered and visually checked: 70/50/20%, fixed 0.80, mounting
height 3.035 m, workplane 0.8 m, wall zone 0 m, room height 3 m and area 24 m².
This is tool-validation evidence, not an assignment design.

A real stdio MCP client also called `read_model_parameters` against that native
report and verified the same values. Its local result is retained as
`local/model-parameters-mcp-result.json`. This checks the transport and backend
with actual PDF bytes; it does not upgrade freshness or per-surface claims.

## Explicit expected-parameter comparison

CLI `report-check-model-parameters --request request.json` and MCP
`check_model_parameters` accept `path`, `summary_id`, `expected_sha256` and
`expectations`. Expectations must contain all nine fields listed above using
their returned parameter keys; each entry is `{ "value": number,
"absolute_tolerance": nonnegative_number }`. There are no inferred criteria or
default rounding tolerances. Reflection factors use percent, heights/zones use
metres, area uses square metres, and maintenance factor is dimensionless.

The result includes every reported/expected value, error, tolerance and match
decision. Inspect `all_reported_parameters_match`; successful command execution
alone does not mean a match. Wrong source hashes and incomplete or invalid
expectations are rejected. It still does not verify live state, individual surface
materials, fresh calculation or engineering suitability.

The native report above passed all nine exact comparisons through both CLI and
real stdio MCP. A deliberate expected maintenance factor of 0.70 produced exactly
one mismatch against reported 0.80. Requests/results are retained under
`local/model-parameter-check-v1`. Nineteen focused tests cover each parameter's
mismatch, tolerance boundary, missing fields, bad numbers and stale hashes.
