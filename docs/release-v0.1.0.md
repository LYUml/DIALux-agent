# v0.1.0

Windows CLI and MCP tools for DIALux evo, with verified setup and saved-project recovery.

## Changes

- PowerShell setup detects Python 3.12, installs pinned dependencies, validates the environment and generates local MCP configuration.
- Desktop status reports process startup, readiness, blocking dialogs and multiple instances.
- Cold startup allows time for DIALux module loading.
- The known energy overlay is handled consistently across window enumeration paths.
- Saved checkpoint recovery verifies the source hash, creates a fresh project copy, recalculates, exports a scoped report and saves the result with retained step journals.
- Export failures identify their destination and pending dialogs for inspection.
- English quickstart and consolidated resources support a smaller checkout structure.

## Acceptance

- Fresh local Python environment installed successfully and passed 667 tests.
- Independent GitHub Windows runner installed through setup.ps1 and passed 660 tests, with seven platform/local-evidence skips.
- CLI and real stdio MCP both recovered a saved synthetic 168-luminaire project.
- Native calculation, report export and save completed. Reopened report values, units, surfaces and room/scene identity matched. Source and saved native project hashes remained unchanged during reopening.
- One reopened export was interrupted by an altered filename. The existing save dialog was inspected and resubmitted, then the PDF was checked successfully.

## Operating conditions

Requires Windows, Python 3.12 and installed DIALux evo. Tested with DIALux evo 14.1.
AutoCAD Core Console is required for native CAD operations. Use English DIALux reports for supported parsing.

Use one desktop task at a time and avoid typing in DIALux while it is being controlled.
Review blocking dialogs before continuing. Recovery restarts from an explicitly selected saved checkpoint and retains partial operation logs for inspection.
Complex geometry, arbitrary large fixture edits and unattended operation across unknown dialogs retain the limits described in current-acceptance.md.
