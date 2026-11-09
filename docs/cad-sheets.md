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

A second native gate exported the existing synthetic concave grid through the
public drawing exporter with `spec.sheet`: 23 fixtures, 12 m and 9 m native linear
dimensions, label-placement rules and the fixed A3 frame. Native reopen preserved
all fixture, dimension and sheet records. PDF physical scale error was below
0.078 pt; visual inspection confirmed complete frame, dimension labels and all
fixture IDs. It retains substantial whitespace and is not an automatic sheet
composition acceptance.

- Evidence: ignored `local/sheet-dimensions-evidence-v1.json`.
- PDF SHA256: `7173df0d016ea159fb99d5ee1a3b3e8d5d4abd23bbb81ceec892950c082e9ad0`.
- Native DWG SHA256: `c40a29850a02a1bb2ff7376e16b49ec001a824bef25c5d899ebb572ee4c6c4d0`.

Actual Core Console negative gates also refused a 1:50 request for a 1:100 sheet
and a fit-to-page request. Logs contain the specific sheet-guard errors;
`local/sheet-negative-gates-v1.json` records these outcomes. These are actual
native refusals, not inferred from unit tests. Full regression suite: 395 passed.

The 168-fixture synthetic planned CAD case also passed A1 1:100 framing,
independent DWG reopening and vector-scale verification. All 168 unique fixture
IDs were extracted from the PDF; sheet and fixture records matched the source.
Whole-sheet preview showed a complete frame and titleblock, with no clipped
content; typography and whitespace still require content-composition work.
This is CAD evidence, not a new DIALux placement or photometry acceptance.

- Evidence: ignored `local/sheet-large-evidence-v1.json`.
- PDF SHA256: `2fc15a23dc4f3dd668fcd1f9d7479e2f7fd0835490f600ef0cfa5417040f8e30`.
- Native DWG SHA256: `b97113cd91a983fb2829abd7c434027356d1bf378e5c79091dd962fe997416c6`.
- Maximum outline-coordinate error: 0.07371 pt.
