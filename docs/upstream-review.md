# Upstream reuse review

## Incorporated

MCP_Dialux — https://github.com/MarcosCastanedaVentura/MCP_Dialux

Pinned commit: 4489032e67cabe0d409819fad24f091128620a9d. MIT, copyright Marcos Castañeda. Unmodified `dialux/` sources and LICENSE copied to `vendor/MCP_Dialux`. Planned reuse: STF serialization/reading, geometry and layout routines, exported-result inspection. The Spanish standards parser is not a Hong Kong compliance engine. Do not run upstream building conversion against originals: review output destinations first. Upstream comments and README disagree about furniture/openings; verify actual evo behavior rather than treating either as proof.

CLI-Anything — https://github.com/HKUDS/CLI-Anything

Research checkout: 34f519533bc175d2fe287ab8316b0dd99bb9cc43. Apache-2.0, confirmed in the checkout LICENSE. Use its CLI/JSON architecture, real-backend tests and documented capabilities methodology. No claim of complete harness conformance yet. DIALux lacks the available source/backend assumed by its primary workflow; live UI control requires an explicit adapter.

## Retained as research, not redistributed dependencies

EvoParse — https://github.com/luciodias/EvoParse. Current pyproject requires Python >=3.14; no root LICENSE found during inspection. Do not vendor until license is established. Possible future read-only project inspection.

BHoM DIALux_Toolkit — https://github.com/BHoM/DIALux_Toolkit. LGPL-3.0; advertised compatibility DIALux 4.13. Existing STF implementation in MCP_Dialux already draws on this work; avoid a redundant second serializer.

dwg2ifc — https://github.com/ZOdiaKTN/dwg2ifc. Experimental single-storey orthogonal geometry; author says real-world accuracy target is not achieved. IFC import is marked PRO in the installed evo UI. Keep as research, not default conversion.

## Live evidence, 2026-11-08

Installed evo 14.1 reaches logged-in start screen. UI exposes StartRoomPlanning, StartImportPlan, StartNewProject and LoadProjectButton automation IDs. Subsequent real project/calculation gates are documented in `live-validation-2026-11-08.md` and `desktop-adapter.md`. Minimized windows must be activated before snapshot capture. Select target by executable, not title substring (browser titles may also include DIALux).
