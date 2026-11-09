# Mixed-product native report sections

`report-arrangements-read --request request.json` and MCP `read_report_arrangements` read explicitly selected English **field-arrangement** sections. They reuse the existing coordinate-table reader, while retaining the product and group for each coordinate. The single-product `report-layout-read` interface remains unchanged.

The request contains `path`, `expected_header`, `expected_count`, and `sections`. Each section supplies `first_page`, `last_page`, `expected_count`, `expected_group` and `expected_article_number`. Page numbers are one-based. The parser requires exact room headers, nonoverlapping page ranges, unique group/arrangement identities, positive reported power/flux, and native X/Y field counts matching the declared quantity. All sections together must provide each room-wide number from 1 to the declared total exactly once. Page order need not match number order. An unexpected product on a continuation page is rejected.

A result proves coverage of the **declared sections**, not discovery of every fixture or room in the project. It does not infer a coordinate transform, rotation, live runtime identity, fresh simulation, manufacturer dimensions or compliance. Other arrangement types, several tables on one page and other languages are unsupported. Native validation below covers one page per section; longer field-arrangement sections remain a native acceptance gap.

## Native synthetic case, 2026-11-09

The independent desktop worker added `MixedSecondary` with the imported RC132V G6 43S/840 SIA W60L60 OC IA4 ULD to the saved synthetic obstacle room. The singleton room-context fallback was required. Creation returned `created_unverified`; separate full group inspections then verified four original fixtures at X=1.5/4.5, Y=1/3 and one new fixture at (3,1), all Z=3.035 m. Before/after original-group observations matched. Assumed 0.597 m square envelopes passed containment, exclusion and mutual overlap checks; this is not manufacturer-dimension authentication.

The fresh native calculation report contains an overview on page 17, the secondary product on page 18 (number 5, article 910505102802, 32 W, reported 4303 lm), and the primary product on page 19 (numbers 1–4, article 910505102817, 26 W, 3602 lm). Both rendered product pages were inspected. All five parsed XYZ positions matched the independently inspected UI positions by group. The new product's reported flux is retained as 4303 lm; it is not replaced by the marketing value or another photometry file's value.

- Native file SHA-256: `0874aab47bd3fdecc2d0ee8f136546b97df1eaa909c49912024fb103ab58b218`.
- Fresh report SHA-256: `0460dfefe9bf1ea397be1cfc8da8f82f0835beaeb6818b8d36f42f644e482fcf`.
- Original synthetic source SHA-256 remained `9007f05d9f063de6828d93818f15ae3c7fc7f2abdf316e331453cdff74291d27`.

Local evidence: `local/mixed-products-native-v1/creation-v2/journal.json`, `continuation-journal.json`, full `primary-after` / `secondary-after` checkpoints, `calculation/report.pdf`, `arrangements-request.json` and `parsed-arrangements.json`. The first failed creation journal is retained; it stopped before placement and was inspected before the explicit continuation.

The native calculation used synthetic positive-illuminance smoke criteria only. Save/reopen persistence subsequently passed as described below. Mixed-product CAD symbols/tables and varying-product optimization remain unverified. Position-linked mixed schedule data is available; see [mixed-product schedule](mixed-product-schedule.md). No assignment design was made. Full suite: 486 tests passed, including ambiguity/coverage rejection and actual MCP discovery; the public CLI also read this native report successfully.

## Save/reopen persistence

The independent worker closed and reopened the saved native file, re-inspected both groups completely, and verified all five XYZ positions, rotations and names against the pre-save observations. A fresh export matched both product sections, every report coordinate and all parsed scoped summary measurements. The native hash remained unchanged. Reopened report SHA-256: `93268dd86653b90fc6802c1c199968d6cf43f6bdd1470fea9d35dc3156c0493e`. The source hash also remained unchanged. `local/mixed-products-native-v1/reopen-v1/journal.json` ended `verified`; hashed UI checkpoint pages are retained there. Documentation-session changes were saved to a separate copy and closed. This is a two-group synthetic persistence check, not whole-project or assignment acceptance.
