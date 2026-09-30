# Environment check for furniture-kit (Windows). Read-only: it never installs or changes anything.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File setup/check.ps1
# Works on Windows PowerShell 5.1 and PowerShell 7+.

$ErrorActionPreference = "SilentlyContinue"
$Kit = Split-Path -Parent $PSScriptRoot
$Missing = New-Object System.Collections.Generic.List[string]
$TestedFreeCAD = "1.1.3"; $TestedBlender = "5.1.2"

function Line($status, $item, $detail) { Write-Output ("[{0}] {1}: {2}" -f $status, $item, $detail) }

Write-Output "furniture-kit environment check (Windows)"
Write-Output ("OS: " + [System.Environment]::OSVersion.VersionString)
if ($env:CLAUDE_CODE_ENTRYPOINT) { Write-Output ("Claude entrypoint: " + $env:CLAUDE_CODE_ENTRYPOINT) }
if ($env:CLAUDE_CODE_ENTRYPOINT -eq "claude-desktop") {
    Write-Output "NOTE: Claude desktop app on Windows (MSIX). Files it writes under %APPDATA% may be invisible to FreeCAD."
    Write-Output "      Prepare files inside the kit folder and let the user move them; start FreeCAD with explorer.exe."
}
Write-Output ""

# ------------------------------------------------------------------ FreeCAD
$fc = $null
foreach ($root in @("HKLM:", "HKCU:")) {
    $k = Get-ItemProperty "$root\Software\Microsoft\Windows\CurrentVersion\App Paths\FreeCAD.exe"
    if ($k -and $k.'(default)' -and (Test-Path $k.'(default)')) { $fc = $k.'(default)'; break }
}
if (-not $fc) {
    $cands = @()
    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, (Join-Path $env:LOCALAPPDATA "Programs"))) {
        if ($base) { $cands += Get-ChildItem -Path (Join-Path $base "FreeCAD*\bin\freecad.exe") }
    }
    $fc = ($cands | Sort-Object FullName -Descending | Select-Object -First 1).FullName
}
$fcVer = $null
if ($fc) {
    $cmd = Join-Path (Split-Path $fc) "freecadcmd.exe"
    if (Test-Path $cmd) {
        $out = (& $cmd --version 2>&1 | Out-String)
        if ($out -match "FreeCAD\s+(\d+\.\d+(\.\d+)?)") { $fcVer = $Matches[1] }
    }
    if (-not $fcVer -and $fc -match "FreeCAD (\d+\.\d+)") { $fcVer = $Matches[1] }
    $note = ""
    if ($fcVer -and $fcVer -ne $TestedFreeCAD) { $note = " (kit tested with $TestedFreeCAD)" }
    Line "OK" "FreeCAD" ("$fcVer - $fc" + $note)
} else {
    Line "MISSING" "FreeCAD" "not found. Download: https://www.freecad.org/downloads.php"
    $Missing.Add("FreeCAD")
}

# FreeCAD user folder: %APPDATA%\FreeCAD\v<major>-<minor> since 1.1, %APPDATA%\FreeCAD before
$userDir = $null
if ($fcVer -match "^(\d+)\.(\d+)") {
    $v = Join-Path $env:APPDATA ("FreeCAD\v{0}-{1}" -f $Matches[1], $Matches[2])
    if (Test-Path $v) { $userDir = $v }
}
if (-not $userDir) {
    $vs = Get-ChildItem -Path (Join-Path $env:APPDATA "FreeCAD") -Directory -Filter "v*" | Sort-Object Name -Descending
    if ($vs) { $userDir = $vs[0].FullName } elseif (Test-Path (Join-Path $env:APPDATA "FreeCAD")) { $userDir = Join-Path $env:APPDATA "FreeCAD" }
}
if ($userDir) {
    Write-Output ("FreeCAD user folder: " + $userDir)
    $mod = Join-Path $userDir "Mod"
    if (Test-Path (Join-Path $mod "FreeCADMCP\InitGui.py")) { Line "OK" "FreeCAD MCP addon" (Join-Path $mod "FreeCADMCP") }
    else {
        Line "MISSING" "FreeCAD MCP addon" ("copy addon/FreeCADMCP from https://github.com/neka-nat/freecad-mcp into " + $mod)
        $Missing.Add("FreeCAD MCP addon")
    }
    foreach ($opt in @("Woodworking", "frameforge")) {
        $found = Get-ChildItem -Path $mod -Directory | Where-Object { $_.Name -ieq $opt }
        if ($found) { Line "OK" "$opt addon (optional)" $found[0].FullName } else { Line "OPTIONAL" "$opt addon" "not installed (FreeCAD Addon Manager)" }
    }
    $st = Join-Path $userDir "freecad_mcp_settings.json"
    if ((Test-Path $st) -and ((Get-Content $st -Raw) -match '"auto_start_rpc"\s*:\s*true')) { Line "OK" "MCP server auto-start" "on" }
    else { Line "RECOMMENDED" "MCP server auto-start" "off: in FreeCAD, MCP Addon workbench > FreeCAD MCP menu > Auto-Start Server" }
} elseif ($fc) {
    Line "INFO" "FreeCAD user folder" "not created yet: open FreeCAD once"
    $Missing.Add("FreeCAD MCP addon")
}

