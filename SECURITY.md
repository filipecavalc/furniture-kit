# Security

## What opening this folder allows

When you trust this folder in Claude Code:

- `.claude/settings.json` lets Claude Code use every FreeCAD MCP tool and run the read-only
  environment check without asking each time. Installers and downloads (winget, brew, curl, wget,
  `Invoke-WebRequest`, the uv installer...) are set to always ask.
- When you also approve the `freecad` server, `.mcp.json` starts it with `uvx freecad-mcp`, which
  downloads the server from PyPI (always the latest version).

The FreeCAD tools include running Python inside FreeCAD. That Python has the same rights as you: it
can read and write files anywhere your user account can. This is what lets the kit build models and
write documents, but it means those actions are not confirmed one by one. If you prefer to approve
each one, remove `"mcp__freecad__*"` from `.claude/settings.json`.

The FreeCAD MCP addon listens on 127.0.0.1:9875 while FreeCAD is running. It accepts connections
from programs on your computer, not from the network (`remote_enabled: false`).

A project's `model/build.py` is a Python program. Only run projects from people you trust.

## What the setup changes outside the kit folder

Only with your permission: installs FreeCAD, uv and Blender; copies the FreeCAD MCP addon into
FreeCAD's `Mod` folder; writes `freecad_mcp_settings.json` (auto-start) in FreeCAD's user folder.
The uv installer is the official script from astral.sh, run from the internet.

## Reporting a problem

Please report security issues privately through
[GitHub security advisories](https://github.com/filipecavalc/furniture-kit/security/advisories/new),
not in public issues.
