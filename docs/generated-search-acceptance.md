# Generated offset search: native four-candidate acceptance

2026-11-09, synthetic six-fixture obstacle room only. Public independent CLI:

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent layout-offset-search --request local/offset-search-native-request-v4.json
```

The run completed with exit 0 using execution code at `f5f5019`. Existing execution
files were held unchanged and checked against a pre-run SHA256 snapshot before
subsequent CLI development. Separate documentation and an unrelated optional HK
profile were added during the run; its embedded checks were unchanged.

The explicit domain used X offsets [0, 0.1, 2] m and Y offsets [0, 0.1] m. The
2 m offset equals one grid spacing and produced two duplicate physical grids.
All four distinct same-count candidates were retained and actually simulated.

| Candidate index | Offset X/Y (m) | Fresh WP1 Uo | Complete UI/report position match | Reopen comparison |
| --- | --- | --- | --- | --- |
| 0 | 0 / 0 | 0.060 | All six | Passed |
| 1 | 0 / 0.1 | 0.060 | All six | Passed |
| 2 | 0.1 / 0 | 0.066 | All six | Passed |
| 3 | 0.1 / 0.1 | 0.062 | All six | Passed |

The runner selected index 2 for the supplied maximize-Uo objective and stopped
with `candidate_list_exhausted`. Its criteria were explicitly synthetic positive-
illuminance smoke checks, not design or compliance thresholds. A higher Uo here
does not imply an acceptable lighting design. The runner did not install a winner.

## Independent checks

`local/offset-search-native-v4/independent-audit.json` re-generated the supplied
candidate domain, checked request/generation hashes, all candidate plans, complete
hashed before/after pages and unique fixture identities. It compared every final
UI coordinate with each newly exported native PDF, verified the saved project
hashes and independently recomputed objective values and the best index.

`reopen-check/journal.json` records separately closing/opening each candidate and
exporting another native report. All fixture coordinates, reported product records
and selected summary metrics matched. Original source and candidate hashes were
unchanged. Documentation-session changes were saved to separate copies, which were
then closed; the persistence worker exited 0. Artifact hashes are retained in
[the evidence index](evidence/generated-search-v4.json).

Earlier v1/v2/v3 failures remain retained and are not relabelled as successful.
The [notification investigation](desktop-notification-transitions.md) explains
the later bounded wait change without asserting a universal cause or cure.

## Acceptance boundary

This accepts the supplied four-candidate domain in this synthetic project on the
tested installation. It does not verify a global optimum, arbitrary fixture count
or product search, other stop-policy branches natively, general interruption
recovery, every room/scene or an assignment design. Native rotation and guarded
reusable bulk-array application remain separate gates.
