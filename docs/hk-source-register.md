# Hong Kong official-source register

Research started 2026-11-08. Source discovery is not adoption of requirements. Only official documents support rule extraction; verify edition, amendments, page and project applicability before activating a criterion.

| Authority | Official source | Intended role | Review status |
|---|---|---|---|
| EMSD | https://www.emsd.gov.hk/beeo/en/mibec_beeo_codtechguidelines.html | Current BEC editions, technical guidance and implementation circulars | Index reviewed; edition applicability still to be resolved for project |
| EMSD | https://www.emsd.gov.hk/beeo/en/pee/BEC_2024_ENG.pdf | Lighting power density and lighting controls, section 5 | Downloaded locally; table/clauses being checked |
| EMSD | https://www.emsd.gov.hk/beeo/sc/pee/TG-BEC_2024.pdf | Interpretation of BEC, scope, LPD and controls | Located; detailed review pending |
| ArchSD | https://www.archsd.gov.hk/en/publications-publicity/general-specification-for-electrical-installation.html | Government-building specifications | This is an earlier-years index, NOT evidence of current edition |
| ArchSD | https://www.archsd.gov.hk/en/ | Current general specification and corrigenda notices | Current document discovery pending |
| Labour Department | https://www.labour.gov.hk/eng/public/content2_9b.htm | Office lighting and workplace lighting-assessment guidance | Official index reviewed; guidance is not automatically a universal statutory threshold |
| Labour Department | https://www.labour.gov.hk/eng/public/oh/DisplayScreen.pdf | Display-screen task lighting guidance | Located; do not confuse recommendation with general office design minimum |
| FSD | https://www.hkfsd.gov.hk/eng/source/guidance/Technical_Guidance_BS5266_2016_BSEN1838_2013.pdf | Local interpretation of emergency-lighting standards | Located; applicability and current supersession require review |

Do not import legacy EMSD `lightingcop.pdf` values merely because search results rank them highly. Do not apply licensing appendices for restaurants/other specified premises to an office without checking scope. Keep normal lighting, energy, government-contract specifications and emergency lighting as separate modules. International guidance must be sourced independently where the assignment requires it.

## Expanded review, 2026-11-08

Machine-readable PDF discovery is in `profiles/hk-sources.json`. Run `python scripts/cache_hk_sources.py` to cache the official files under ignored `local/references/official` and record SHA-256 hashes. Cache success does not mean the document has been reviewed. PDFs are not redistributed in Git.

- ArchSD's [building services specification index](https://www.archsd.gov.hk/en/publications-publicity/general-specification-for-building-services.html) embeds the 2022 edition incorporating GSBS05-2022 (July 2026). Its static footer date is misleading; the embedded publication entries and actual PDF must be inspected. Government-building contractual scope must be explicitly selected.
- EMSD's [lighting FAQ](https://www.emsd.gov.hk/beeo/en/mibec_faq_lighting_a.html), answer 1, confirms that section 5.5 control points and section 5.6 automatic lighting controls are independent. Sensors and timers do not substitute for the required control points.
- Labour Department's [Lighting in Offices](https://www.labour.gov.hk/eng/public/oh/OHB50.pdf) identifies itself as September 2003, third edition (PDF page 2). Page 8 discusses general and desk-work recommendations; page 11 gives optimum average illumination examples. Do not equate these different metrics, or promote recommendations to statutory limits.
- FSD's [code index](https://www.hkfsd.gov.hk/eng/fire_protection/notices/code.html) lists September 2022 as current. Read section 5.9 together with local technical guidance and circulars before creating emergency rules. A newer BSI edition is not evidence of Hong Kong adoption.
- Buildings Department's [PNAP index](https://www.bd.gov.hk/en/resources/codes-and-references/practice-notes-and-circular-letters/index_pnap.html) marks APP-113 repealed. APP-130 addresses a performance approach for domestic habitable rooms/kitchens; do not borrow its daylight-factor table for this office assignment.
- [WSD M&E specifications](https://www.wsd.gov.hk/en/publications-and-statistics/guidelines-reports-drawings-specifications/mechanical-electrical-standard-specification/volume-i/index.html) and [Housing Authority specification library](https://www.housingauthority.gov.hk/tc/business-partnerships/resources/specification-library/) are project-owner references, not defaults for an ordinary office.
- EMSD's [Wiring Regulations CoP page](https://www.emsd.gov.hk/en/electricity_safety/new_edition_cop/new_edition_cop_electricity_wiring_regulations/) identifies the 2025 edition and a transition for installations completed and connected by 31 December 2026. Electrical safety belongs in a separate module; the current assignment does not request circuit design.

## BEC extraction checkpoint

The office rows of Table 5.4 were checked against a rendered copy of PDF page 22 (printed 16): enclosed office up to 15 m2, office above 15 up to 200 m2, and office above 200 m2 have different LPD limits. This confirms that a single hard-coded office limit is invalid. Before activation, check section 5.1 exclusions, 5.4.1 low-power exception, space boundaries under 5.4.3, the applicable code edition, and evidence for area and complete fixed-lighting power. Automatic control has separate exceptions under 5.6; do not reuse the LPD exception. No project has been declared compliant from this extraction.

Rendered PDF pages 20, 21 and 23 were subsequently checked for scope, the 70 W exception and boundary/load rules. The scoped implementation is now `profiles/hk-bec2024-office-lpd.json`; see `docs/hk-office-lpd.md`. This does not activate any rule for an actual project without its evidenced context.

## Labour Department extraction checkpoint

The official OHB50 PDF was re-opened online and locally rendered at pages 8 and 11. Paragraph 8's normal-desk minimum recommendation is now isolated in `profiles/hk-labour-desk-lighting.json`, with explicit advisory classification and adoption/surface/condition evidence. Appendix optimum-average examples remain non-executable reference notes. See `docs/hk-desk-lighting.md`; a Summary average is not an acceptable substitute for the required task minimum.

## Automatic-control numerical extraction, 2026-11-09

BEC printed pages 18–19 / PDF pages 24–25 were checked as text and rendered images;
a fresh official download matched the existing source hash. The optional
`hk-bec2024-office-automatic-control.json` module checks five numerical conditions
for one evidenced office control zone. See [input scope and omissions](hk-automatic-control.md).
It preserves the 150 W and 24/7 occupancy boundaries and conditional sensor/override
scope. Control-point counting, daylight control and whole-system acceptance are
not implemented by this module; no assignment control scheme was created.
