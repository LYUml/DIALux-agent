# Hong Kong BEC 2024 office LPD module

`resources/profiles/hk-bec2024-office-lpd.json` implements the three office rows of Table 5.4, with conditions derived from clauses 5.1 and 5.4.1–5.4.3. The official source PDF hash, printed/PDF pages and extraction review are embedded. `verified` means the extraction was checked against the source, not that a building has been certified.

This module evaluates one single-function office space at a time. The measurement must use `lighting_power_density`, `W/m2` and calculation surface `space`. Supply an evidenced context using these fields:

| Fact | Required meaning |
|---|---|
| `design_code` | `BEC 2024`, with evidence why this edition applies |
| `bec_section5_scope_confirmed` | Boolean; review prescribed-building/installations scope and exclusions |
| `space_use` | `office`, supported by the actual brief or plan |
| `single_function_space` | Boolean; multifunction combinations are outside this module |
| `space_boundary_5_4_3_reviewed` | Boolean; floor-to-ceiling divisions treated correctly |
| `lpd_power_basis_5_4_2_reviewed` | Boolean; included/excluded loads resolved, no unresolved manufacturer power discrepancy |
| `internal_area` | Positive number, unit `m2`, measured from the same space |
| `complete_fixed_lighting_power` | Number, unit `W`, used for the clause 5.4.1 exception |
| `enclosed` | Boolean; small-office classification requires enclosure |

Every fact is `{ "value": ..., "evidence": "..." }`, plus `unit` for numeric facts. Missing facts remain unverified. The generic engine conservatively checks all conditions, so include enclosure evidence for larger rooms too. Never fill a review boolean merely to obtain a pass. The caller must reconcile the supplied LPD with the same area, loads and operating basis; no power-basis reconstruction is performed here.

Run `criteria-check --profile resources/profiles/hk-bec2024-office-lpd.json --measurements <measurements.json> --context <context.json>`. All paths can be absolute. Numeric `measurement_min: 0` prevents impossible negative LPD values from passing.

Lighting controls, illuminance, uniformity, glare, emergency lighting, other occupancies, energy estimation, and whole-building BEC compliance are not covered by this module. The separate 70 W LPD exception is not an automatic-control exception. If every band is inapplicable, the aggregate stays unverified; this is not a statement that the installation fails or complies.

The local one-luminaire validation scene is not claimed compliant: it is synthetic, has an unresolved manufacturer power discrepancy and has no evidenced project-specific code applicability. Tests verify band boundaries and exception handling using explicitly synthetic facts, not the assignment.
