# Changelog

All notable changes to this project. Versions follow [Semantic Versioning](https://semver.org/):
a major version means existing `build.py` files, catalogs or assembly scripts may need changes.

## [1.0.0] - 2026-10-08

First stable release.

### Added
- `furniture` library (runs inside FreeCAD): parametric parts with material metadata (panels,
  solid wood, steel profiles RECT/SQ/ROUND/BAR, glass, hardware), driven by a `Params` spreadsheet.
- Checks: collisions, invalid shapes, overall envelope.
- Bill of materials (CSV, Markdown and a FreeCAD spreadsheet).
- Sheet cut list (guillotine, respects grain) and bar cut list (linear) as PDF, with warnings for
  unconfirmed supplier data.
- Solid-wood buying and ripping plan (PDF) and assembly guide (PDF).
- Images: standard views, exploded view, assembly steps, contact sheets.
- TechDraw helpers for dimensioned drawings.
- Export to glTF with materials; Blender scripts for photo-style renders (8 camera shots, GPU
  auto-detect with CPU fallback) and step-by-step assembly videos.
- Documents in English and Brazilian Portuguese; material catalog for Brazil (`catalog/br.json`).
- Environment checks for Windows (`setup/check.ps1`) and macOS/Linux (`setup/check.sh`).
- Claude Code skills `kit-setup`, `new-project`, `render`, `kit-test`; library self-test.
- Examples: Drawer_Cabinet, Industrial_Table.

### Fixed after the first macOS test (2026-10-08)
- A part and a group with the same name raised a cryptic error; names are now checked with a clear message.
- Self-test runs in English whatever the user's language, so results match on every machine.
- Long footers and titles shrink to fit the page (wider fonts on macOS clipped them).
- Singular/plural in cut lists ("1 part"); repeated supplier warnings shown once.
- Old assembly-step images are removed before new ones are written.
- Assembly video: 64 samples by default (was 16, grainy); log line with engine and samples.
- Drawing views keep Z vertical by default (perspective views of tall pieces were skewed).
- Parameter names that are FreeCAD units (`mm`, `h`, `t`...) are rejected with a clear message.
- Setup: auto-start of the FreeCAD MCP server done by Claude Code on macOS/Linux; Gatekeeper note
  for brew installs; first-render delay on Apple Silicon documented.

### Fixed in the pre-release review
- Project, group and part names are validated before anything is created (FreeCAD rewrites names
  with spaces, accents or a leading digit, which broke lookups); no half-made parts are left behind.
- Grain values are validated; missing translation keys no longer crash.
- Bill of materials keeps parts with different notes (e.g. edge banding) on separate rows.
- A panel in a material without a sheet size gives a clear warning instead of crashing the cut list.
- The cut-list summary continues on further pages when it does not fit on one.
- The same tube in both orientations (30x50 / 50x30) is one stock item; sections accept lower case,
  decimal commas and solid round bar (`ROUND 12`); a wall too thick for the size is rejected.
- Assembly steps, exploded views and animation steps reject names that match no part (typos).
- Missing images, catalogs without colours and `config/local.json` with a BOM no longer crash.
- Glass is transparent in the assembly video; renders work on Blender versions without AgX.
- Environment check: prints the kit version, flags FreeCAD older than 1.0 and Blender older than
  4.2, runnable Flatpak command, Snap user folder.
- `furniture.reload()` also reloads the package itself.
- Permissions: installers and downloads always ask (`ask` rules in `.claude/settings.json`).

### Tested on
- Windows 11 (FreeCAD 1.1.3, Blender 5.1.2) and macOS 26 on Apple Silicon (FreeCAD 1.1.4, Blender 5.2.2).
