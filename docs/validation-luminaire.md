# Real luminaire prepared for the live gate

Retrieved 2026-11-08 from [Signify Hong Kong's product page](https://www.signify.com/en-hk/prof/indoor-luminaires/recessed/philips-coreline-panel-gen6/910505102817_EU/product): Philips RC132V G6 36S/840 PSD W60L60 OC ELB3, order code 910505102817. This is a **test candidate**, not the final assignment selection or confirmation of local stock.

Original IES, LDT and ULD files are cached under ignored `local/luminaires/`. Exact download URLs, hashes and sizes are in `examples/validation-luminaire.assets.json`. The IES starts with LM-63-2002, the LDT identifies the same product code, and the ULD has an OLE compound-file signature. These are format-identification checks, not evidence of DIALux compatibility. Manufacturer files are not redistributed in this repository.

The [manufacturer fact sheet](https://www.docs.signify.com/assets/Leaflet/Philips_PROF/FP/en_HK/910505102817_EU.en_HK.PROF.FP.pdf), dated 27 October 2026, is cached beside them. Its nominal normal-operation figures are 3600 lm and 27 W, while the retrieved IES lists 3609 lm and 26 W. LDT also contains a second emergency lamp set, with 333 lm and 1 W; the current fact sheet instead lists 250 lm emergency flux and 2 W central-DC emergency power, plus additional charging consumption. These fields may represent different conditions or revisions: the discrepancy is **unresolved**, and must not be silently normalized. Do not use this candidate for a compliance conclusion until the selected operating mode, power basis and dataset are reconciled.

## Live verification sequence

When shared-desktop time is available:

1. Import the versioned synthetic room STF into a new empty project. Confirm dimensions, workplane, reflectances and maintenance factor in evo; record actual values.
2. Import the original ULD. Inspect product identity and each operating/photometric mode. Prefer the full manufacturer ULD for the first attempt; IES/LDT are alternatives, not interchangeable evidence.
3. Select normal operation explicitly. Record the flux, input power, dimensions and orientation evo actually uses. Preserve screenshots and the original files' hashes.
4. Place one luminaire at room centre, then calculate. Record the real workplane result, calculation status and warning messages. Do not expect a predetermined lux result or use this one-luminaire scene as a design recommendation.
5. Save a new native evo project under `local/`, reopen it, and confirm luminaire identity and calculation results persist.
6. Export the calculation documentation to PDF. Check its room, luminaire count, photometry, maintenance factor and result values against the application. Record hashes of the saved project and report.
7. Only after this gate works, test placement automation and multiple fixtures. A product's catalogue UGR label is not a calculated room UGR result.

Current status: manufacturer assets downloaded; no import, calculation or native save has been verified. No desktop input was performed to prepare these assets.
