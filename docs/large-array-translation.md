# Native 168-fixture regular-array translation

Synthetic agent test, 2026-11-09; not an assignment design or compliance assessment.
Independent CLI/MCP desktop functions operated DIALux evo 14.1 without Codex Computer Use.

The original 30 × 34 m synthetic project contains a 14 × 12 native array.
`desktop_read_arrangement` read the counts and centre (15, 17, 3.035) m.
`desktop_edit_arrangement` atomically replaced centre X/Y with 15.1/17.1 m.
A complete persistent inspection read all 168 individual fixtures across 42
hashed pages. Offline verification matched the intended translated grid,
including rotation; maximum coordinate rounding error was approximately 0.000429 m.
This proves regular-array translation, not arbitrary individual rearrangement.

`calculation-checkpoint --recalculate` performed a fresh native calculation,
exported the report and saved the project. Report coordinates for all 168 fixtures
matched the individual UI readings. WP1 reported 510 lx average and 0.39 uniformity;
space LPD was 4.28 W/m². The checkpoint's positive-illuminance smoke-test condition
is deliberately synthetic and is not a lighting design standard.

Closing and reopening the saved project, then independently exporting its stored
report, preserved every reported fixture position, product record and selected
summary measurement. Both the saved project and original source hashes remained
unchanged. This persistence check does not constitute a second fresh calculation
or a second full UI inventory. Documentation-session changes were saved separately.

## Local evidence

Ignored local artifacts are retained on the verification machine; hashes identify
them but do not make them downloadable from the public repository.

| Artifact | SHA-256 |
| --- | --- |
| Original `local/large-native-v1.evo` | `68be0e4bee9cad65132b3ff76841414496c2bdf7ecf133940d538f6ef22218b9` |
| Full UI observations `local/large-array-inspection-v1/observed.json` | `cb7e4b2d9f73a70d62914547055f56ea9012c01ae3ca945cdef572a602a911b6` |
| Calculated `local/large-array-probe-v1.evo` | `d1160ab4de37eff2e798e1ae835761092bb838af2e5c5472ad8e4f2e9542ba4a` |
| Fresh report `local/large-array-calculation-v1/report.pdf` | `b8f8592b917703a60ee90970e09cc9ae0eea9349b0a98ee2068eff7ba6bd9d78` |
| Reopened report `local/large-array-reopen-v1/reopened.pdf` | `1c6a2c5e1fe3b13144ab460428d523c8283ed42cbfbb3dfcbe5fead32e1387be` |

Journals: `local/large-array-inspection-v1/journal.json`,
`local/large-array-calculation-v1/journal.json`, and
`local/large-array-reopen-v1/journal.json`. Offline verification is recorded in
`local/large-array-verification-v1.json`. The earlier failed 168-fixture individual
movement and partial-write recovery evidence remain separate and unaccepted.

Regression suite at this checkpoint: 387 tests passed. Unit tests alone do not
establish native support beyond the observed case.
