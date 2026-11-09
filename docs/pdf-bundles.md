# Explicit static PDF bundles

`python -m src.pdf_bundle --request request.json` assembles existing report/drawing pages without authoring engineering conclusions. It reuses the installed, pinned `pypdfium2==5.15.1` page importer and renderer, rather than implementing a PDF merger. API reference: https://pypdfium2.readthedocs.io/en/stable/python_api.html#pypdfium2.PdfDocument.import_pages

The request contains `sections`, `output_directory`, `max_main_pages`, and `max_bytes`. Each section has exactly `path`, `sha256`, `pages` (explicit ordered 1-based integers), and `role` (`main` or `appendix`). At least one main page is required; main pages precede appendices. Page duplication, out-of-range selections, source hash mismatches, exceeded limits and existing output directories are rejected. Limits are explicit, not inferred from an assignment. Byte limits use decimal bytes. There are at most 100 sections, 1000 total pages and 20 million rendered pixels per page at 72 dpi.

The module reads source bytes, imports selected pages, reopens the in-memory output, and compares each page's text hash, physical dimensions and 72-dpi rendering hash against its source page. It rechecks source file hashes before publishing `bundle.pdf` and a page-by-page `manifest.json` to a new directory. A failed filesystem write can leave a partial directory; no automatic overwrite/resume is provided.

This is a static page copier. Forms and signed documents are refused. Bookmarks, links, attachments, accessibility structure and other interactive/document-level features are not verified. The pixel comparison is bounded rendering evidence, not full-resolution, engineering-content or source-authenticity verification. There is no lossy size reduction or automatic omission of pages to satisfy a limit.

## Synthetic acceptance

Thirteen tests cover reordered visible text and unequal page sizes, pinned source preservation, duplicate/out-of-range pages, hash mismatches, main-page and byte limits, section ordering, boolean page-number rejection and existing-output preservation. A real AcroForm fixture is refused. Fault injection verifies that an externally changed source or an importer returning the wrong page cannot publish a bundle. Invalid module requests return JSON with `state: rejected` and exit code 2.

The native-output smoke case `local/pdf-bundle-native-v1` combines the previously verified synthetic mixed-product A3 CAD sheet with pages 18 and 19 of the same synthetic project's DIALux report. All three source/output page rendering, text and size comparisons passed. Each output page was rendered and visually inspected: the landscape sheet, both portrait product tables, coordinates and labels remain legible with no new clipping. Original report page labels remain 18 and 19; they are not renumbered.

Output: 3 pages, 1 main page, 1,726,443 bytes; SHA-256 `4c3e849659008b4353a1a35d33dce07fd33cb6a2121d0f809976bc4556eab11c`. This is tool-test packaging, not an assignment report. Standard CLI/MCP registration and broader document-feature acceptance remain pending; the independent module command is available now.
