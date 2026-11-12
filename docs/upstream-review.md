# Upstream reuse review

## Incorporated

MCP_Dialux — https://github.com/MarcosCastanedaVentura/MCP_Dialux

Pinned commit: 4489032e67cabe0d409819fad24f091128620a9d. MIT, copyright Marcos Castañeda. Unmodified `dialux/` sources and LICENSE copied to `resources/vendor/MCP_Dialux`. Planned reuse: STF serialization/reading, geometry and layout routines, exported-result inspection. The Spanish standards parser is not a Hong Kong compliance engine. Do not run upstream building conversion against originals: review output destinations first. Upstream comments and README disagree about furniture/openings; verify actual evo behavior rather than treating either as proof.

CLI-Anything — https://github.com/HKUDS/CLI-Anything

Research checkout: 34f519533bc175d2fe287ab8316b0dd99bb9cc43. Apache-2.0, confirmed in the checkout LICENSE. Use its CLI/JSON architecture, real-backend tests and documented capabilities methodology. No claim of complete harness conformance yet. DIALux lacks the available source/backend assumed by its primary workflow; live UI control requires an explicit adapter.

## Retained as research, not redistributed dependencies

EvoParse — https://github.com/luciodias/EvoParse. Current pyproject requires Python >=3.14; no root LICENSE found during inspection. Do not vendor until license is established. Possible future read-only project inspection.

BHoM DIALux_Toolkit — https://github.com/BHoM/DIALux_Toolkit. LGPL-3.0; advertised compatibility DIALux 4.13. Existing STF implementation in MCP_Dialux already draws on this work; avoid a redundant second serializer.

dwg2ifc — https://github.com/ZOdiaKTN/dwg2ifc. Experimental single-storey orthogonal geometry; author says real-world accuracy target is not achieved. IFC import is marked PRO in the installed evo UI. Keep as research, not default conversion.

## Live evidence, 2026-11-08

Installed evo 14.1 reaches logged-in start screen. UI exposes StartRoomPlanning, StartImportPlan, StartNewProject and LoadProjectButton automation IDs. Subsequent real project/calculation gates are documented in `live-validation-2026-11-08.md` and `desktop-adapter.md`. Minimized windows must be activated before snapshot capture. Select target by executable, not title substring (browser titles may also include DIALux).


## Explicit grid planner extension

The vendored `dialux/luminarias.py` was reviewed before implementing `src/layout.py`. Its `reticula` places a requested count into bounding-box subdivisions and clips center points. It does not provide an externally anchored/rotated ceiling grid, full fixture footprint containment or polygonal keep-out regions. The new module addresses those distinct requirements using the already installed Shapely library, while leaving the upstream implementation and MIT notice unchanged. It does not replace the upstream STF serializer or claim photometric optimization. Synthetic tests cover footprint containment, exclusions, transform invariance and invalid inputs.

## Repository subset

The vendored copy retains the STF reader/writer and their optional CAD-reading dependencies, together with the original MIT license. Unused upstream room-building, layout and regulation modules were removed during repository cleanup. The original reviewed commit remains documented above.
