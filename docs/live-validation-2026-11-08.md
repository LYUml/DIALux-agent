# First real DIALux calculation gate

On 2026-11-08, after the user authorized shared-mouse operation, the agent performed this sequence in installed DIALux evo 14.1 (64-bit) using the computer-use skill:

1. File > Import > STF file: imported `local/adapter-room-v1.stf` into an empty application workspace.
2. Selected the imported room in Spaces. The UI showed height 3.000 m and workplane 0.800 m.
3. File > Import > Luminaire file: loaded the original Signify ULD `local/luminaires/910505102817.uld`.
4. Placed one real Philips 910505102817 luminaire using the individual-placement tool. Observed placement coordinates were X=2.800, Y=2.000, Z=3.035 m. An attempted accessibility edit to X timed out; do not claim the light was set exactly to X=3.000. The exported plan shows the light slightly off centre.
5. Ran Calculation. The room became illuminated and real calculated documentation was available.
6. Saved `local/adapter-room-v1.evo`, generated the room Summary documentation and exported its two pages to `local/validation-summary-v1.pdf`.
7. Saved again after documentation settings, closed the project via File > Close, reopened it from project history, and navigated to Summary page 2. The same average illuminance, uniformity and LPD were present without recalculating.

## Observed evidence

The exported PDF was text-extracted and page 1 rendered for visual comparison with the application preview. The re-opened application's page 2 showed the same result table.

| Field | Observed value |
|---|---|
| Room dimensions / area | 6.000 x 4.000 m / 24.00 m2 |
| Clearance height / workplane | 3.000 m / 0.800 m |
| Ceiling / wall / floor reflectance | 70 / 50 / 20 percent |
| Maintenance factor / wall zone | 0.80 fixed / 0.000 m |
| Luminaire | 1 x Philips RC132V G6 36S/840 PSD W60L60 OC ELB3, 910505102817 |
| Luminaire power / luminous flux | 26.0 W / 3602 lm |
| Mounting height | 3.035 m, ceiling recessed |
| Workplane average perpendicular illuminance | 104 lx |
| Workplane uniformity Uo | 0.20 |
| Reported glare valuation RUG,max | 16; report qualifies rectangular room and SHR 0.25 |
| LPD | 1.08 W/m2 |

The report's 500 lx / 0.60 targets belong to DIALux presetting 34.2 Standard (office), not an adopted Hong Kong rule pack. Both checks fail in this deliberately single-luminaire test. Energy estimation uses DIN 18599-4; it is not a Hong Kong energy assessment. The manufacturer's differing product-sheet values remain unresolved; see `validation-luminaire.md`.

Hashes and byte sizes are in `live-validation-artifacts.json`. The actual native project, manufacturer asset and PDF stay local and ignored by Git. A title bar alone was not accepted as save evidence: the file exists, and the project was closed and reopened successfully.

## What this proves and what remains

This proves a real end-to-end route from the current STF serializer through evo import, manufacturer ULD import, placement, calculation, native save/reopen, and PDF export for one synthetic room. It does not prove unattended CLI/MCP desktop control, repeatability across display configurations, bulk fixture placement, assignment geometry, or regulatory compliance.

The current CLI/MCP still performs file preparation and criteria evaluation only. UI actions in this gate were agent-directed computer use. Accessibility snapshots sometimes lagged the screenshot, filename focus metadata incorrectly reported the search box, and a hidden/offscreen numeric edit timed out. Reliable automation must refresh state, verify visible results, and avoid treating successful input calls as proof of mutation. Do not encode the screen coordinates from this run as a portable driver.
