# Synthetic PDF reports

These six PDFs contain original synthetic text authored for parser tests. Their
rooms, pages and numeric values are test inputs. Every page identifies the file
as synthetic test data. They contain no assignment plans, personal information,
photometry, simulation images or extracted pages from proprietary reports.

The fixtures exercise real PDF text extraction, multi-room/scene separation,
page numbering, missing uniformity, source hashes and CLI applicability checks.
They replace seven tests that previously depended on undistributed local files.
The concave-area fixture tests the reported area field, not geometric simulation.

Tests consume the committed PDFs directly and check the SHA-256 manifest. They
need neither DIALux nor a PDF generator. To regenerate on Windows, install
ReportLab in a development environment and run:

```powershell
python -m pip install reportlab
python -m scripts.generate_test_reports
```

The generator uses the Windows Arial font with document embedding permission
(OS/2 fsType 8). PDFs contain embedded font subsets; the original font file is
not distributed. Regeneration updates manifest.json. Review changed PDFs and
manifest hashes together before committing them. Normal installation and CI
do not require ReportLab or system fonts.
