# Mixed-product observed CAD

CLI `drawing-export-mixed --request request.json` and MCP `export_mixed_scheduled_layout_dxf` reuse the observed-layout validator, mixed report schedule linker, CAD renderer, label placement, native round-trip checker and fixed-scale plotter.

The request contains `spec`, `groups`, `report_request`, `alignment` and `output`. The common `spec` holds metre units, active-storey frame, contour, exclusions, clearance, assumptions and optional annotations/dimensions/sheet. It must not contain a single global `fixture`. Each group supplies `report_group`, `fixture` (product identifier, width/depth/mounting height), `observed` and `fixture_ids`. The report request and alignment follow [mixed schedule](mixed-product-schedule.md).

Each group receives a distinct CAD block, with dimensions from its explicit fixture definition. The label placer uses each fixture's own rotated footprint. Every group is validated against the room/exclusions, then cross-group envelope overlaps are rejected. The mixed schedule additionally checks group coverage, drawing-ID uniqueness and report position correspondence. Total supported fixtures are bounded to 2000.

Tables include symbol samples, type labels, article/description, installation height, drawing IDs, quantities and reported power/flux. They are laid out in two columns using actual entity extents. Symbols are generic rectangles with diagonals, not manufacturer geometry. Equal footprints can look identical; explicit drawing IDs associate them with the product tables. Native verification checks separate block associations and internal shapes as well as schedule text/lines. General multi-page composition, arbitrary manufacturer symbols and complete annotation collision analysis remain unsupported.

## Fixed-scale plot labels

Because schedules repeat fixture IDs, fixed-scale plotting now checks fixture labels **inside the independently verified PDF room outline**. References outside that polygon do not substitute for missing drawing labels. Duplicate/unknown labels or labels whose word boxes cross the outline are rejected. Fit-to-page plotting retains its conservative whole-page uniqueness check; use explicit fixed scale for these mixed schedule sheets. This is scoped label coverage, not proof that all native project content was exported.

## Native synthetic checkpoint, 2026-11-09

The five observed fixtures and two report products from the [mixed native case](mixed-product-report-reading.md) were exported through the public CLI. The final sheet is A3 landscape at 1:50, with two symbol blocks and two side-by-side product tables. It passed native AutoCAD save/reopen including both block shapes, product/block association, fixture labels, schedule entities and sheet entities. Native PDF output passed the paper-size check, vector-outline physical-scale check, scoped five-ID check and paper-edge check. The final preview was visually inspected: plan, notes, both tables and titleblock are present and legible, with no observed clipping or overlap.

- DXF SHA-256: `5f23ee3bdcf5e9a0da756a36832e53af426d90ba3847db8982da404d8bae3401`.
- DWG SHA-256: `72be115337c5d1bbbe37cb19061d426f20673a05f69efd687325a030ab74328e`.
- PDF SHA-256: `7cf33f51905536d5c5077ec1cb300de7f31b119c22561a807f29e5b9010d1f8d`.

Local evidence under `local/mixed-products-native-v1`: `mixed-cad-request-v4.json`, `mixed-cad-result-v4.json`, `cad-native-v4/manifest.json`, `cad-plot-v5/manifest.json`, and `cad-plot-v5/preview.png`. The earlier A2 plot rejection caused by repeated table IDs is retained under `cad-plot-v2`; it is not marked successful. A3 public-CLI execution is also retained in request/CLI result v3; v4 has the same geometry with clearer type captions.

The native case uses two supplied 0.597 m square envelopes. Unit tests separately check two different rectangular dimensions, per-product label avoidance, input preservation, overlaps, invalid dimensions, incomplete observations, duplicate IDs and missing assumptions. The complete suite passed 520 tests; the final caption/limit adjustments additionally passed all 15 targeted mixed-CAD/schedule/plot-label tests. No assignment artifacts were produced, and physical dimensions remain supplied assumptions.

## Differing-envelope renderer stress test

A separate synthetic drawing retained the five observed positions and report associations but deliberately changed the second symbol envelope to **1.2 × 0.3 m**, alongside the first group's 0.597 × 0.597 m envelope. This rectangle is invented test geometry, **not the reported Philips product's body**; no DIALux model or photometry file was changed. The sheet title explicitly says it is a differing-envelope test, not product dimensions. Mixed tables now print each supplied symbol envelope size.

Both differently sized block definitions survived native DWG reopening, including the full polyline/diagonal dimensions and ID definitions. The A3 1:50 PDF contained both envelope-size strings, all five in-room labels and both tables. Its rendered preview was inspected; the wider shallow symbol, matching legend and clear fixture label were visible without clipping. This proves renderer/round-trip handling of these two supplied shapes, not physical-product authentication.

Evidence: `local/mixed-products-native-v1/different-envelope-v2/{request.json,export.json,native/manifest.json,plot/manifest.json,plot/preview.png}`. Source DXF SHA-256 `675fa2cbc64c6ca880955846b3aaf7d44e8f269bb7ff5154326a77dee7a3244a`; native DWG `de41c817ab890b41e3a7cbb4f899a21bda0f90a92310ea3a056f3d7bc0965147`; PDF `9a21c4df3d386387c7eec0015da8f13883c86546a3720732af7bf2fa93c020fe`. All ten targeted mixed-CAD/schedule tests passed after adding explicit envelope text.
