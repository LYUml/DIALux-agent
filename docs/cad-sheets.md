# Fixed-paper frames and titleblocks

Optional drawing `spec.sheet` accepts exactly `paper` (A3/A2/A1/A0),
`scale_denominator` (25/50/100/200/500), `title`, `drawing_number`, and `revision`.
Text is bounded plain ASCII without CAD escapes. Example:

```json
{"paper":"A3","scale_denominator":100,"title":"Synthetic lighting test","drawing_number":"TEST-001","revision":"A"}
```

The existing planned/observed/scheduled drawing export routes accept this option.
A separate module uses ezdxf entity extents to estimate content fit and adds
editable LINE/TEXT entities on SHEET. Engineering coordinates remain unchanged.
The fixed frame has 20 mm paper margins and a 30 mm titleblock. Oversize content
or title text is refused, without automatic scale changes. This is not automatic
multi-viewport composition or a general annotation-collision proof.

Native verification compares all sheet entities after DWG save and independent
reopening, alongside fixtures, dimensions and schedule entities. Native plotting
refuses a sheet whose paper/scale label differs from the explicit print request;
fit-to-page is refused for framed sheets.

## Native synthetic checkpoint

2026-11-09: existing six-fixture observed drawing with its report-linked schedule
was framed, saved to DWG, reopened and plotted at A3 1:100. All sheet entities and
fixture/schedule records survived. PDF outline scale error was 0.03875 pt or less.
Rendered inspection showed complete border, labels, table and titleblock. Large
unused space remains: automatic content-zone arrangement is unfinished.

- Evidence: ignored `local/sheet-evidence-v2.json`, `local/sheet-native-v2/manifest.json`.
- PDF: `local/sheet-plot-v2/layout.pdf`.
- PDF SHA256: `419ae9d03fab7f70d4b7f53bc4d109b33ad1a6bc889bbf16da7ce3ffcb1cdafc`.
- DWG SHA256: `0c3e3ed18cf44f3c09970bbaacebda11e6cb03c3f1a85fba4b48f8bdec7606f3`.

The initial 10 mm frame was clipped by the installed PDF plot configuration;
its missing room edge correctly failed vector-scale verification. Failed v1
artifacts remain preserved. The accepted 20 mm frame is tested on this A3 setup,
not certified for every printer or paper configuration. 30 targeted CAD tests
passed. Combined dimension-heavy/large framed sheets remain separate gates.
