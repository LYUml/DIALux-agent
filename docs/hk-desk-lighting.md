# Hong Kong desk-lighting advisory module

`profiles/hk-labour-desk-lighting.json` is separate from the EMSD energy module. Its source is Labour Department, *Lighting in Offices*, September 2003 third edition, [official PDF](https://www.labour.gov.hk/eng/public/oh/OHB50.pdf). Pages 8 and 11 were checked in both extracted text and rendered images on 2026-11-08. The source hash is retained in the profile.

Paragraph 8 on page 8 recommends an optimum 300–500 lx for normal desk work and a floor of 200 lx under all conditions. The implemented criterion checks only that floor. The page 11 Appendix instead gives optimum **average** examples for different activities. Those examples are retained as non-executable notes, not converted to legal minimums. This publication is advisory guidance; `verified` means the extraction was reviewed, not that a project is legally compliant.

Supply a measurement with metric `minimum_illuminance`, unit `lx`, surface `normal_desk_work` and evidence identifying its task surface, result source and covered operating conditions. A DIALux identifier such as WP1 is not automatically a desk surface. Review and document the mapping before using the semantic surface name. All of these context facts require nonempty evidence:

| Fact | Required value |
|---|---|
| labour_desk_guidance_adopted | true |
| visual_task | normal_desk_work |
| task_surface_mapping_reviewed | true |
| operating_conditions_coverage_reviewed | true |

The current two-page Summary reader does not extract a direct minimum or prove this scope. Therefore `report-check` on the test PDF cannot pass this module. Do not multiply rounded average illuminance and uniformity to fabricate the missing measurement. Do not infer all-condition coverage from a single scene or undocumented maintenance assumptions.

Use the existing `criteria-check` command or `evaluate_profile` MCP tool with independently evidenced task minimums. Missing scope, a room-average metric or an unmapped surface returns `unverified`. A pass checks only this adopted advisory floor; it does not establish optimum illumination or satisfy the other lighting-quality, energy and statutory requirements.
