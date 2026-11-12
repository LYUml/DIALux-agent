# v0.1.1

All seven previously skipped local-report tests now use committed synthetic PDF
fixtures. A fresh checkout runs their real PDF extraction and CLI checks without
local DIALux artifacts.

Six synthetic PDFs and a SHA-256 manifest cover multi-room results, unavailable
uniformity, original page numbering, reported area and Hong Kong applicability.
The fixture generator is included for development use. Runtime dependencies are
unchanged. CI now fails if any test is skipped.
