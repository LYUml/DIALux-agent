# Concave-room native validation

Synthetic software validation only, not assignment geometry or design criteria. The source fixture is `examples/synthetic-concave-room.json`: (0,0), (6,0), (6,2), (4,2), (4,4), (0,4), height 3 m, working plane 0.8 m, maintenance factor 0.8, assumed reflectances 70/50/20 percent. Area is 20 m², versus a 24 m² bounding rectangle.

## Observed chain, 2026-11-09

1. A synthetic DXF expressed the six vertices in millimetres with a drawing offset of (10,20) metres. `drawing_extract_boundary` used handle `2F`, source SHA256 `afbb0ced60b817e7b6bbad3100fafed43017731bd2c3603417607f2d37061c30`, explicit origin (10,20) m and rotation 0. Extracted coordinates matched the fixture exactly. This source DXF was programmatically generated; no native AutoCAD roundtrip is claimed for it.
2. Public `room-create` reused the licensed upstream STF serializer. Independent STF readback retained all six vertices, including the reentrant corner, and 20 m² area. STF SHA256: `c0fb8abe85df0fce4fa280b0663c4a28f046c690309006ed7eef49bce73bb92a`.
3. Public desktop close/import/save-as/import-luminaire/arrange-space operations created `local/concave-native-v1.evo`. The previously calculated checkpoint project was closed without modifying its saved file. The known manufacturer ULD was reused; no invented photometry was supplied.
4. Native automatic placement reported a 3×2 arrangement but **five actual luminaires**. Public paginated readback found (1,1), (3,1), (5,1), (1,3), (3,3) m, all Z=3.035 m and zero rotation. The missing (5,3) lattice point is inside the excluded corner. This demonstrates why grid counts alone must not be treated as actual fixture count.
5. `verify_room_addition` checked all five assumed 0.6 m square footprints inside the explicit concave polygon. No previous groups existed in this synthetic case. This is a supplied-boundary check, not native vertex measurement.
6. Public native calculation, full PDF export and report parsing returned 493 lx average perpendicular illuminance, Uo 0.55 and 6.50 W/m². Summary pages 14–15 state 20.00 m². The rendered first summary visibly shows the reentrant outline and five fixtures with isolux results. PDF: 28 pages, 1,573,913 bytes, SHA256 `1134b36263af8f5b26c70c512be2758ecd1e5d5f98bc6627842a5f58e20de04c`.
7. Calculated native file saved: 505,595 bytes, SHA256 `8e10c61a34971ac91c90de5f8e53d6b05177ba4aba81352a1b2871c0bc01a72c`. A separate reopen/geometry readback gate for this case remains outstanding.

The long native room header wrapped between “Light” and “scene”; report parsing now supports that whitespace while retaining exact paired room/scene identity checks. Native DIALux report targets and bounding-rectangle glare footnotes are not adopted compliance criteria. Area, plotted topology and observed fixture positions support this concave test; they do not prove arbitrary curve/obstacle handling, full native vertex equality or all engineering criteria.
