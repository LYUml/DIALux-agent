# Hong Kong office automatic-control numerical checks

`profiles/hk-bec2024-office-automatic-control.json` is an optional module for one
explicitly mapped office control zone. It reuses the region-independent evaluator;
no DIALux geometry, calculation or controller settings are changed.

Source: EMSD [BEC 2024](https://www.emsd.gov.hk/beeo/en/pee/BEC_2024_ENG.pdf),
clauses 5.6.1.1, 5.6.1.3(a), 5.6.1.4–5.6.1.6, printed pages 18–19 / PDF pages
24–25. Extracted text and both rendered pages were reviewed on 2026-11-09. A fresh
download matched the cached SHA256
`9fae5eb2134caa7f5645735d618d82da0cf3f284e576a9f6402de9b8357f95b7`.
The profile's verified label refers to this extraction, not project certification.

## Input contract

Each context fact needs a value and nonempty evidence. Numeric facts also need
the stated unit. Required scope:

| Fact | Value |
| --- | --- |
| `design_code` | `BEC 2024` |
| `bec_section5_scope_confirmed` | true |
| `space_use` | `office` |
| `automatic_control_required_reviewed` | true, with applicable Table 5.4 classification |
| `occupied_24_hours_7_days` | false |
| `control_zone_mapping_reviewed` | true, identifying the selected zone |
| `control_zone_nonempty_reviewed` | true, with its actual nonzero boundary/load |
| `complete_fixed_lighting_power` | greater than 150, unit `W`; complete space load, not selected-zone load |
| `occupant_sensors_deployed` | evidenced true or false |
| `manual_override_installed` | evidenced true or false |

Evaluate each zone separately. Use `calculation_surface: selected_control_zone`
on the measurements; this is a semantic key, not an inferred DIALux WP identifier.

| Metric | Unit | Check | Additional applicability |
| --- | --- | --- | --- |
| `automatic_control_remaining_power_percent` | `%` | ≤50 | Remaining general-lighting power after automatic action, relative to the same zone's baseline; not illuminance or dimmer-position percentage |
| `automatic_controlled_area` | `m2` | ≤250 | Selected automatic-control area |
| `occupancy_reduction_delay` | `min` | ≤15 | Occupant sensors deployed; delay after all occupants leave |
| `manual_override_duration` | `min` | ≤120 | Manual override installed; duration per activation |
| `manual_override_controlled_area` | `m2` | ≤250 | Manual override installed |

Supply control-design, device-configuration or commissioning evidence and identify
whether a value is proposed or measured. DIALux illumination/LPD reports do not
establish these functions. Negative inputs are unverified. Missing optional-device
facts remain unverified; evidenced absence skips only those device-specific checks.

## Limits and separate requirements

This module does not establish that a control exists, cover every zone, check
floor-sharing/weekend/holiday logic, count manual control points, or assess daylight
controls. Other space types and exceptions require their own review. An excluded
scope returns no passing assessment; it is not a whole-installation exemption.

EMSD's [lighting FAQ, answer 1](https://www.emsd.gov.hk/beeo/en/mibec_faq_lighting_a.html)
explicitly separates sections 5.5 and 5.6: automatic sensors/timers cannot substitute
for lighting control points. This module must not be used as a Table 5.5 assessment.

## Synthetic reproducible check

```powershell
.\.venv\Scripts\python.exe -m src.dialux_agent criteria-check --profile profiles/hk-bec2024-office-automatic-control.json --measurements examples/synthetic-control-measurements.json --context examples/synthetic-control-context.json
```

The supplied examples are fabricated **test inputs**, clearly labelled in every
evidence field; they are not installation evidence or an assignment control scheme.
Their exact-boundary values should pass only these five scoped criteria.
Tests also cover excess limits, the 150 W boundary, absent scope, other editions/
occupancies/uses, optional-device absence and invalid measurement units/surfaces.
