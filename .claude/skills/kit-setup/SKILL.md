---
name: kit-setup
description: Set up or repair the furniture-kit environment - FreeCAD, the FreeCAD MCP addon, uv, Blender, language/catalog settings and the user profile. Use on first run, when setup/check reports MISSING or TODO, or when the FreeCAD MCP tools are missing or fail to connect.
---

# Setting up furniture-kit

The person may have nothing installed and may not be technical. Principles:

- Go one step at a time, in plain words, in the user's language.
- For every step say **who does it**: "I can do this for you" or "you need to do this, because ...".
- **Never install, download or copy anything without asking first.** Offer, wait for a clear yes.
- Installers may show an administrator prompt (Windows "Yes/No", macOS password). Only the user can
  answer it; tell them it will appear.
- The latest stable versions are fine. The kit was tested with FreeCAD 1.1.3 and Blender 5.1.2; the
  check prints a note when versions differ. If something breaks on a newer version, say so.
- Re-run the check (`setup/check.ps1` or `setup/check.sh`) after each step and show the result.

## What the user must have before this (you cannot do it for them)

- Claude Code (desktop app or CLI) on a plan that includes it, with this folder open.
- Accepted the folder **trust** prompt and approved the `freecad` MCP server when asked. Without
  that, `.mcp.json`, the permissions in `.claude/settings.json` and this setup do not take effect.

## Order

1. uv (runs the FreeCAD MCP server) → 2. FreeCAD → 3. FreeCAD MCP addon (+ auto-start) →
4. restart Claude so the `freecad` server connects → 5. Blender (optional) → 6. settings and profile →
7. smoke test.

## 1. uv

Official page: https://docs.astral.sh/uv/getting-started/installation/ (no administrator rights needed).

- **Windows, desktop app:** the user runs it in their own PowerShell window (Start menu > PowerShell),
  not through you: changes made from inside the app (like the PATH) are not seen by the rest of Windows.
  `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Windows CLI, macOS, Linux:** you may run it after asking.
  Windows: the command above. macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  (or `brew install uv` on macOS).
- Programs that are already open do not see the new PATH: **fully restart Claude** afterwards.

## 2. FreeCAD

Download page: https://www.freecad.org/downloads.php

- **Windows:** installer from the page. Or, if the user agrees, `winget install --id FreeCAD.FreeCAD -e --source winget`
  (an administrator prompt may appear).
- **macOS:** `.dmg` from the page (drag to Applications), or `brew install --cask freecad` (no
  password needed). On the first launch macOS asks for confirmation, also when installed with brew:
  the user confirms the dialog (if it refuses, System Settings > Privacy & Security > Open Anyway).
- **Linux:** AppImage or Flatpak from the page (`flatpak install flathub org.freecad.FreeCAD`) or the
  distribution package. Flatpak/Snap keep the user folder elsewhere; the check prints the right one.
- The user opens FreeCAD once so it creates its user folder. If FreeCAD asks about migrating settings
  from an older version, the user decides.

## 3. FreeCAD MCP addon

Source: https://github.com/neka-nat/freecad-mcp (it is **not** in FreeCAD's Addon Manager).
Goal: `<FreeCAD user folder>/Mod/FreeCADMCP/InitGui.py` exists. The check prints the user folder
(Windows: `%APPDATA%\FreeCAD\v1-1`; macOS: `~/Library/Application Support/FreeCAD/v1-1`;
Linux: usually `~/.local/share/FreeCAD/v1-1`).

1. Ask permission to download `https://github.com/neka-nat/freecad-mcp/archive/refs/heads/main.zip`
   (small zip) into `setup/downloads/` (gitignored) and extract it:
   - Windows: `Invoke-WebRequest -Uri <url> -OutFile setup/downloads/freecad-mcp.zip` then
     `Expand-Archive setup/downloads/freecad-mcp.zip -DestinationPath setup/downloads -Force`
   - macOS/Linux: `curl -L -o setup/downloads/freecad-mcp.zip <url> && unzip -o setup/downloads/freecad-mcp.zip -d setup/downloads`
   The folder to install is `setup/downloads/freecad-mcp-main/addon/FreeCADMCP`.
2. Put it in `Mod`:
   - **Windows, desktop app:** do not copy into `%APPDATA%` yourself (the app's sandbox hides it from
     FreeCAD). Open both folders for the user with `explorer.exe "<kit>\setup\downloads\freecad-mcp-main\addon"`
     and `explorer.exe "<FreeCAD user folder>"`, and ask them to create `Mod` if it does not exist and
     drag `FreeCADMCP` into it.
   - **Windows CLI, macOS, Linux:** you may copy it after asking. Create the `Mod` folder first
     (copying into a folder that does not exist yet can flatten the contents).
