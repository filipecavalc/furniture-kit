# Testing furniture-kit on your computer

The kit is tested on Windows 11. We want it to work the same on macOS and Linux, and that needs
people running it on real machines. A test run takes about an hour and you mostly answer questions.

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

Nothing outside `projects/_selftest/` is changed, and nothing is committed.

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
| Windows 11 (desktop app and CLI) | Tested |
| macOS (Apple Silicon / Intel) | Not tested yet |
| Linux (AppImage / Flatpak / distro packages) | Not tested yet |
