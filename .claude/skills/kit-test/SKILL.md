---
name: kit-test
description: Run the furniture-kit test protocol on this computer (any OS) and package the evidence - setup experience, environment check, library self-test, renders and a small design from scratch - into a zip the tester sends back to the maintainers.
disable-model-invocation: true
---

# Kit test protocol

Goal: find out what works and what breaks on this computer, as a new user would experience it, and
hand the maintainers evidence they can act on without being here. You are testing the kit, not
fixing it: record problems precisely; apply a workaround only to keep going, and record it.

Everything goes in `projects/_selftest/` (gitignored). Keep a running log there, `LOG.md`, and add an
entry for every step as you go (not at the end):

```
## <time> - <step>
- Done by: assistant | tester (by hand)
- Command / action: ...
- Result: ok | problem
- Output / error (verbatim, trimmed): ...
- Workaround (if any): ...
```

## 0. Tester and machine

Ask, and write at the top of `LOG.md`:
- OS and version; for macOS also the chip (Apple Silicon or Intel); for Linux the distribution and
  desktop (Wayland/X11).
- Claude Code surface: desktop app or CLI.
- What was already installed before starting (FreeCAD, Blender, uv, Git, Homebrew...), so the report
  separates "fresh install" from "already there".
Also record `uname -a` (macOS/Linux) or the OS line from `setup/check.ps1` (Windows).

## 1. Setup as a new user

Follow the **kit-setup** skill exactly as with a new user, including asking before installing or
downloading anything. Log every step, who did it, and every manual action the tester had to take
(administrator prompts, macOS "open anyway" / Gatekeeper, moving folders, clicking in FreeCAD,
restarting Claude). Note anything in the setup instructions that was wrong, missing or confusing.
If something is already installed, still verify it the way the skill says and note "already installed".

## 2. Environment check

Run the check for this OS and save the full output to `projects/_selftest/check.txt`.
Note any line that is wrong for this machine (a tool reported missing that is installed, wrong path,
wrong version).

## 3. FreeCAD and the MCP connection

Start FreeCAD the way `CLAUDE.md` says for this OS; record the exact command, how long until port
9875 answers, and the output of `mcp__freecad__get_rpc_status`. If the `mcp__freecad__*` tools are
missing or fail, record the symptom and what fixed it.

## 4. Library self-test (inside FreeCAD)

```python
import sys; KIT = r"<absolute kit path>"; sys.path.insert(0, KIT + "/scripts")
import furniture; furniture.reload(); from furniture import selftest; print(selftest.run())
```

It writes `projects/_selftest/selftest.md` and `selftest.json`. Use a generous timeout (600 s).
Then open and look at, at least: `Drawer_Cabinet/images/SHEET_assembly.png`,
`Drawer_Cabinet/drawings/Drawer_Cabinet_Sheet1_Assembly.pdf`, `Drawer_Cabinet/cutlist/Drawer_Cabinet_Cut_List.pdf`,
`Industrial_Table/cutlist_pt-BR/Industrial_Table_Cut_List.pdf` and `Industrial_Table/Industrial_Table_Guide.pdf`.
Log anything visually wrong (missing or clipped text, wrong font, accents broken, empty pages,
dimensions in the wrong place, black or blank images).

## 5. Blender (skip if the tester chose not to install it)

With absolute paths, from the self-test copies:
- render `Drawer_Cabinet/model/Drawer_Cabinet_closed.glb` → `Drawer_Cabinet/render`, `--shots 3q_right --samples 32`
- render `Industrial_Table/model/Industrial_Table.glb` → `Industrial_Table/render`, `--shots 3q_right --samples 32 --no-wall`
- animation frames: `animate_assembly.py` on `Drawer_Cabinet_closed.glb` with `--frame 200,420`
Record the `DEVICE` line, the time each took, and look at every image.

## 6. A small design from scratch

Run the normal workflow (`CLAUDE.md`) on a simple brief, without the tester having to explain much:
"A bookshelf 800 wide, 300 deep, 1800 high, 18 mm plywood, 4 fixed shelves, back panel 6 mm."
Create it as `projects/_selftest/Bookshelf` (new-project skill, but in that folder), write
`build.py`, build, check collisions, run deliverables and one render. Log friction: anything you had
to guess, workarounds in `build.py`, library functions that were missing or confusing.

## 7. Report and package

Write `projects/_selftest/REPORT.md`:
1. Summary table: area (setup, check, FreeCAD/MCP, self-test, visual review, Blender, design) → pass /
   partial / fail, one line each.
2. Problems, most serious first: what happened, exact error, steps to reproduce, suspected cause
   (kit bug / documentation / this machine), suggested fix.
3. Manual steps the tester had to do, in order.
4. Versions and paths (OS, FreeCAD, Blender, uv, Qt, GPU device).
5. Time spent per phase.

Then zip the folder without the heaviest files:
- macOS / Linux: `cd projects && zip -r ../selftest-<os>-<yyyymmdd>.zip _selftest -x "*.FCStd" "*.FCBak" "*.blend"`
- Windows: `Compress-Archive -Path projects/_selftest/* -DestinationPath selftest-windows-<yyyymmdd>.zip`
  (delete `*.FCStd` from a copy first if the zip is large).

Tell the tester where the zip is and to send it to the maintainers, or attach it to a new issue at
https://github.com/filipecavalc/furniture-kit/issues together with `REPORT.md` pasted in the text.
Do not change files outside `projects/_selftest/` and the zip, and do not commit anything.
