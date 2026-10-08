# Testing furniture-kit on your computer

The kit is tested on Windows 11 and macOS on Apple Silicon (table below). We want it to work the same
everywhere, and that needs people running it on real machines. A test run takes 30 to 60 minutes,
you mostly answer questions, and it counts against your Claude plan's usage like any session.

## How to run it

1. Get the kit (Download ZIP or `git clone https://github.com/filipecavalc/furniture-kit`).
2. Open the folder in Claude Code (desktop app or CLI), accept the trust prompt.
3. Type `/kit-test` and follow along. The assistant will:
   - ask about your machine and what is already installed;
   - go through the setup as with a new user, asking before installing or downloading anything;
   - run the environment check, a self-test of the library inside FreeCAD and a few renders;
   - design a small bookshelf from scratch;
   - write `projects/_selftest/REPORT.md` and a `selftest-<os>-<date>.zip`.
4. Open a new [issue](https://github.com/filipecavalc/furniture-kit/issues) with the report pasted in
   and the zip attached (or send them to the maintainer).

Inside the kit folder the test writes only gitignored files: `projects/_selftest/`, the zip,
`setup/downloads/`, `config/local.json`, `CLAUDE.local.md` and, if you answer "don't ask again" to a
prompt, `.claude/settings.local.json`. Outside it, and only with your permission, the setup installs
programs and puts the FreeCAD MCP addon and its `freecad_mcp_settings.json` in FreeCAD's user folder.
Nothing is committed.

## Only want the quick checks?

- Environment: `bash setup/check.sh` (macOS/Linux) or
  `powershell -NoProfile -ExecutionPolicy Bypass -File setup/check.ps1` (Windows).
- Library, inside FreeCAD (Python console or MCP):
  ```python
  import sys; KIT = "/path/to/furniture-kit"; sys.path.insert(0, KIT + "/scripts")
  import furniture; furniture.reload(); from furniture import selftest; print(selftest.run())
  ```
  Report: `projects/_selftest/selftest.md`.

## Status by platform

| Platform | Status |
|---|---|
| Windows 11 (desktop app) | Tested (FreeCAD 1.1.3, Blender 5.1.2) |
| macOS 26 on Apple Silicon (desktop app) | Tested 2026-10-08 (FreeCAD 1.1.4, Blender 5.2.2, render on Metal) |
| macOS on Intel | Not tested yet |
| Linux (AppImage / Flatpak / distro packages) | Not tested yet |