3. Turn on auto-start so the RPC server starts with FreeCAD:
   - **macOS, Linux, Windows CLI:** you may do it after asking (tested on macOS 2026-10-08). Write
     `<FreeCAD user folder>/freecad_mcp_settings.json` with
     `{"remote_enabled": false, "allowed_ips": "127.0.0.1", "auto_start_rpc": true}` (keep other keys if
     the file exists), then restart FreeCAD: macOS `osascript -e 'quit app "FreeCAD"'` and `open -a FreeCAD`;
     Linux close it and start it again.
   - **Windows, desktop app:** the file would land in the app's private copy of `%APPDATA%`. Ask the user
     to restart FreeCAD, pick the **MCP Addon** workbench, click **Start RPC Server**, and turn on
     auto-start in the addon's menu.
4. Run the check: addon OK, auto-start on and RPC server listening on 9875.

## 4. MCP server not connected

Symptoms: no `mcp__freecad__*` tools in the session, or calls fail.

- Folder not trusted / server not approved ("Pending approval" in `/mcp`): ask the user to approve it
  (CLI: `/mcp`; desktop app: the prompt appears when the folder is opened; restarting the session
  shows it again). If they declined it earlier, `claude mcp reset-project-choices` in a terminal opened
  in the kit folder brings the prompt back.
- uv missing or not on Claude's PATH: install it (step 1) and fully restart Claude.
- Antivirus or proxy intercepting HTTPS: `.mcp.json` already passes `--system-certs` (uv 0.11 or
  newer; the check warns about older ones: `uv self update`).
- Tools exist but calls fail: FreeCAD closed or RPC server not started (Session start in CLAUDE.md).
- `get_rpc_status` reports a version mismatch: update the addon (step 3 again) and restart FreeCAD.

## 5. Blender (optional, only for renders and animations)

Download page: https://www.blender.org/download/

- **Windows:** installer (asks for administrator rights), or the portable `.zip` (no administrator:
  extract to a folder such as `C:\Users\<name>\Blender`, then tell Claude where it is).
  `winget install --id BlenderFoundation.Blender -e` also asks for administrator rights.
- **macOS:** `.dmg` or `brew install --cask blender`. **Linux:** tarball, Flatpak, Snap or distribution package.
- Renders use the GPU when there is one (NVIDIA, AMD, Apple, Intel) and the CPU otherwise (slower:
  use fewer `--samples`).

## 6. Settings and profile (always with the user)

Ask, one topic at a time:

1. Language for the conversation and for generated documents (`en`, `pt-BR`; offer to add another
   to `scripts/furniture/i18n.py`).
2. Country/region → material catalog. If there is no `catalog/<code>.json` for it, offer to create one
   from `br.json` with local names, sheet/bar sizes and thicknesses researched from local suppliers,
   each unconfirmed value marked `"verify": true` with its `"source"`. Never guess supplier data.
3. Who builds: the user, a cabinet shop, a metal shop, or a mix. If the user builds, ask in a
   separate open question which tools they have (table saw, circular saw, router, drill, pocket-hole
   jig, welding and which process, metal cutting...): a multiple-choice answer does not capture them.
4. Preferences: materials they like or avoid, how they buy (local store, lumber yard, online), local
   trade names and units, anything they always decide themselves (e.g. finishes).

Write `config/local.json` (see `config/example.json`) and `CLAUDE.local.md` from this template.
Both are gitignored and stay on this computer.

```markdown
# User profile

- Language: <conversation language>; documents: <en | pt-BR>
- Region: <country/city> - catalog <code>
- Builds: <self / cabinet shop / metal shop>; tools: <list>
- Buying: <where>; trade names and units: <e.g. mm, local board names>
- Always decides alone (do not ask, do not include): <e.g. finishes>
- Other preferences: <...>
```

## 7. Smoke test

With `RESULT: READY` and the RPC server listening:

1. Build the Drawer_Cabinet example (`__file__ = r"<kit>/examples/Drawer_Cabinet/model/build.py";
   exec(open(__file__, encoding="utf-8").read()); print(build())`) and show the screenshot: the report
   must say `collisions: none`. `build()` writes no files.
2. If Blender is installed, a quick render: export with
   `export.glb(project.open_project("Drawer_Cabinet", folder=HERE), r"<kit>/projects/_smoke/model/smoke.glb")`
   and run the render skill with `--shots 3q_right --samples 32` into `<kit>/projects/_smoke/render`.
   Open the PNG and show it.
3. Tell the user it is ready and what they can do next: describe an idea, share references, or look
   at the examples.
