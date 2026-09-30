#!/usr/bin/env bash
# Environment check for furniture-kit (macOS and Linux). Read-only: it never installs or changes anything.
# Usage: bash setup/check.sh
# Not yet tested on real macOS/Linux machines: report problems in the repository issues.

KIT="$(cd "$(dirname "$0")/.." && pwd)"
MISSING=""
TESTED_FREECAD="1.1.3"; TESTED_BLENDER="5.1.2"
OS="$(uname -s)"

line() { printf '[%s] %s: %s\n' "$1" "$2" "$3"; }
missing() { MISSING="${MISSING:+$MISSING, }$1"; }
first_existing() { for p in "$@"; do [ -e "$p" ] && { echo "$p"; return 0; }; done; return 1; }

case "$OS" in
  Darwin) PLATFORM="macOS" ;;
  Linux) PLATFORM="Linux" ;;
  MINGW*|MSYS*|CYGWIN*) echo "Windows detected: run  powershell -NoProfile -ExecutionPolicy Bypass -File setup/check.ps1"; exit 0 ;;
  *) PLATFORM="$OS" ;;
esac
echo "furniture-kit environment check ($PLATFORM)"
echo "OS: $(uname -sr)"
[ -n "$CLAUDE_CODE_ENTRYPOINT" ] && echo "Claude entrypoint: $CLAUDE_CODE_ENTRYPOINT"
echo

# ------------------------------------------------------------------ FreeCAD
FC=""; FCCMD=""; FCKIND=""
if [ "$PLATFORM" = "macOS" ]; then
  APP="$(first_existing /Applications/FreeCAD.app "$HOME/Applications/FreeCAD.app")"
  if [ -n "$APP" ]; then
    FC="$APP"
    FCCMD="$(first_existing "$APP/Contents/Resources/bin/freecadcmd" "$APP/Contents/Resources/bin/FreeCADCmd" "$APP/Contents/MacOS/FreeCADCmd")"
  fi
else
  for c in freecad FreeCAD; do command -v "$c" >/dev/null 2>&1 && { FC="$(command -v "$c")"; break; }; done
  for c in freecadcmd FreeCADCmd; do command -v "$c" >/dev/null 2>&1 && { FCCMD="$(command -v "$c")"; break; }; done
  if [ -z "$FC" ] && command -v flatpak >/dev/null 2>&1 && flatpak info org.freecad.FreeCAD >/dev/null 2>&1; then
    FC="flatpak org.freecad.FreeCAD"; FCKIND="flatpak"
  fi
  if [ -z "$FC" ]; then
    AI="$(ls -1 "$HOME"/Applications/FreeCAD*.AppImage "$HOME"/Downloads/FreeCAD*.AppImage 2>/dev/null | sort -r | head -n1)"
    [ -n "$AI" ] && FC="$AI"
  fi
  [ -z "$FCKIND" ] && [ -d "$HOME/snap/freecad" ] && FCKIND="snap"
fi
FCVER=""
if [ -n "$FCCMD" ]; then FCVER="$("$FCCMD" --version 2>/dev/null | sed -n 's/.*FreeCAD \([0-9][0-9.]*\).*/\1/p' | head -n1)"; fi
if [ -z "$FCVER" ] && [ "$FCKIND" = "flatpak" ]; then FCVER="$(flatpak info org.freecad.FreeCAD 2>/dev/null | sed -n 's/^ *Version: *//p' | head -n1)"; fi
if [ -n "$FC" ]; then
  NOTE=""; [ -n "$FCVER" ] && [ "$FCVER" != "$TESTED_FREECAD" ] && NOTE=" (kit tested with $TESTED_FREECAD)"
  line OK FreeCAD "${FCVER:-version unknown} - $FC$NOTE"
else
  line MISSING FreeCAD "not found. Download: https://www.freecad.org/downloads.php"; missing FreeCAD
fi

# FreeCAD user folder (paths from github.com/neka-nat/freecad-mcp docs/installation.md)
VDIR="v1-1"
case "$FCVER" in [0-9]*.[0-9]*) VDIR="v$(echo "$FCVER" | cut -d. -f1)-$(echo "$FCVER" | cut -d. -f2)" ;; esac
if [ "$PLATFORM" = "macOS" ]; then
  USERDIR="$(first_existing "$HOME/Library/Application Support/FreeCAD/$VDIR" "$HOME/Library/Application Support/FreeCAD")"
else
  USERDIR="$(first_existing "$HOME/.var/app/org.freecad.FreeCAD/data/FreeCAD/$VDIR" "$HOME/.local/share/FreeCAD/$VDIR" \
             "$HOME/snap/freecad/common" "$HOME/.local/share/FreeCAD" "$HOME/.FreeCAD")"