# RPC port (FreeCAD running with the MCP server started)
$tcp = New-Object System.Net.Sockets.TcpClient
$open = $false
try { $ar = $tcp.BeginConnect("127.0.0.1", 9875, $null, $null); $open = $ar.AsyncWaitHandle.WaitOne(700) -and $tcp.Connected } catch {}
$tcp.Close()
if ($open) { Line "OK" "FreeCAD RPC server" "listening on 127.0.0.1:9875" }
else { Line "INFO" "FreeCAD RPC server" "not listening on 9875 (FreeCAD closed, or server not started)" }

# ------------------------------------------------------------------ uv (runs the FreeCAD MCP server)
$uvx = (Get-Command uvx).Source
if (-not $uvx) { $p = Join-Path $env:USERPROFILE ".local\bin\uvx.exe"; if (Test-Path $p) { $uvx = $p } }
if ($uvx) {
    $uv = Join-Path (Split-Path $uvx) "uv.exe"
    $uvVer = ""; if ((& $uv --version 2>&1 | Out-String) -match "uv (\d+\.\d+\.\d+)") { $uvVer = $Matches[1] }
    $onPath = [bool](Get-Command uvx)
    $note = ""; if (-not $onPath) { $note = " (NOT on PATH: restart Claude after installing, or open a new terminal)" }
    if ($uvVer -and ([version]$uvVer -lt [version]"0.11.0")) { $note += " (older than 0.11: update with 'uv self update')" }
    Line "OK" "uv" ("$uvVer - $uvx" + $note)
} else {
    Line "MISSING" "uv" "not found. Install: https://docs.astral.sh/uv/getting-started/installation/"
    $Missing.Add("uv")
}

# ------------------------------------------------------------------ Blender (render)
$bl = (Get-Command blender).Source
if (-not $bl) {
    $cands = @()
    foreach ($base in @($env:ProgramFiles, (Join-Path $env:LOCALAPPDATA "Programs"))) {
        if ($base) { $cands += Get-ChildItem -Path (Join-Path $base "Blender Foundation\Blender*\blender.exe") }
    }
    $bl = ($cands | Sort-Object FullName -Descending | Select-Object -First 1).FullName
}
if ($bl) {
    $blVer = ""; if ((& $bl --version 2>&1 | Out-String) -match "Blender (\d+\.\d+(\.\d+)?)") { $blVer = $Matches[1] }
    $note = ""; if ($blVer -and $blVer -ne $TestedBlender) { $note = " (kit tested with $TestedBlender)" }
    Line "OK" "Blender" ("$blVer - $bl" + $note)
} else {
    Line "OPTIONAL" "Blender" "not found (only needed for renders). Download: https://www.blender.org/download/"
}

# ------------------------------------------------------------------ optional tools and profile
if (Get-Command git) { Line "OK" "Git (optional)" ((git --version) -join "") } else { Line "OPTIONAL" "Git" "not installed (only needed to clone/update the kit)" }
if (Test-Path (Join-Path $Kit "config\local.json")) { Line "OK" "Kit settings" "config/local.json" } else { Line "TODO" "Kit settings" "config/local.json missing (language and catalog; created during setup)" }
if (Test-Path (Join-Path $Kit "CLAUDE.local.md")) { Line "OK" "User profile" "CLAUDE.local.md" } else { Line "TODO" "User profile" "CLAUDE.local.md missing (workshop, tools, who builds; created during setup)" }

Write-Output ""
if ($Missing.Count -eq 0) { Write-Output "RESULT: READY" } else { Write-Output ("RESULT: MISSING " + ($Missing -join ", ")) }