fi
if [ -n "$USERDIR" ]; then
  echo "FreeCAD user folder: $USERDIR"
  MOD="$USERDIR/Mod"
  if [ -f "$MOD/FreeCADMCP/InitGui.py" ]; then line OK "FreeCAD MCP addon" "$MOD/FreeCADMCP"
  else line MISSING "FreeCAD MCP addon" "copy addon/FreeCADMCP from https://github.com/neka-nat/freecad-mcp into $MOD"; missing "FreeCAD MCP addon"; fi
  for opt in Woodworking frameforge; do
    F="$(ls -1d "$MOD"/* 2>/dev/null | grep -i "/$opt\$" | head -n1)"
    if [ -n "$F" ]; then line OK "$opt addon (optional)" "$F"; else line OPTIONAL "$opt addon" "not installed (FreeCAD Addon Manager)"; fi
  done
  if grep -Eq '"auto_start_rpc"[[:space:]]*:[[:space:]]*true' "$USERDIR/freecad_mcp_settings.json" 2>/dev/null; then line OK "MCP server auto-start" on
  else line RECOMMENDED "MCP server auto-start" "off: in FreeCAD, MCP Addon workbench > FreeCAD MCP menu > Auto-Start Server"; fi
elif [ -n "$FC" ]; then
  line INFO "FreeCAD user folder" "not found: open FreeCAD once"; missing "FreeCAD MCP addon"
fi

# RPC port
if (exec 3<>/dev/tcp/127.0.0.1/9875) 2>/dev/null; then line OK "FreeCAD RPC server" "listening on 127.0.0.1:9875"
else line INFO "FreeCAD RPC server" "not listening on 9875 (FreeCAD closed, or server not started)"; fi

# ------------------------------------------------------------------ uv
UVX="$(command -v uvx 2>/dev/null)"; ONPATH=1
[ -z "$UVX" ] && [ -x "$HOME/.local/bin/uvx" ] && { UVX="$HOME/.local/bin/uvx"; ONPATH=0; }
if [ -n "$UVX" ]; then
  UVVER="$("$(dirname "$UVX")/uv" --version 2>/dev/null | awk '{print $2}')"
  NOTE=""; [ "$ONPATH" = 0 ] && NOTE=" (NOT on PATH: restart Claude after installing, or open a new terminal)"
  case "$UVVER" in 0.[0-9].*|0.10.*) NOTE="$NOTE (older than 0.11: update with 'uv self update')" ;; esac
  line OK uv "$UVVER - $UVX$NOTE"
else
  line MISSING uv "not found. Install: https://docs.astral.sh/uv/getting-started/installation/"; missing uv
fi

# ------------------------------------------------------------------ Blender
BL="$(command -v blender 2>/dev/null)"
[ -z "$BL" ] && [ "$PLATFORM" = "macOS" ] && BL="$(first_existing /Applications/Blender.app/Contents/MacOS/Blender "$HOME/Applications/Blender.app/Contents/MacOS/Blender")"
if [ -z "$BL" ] && command -v flatpak >/dev/null 2>&1 && flatpak info org.blender.Blender >/dev/null 2>&1; then BL="flatpak run org.blender.Blender"; fi
if [ -n "$BL" ]; then
  BLVER="$($BL --version 2>/dev/null | sed -n 's/^Blender \([0-9][0-9.]*\).*/\1/p' | head -n1)"
  NOTE=""; [ -n "$BLVER" ] && [ "$BLVER" != "$TESTED_BLENDER" ] && NOTE=" (kit tested with $TESTED_BLENDER)"
  line OK Blender "${BLVER:-version unknown} - $BL$NOTE"
else
  line OPTIONAL Blender "not found (only needed for renders). Download: https://www.blender.org/download/"
fi

# ------------------------------------------------------------------ optional tools and profile
if command -v git >/dev/null 2>&1; then line OK "Git (optional)" "$(git --version)"; else line OPTIONAL Git "not installed (only needed to clone/update the kit)"; fi
if [ -f "$KIT/config/local.json" ]; then line OK "Kit settings" config/local.json; else line TODO "Kit settings" "config/local.json missing (language and catalog; created during setup)"; fi
if [ -f "$KIT/CLAUDE.local.md" ]; then line OK "User profile" CLAUDE.local.md; else line TODO "User profile" "CLAUDE.local.md missing (workshop, tools, who builds; created during setup)"; fi

echo
if [ -z "$MISSING" ]; then echo "RESULT: READY"; else echo "RESULT: MISSING $MISSING"; fi
