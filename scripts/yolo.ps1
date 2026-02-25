#Requires -Version 5.1
<#
.SYNOPSIS
    Toggle Claude Code permission modes: NORMAL / YOLO / SICKO.
.DESCRIPTION
    Manipulates ~/.claude/settings.local.json between three escalation levels:

      NORMAL  — Per-tool approval prompts. Hooks active.
      YOLO    — Bypass permissions. Hooks still active (guard has your back).
      SICKO   — Bypass permissions. Hooks disabled (guard is sleeping).

    PreToolUse hooks in settings.json fire at NORMAL and YOLO levels because
    settings.local.json only overrides permissions. At SICKO level, an empty
    hooks object in settings.local.json shadows the shared hooks entirely.

    Backup: .pre-yolo file preserves the original settings.local.json.
    Restored on -Off from any level.
.PARAMETER On
    Enable YOLO mode (bypass permissions, hooks active).
.PARAMETER Sicko
    Enable SICKO mode (bypass permissions, hooks disabled).
.PARAMETER Off
    Return to NORMAL from any level.
.PARAMETER Status
    Show current mode without changing anything.
.EXAMPLE
    pwsh scripts\yolo.ps1              # auto-toggle NORMAL <-> YOLO
    pwsh scripts\yolo.ps1 -On          # force YOLO
    pwsh scripts\yolo.ps1 -Sicko       # escalate to SICKO
    pwsh scripts\yolo.ps1 -Off         # return to NORMAL
    pwsh scripts\yolo.ps1 -Status      # check current state
#>

param(
    [switch]$On,
    [switch]$Sicko,
    [switch]$Off,
    [switch]$Status
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Paths ---
$SettingsPath = Join-Path $env:USERPROFILE '.claude' 'settings.local.json'
$BackupPath = "$SettingsPath.pre-yolo"

# --- Output helpers (matches deploy.ps1 style) ---
function Write-Ok { param([string]$Message) Write-Host "   OK: $Message" -ForegroundColor Green }
function Write-Err { param([string]$Message) Write-Host "   ERROR: $Message" -ForegroundColor Red }

# --- Configs ---
$YoloConfig = @'
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
'@

$SickoConfig = @'
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "hooks": {}
}
'@

# --- Detection ---
# Returns: "NORMAL", "YOLO", or "SICKO"
function Get-CurrentMode {
    if (-not (Test-Path $SettingsPath)) { return "NORMAL" }
    $content = Get-Content $SettingsPath -Raw
    $hasBypass = $content -match '"bypassPermissions"'
    $hasEmptyHooks = $content -match '"hooks"\s*:\s*\{\s*\}'
    if ($hasBypass -and $hasEmptyHooks) { return "SICKO" }
    if ($hasBypass) { return "YOLO" }
    return "NORMAL"
}

# --- Backup / Restore ---
function Backup-Settings {
    if ((Test-Path $SettingsPath) -and -not (Test-Path $BackupPath)) {
        Copy-Item $SettingsPath $BackupPath -Force
        Write-Ok "Backed up settings.local.json -> .pre-yolo"
    }
}

function Restore-Settings {
    if (Test-Path $BackupPath) {
        Copy-Item $BackupPath $SettingsPath -Force
        Remove-Item $BackupPath -Force
        Write-Ok "Restored settings.local.json from .pre-yolo"
    } else {
        Remove-Item $SettingsPath -Force -ErrorAction SilentlyContinue
        Write-Ok "Removed override config (no backup to restore)"
    }
}

# --- Actions ---
function Enable-Yolo {
    $mode = Get-CurrentMode
    if ($mode -eq "YOLO") {
        Write-Host "  Already in YOLO mode." -ForegroundColor Yellow
        return
    }

    Backup-Settings
    Set-Content -Path $SettingsPath -Value $YoloConfig -NoNewline

    Write-Host ""
    Write-Host "  YOLO MODE: ON" -ForegroundColor Red -BackgroundColor Black
    Write-Host "  Hooks still active. guard-destructive-bash.sh has your back." -ForegroundColor DarkGray
    Write-Host ""
}

function Enable-Sicko {
    $mode = Get-CurrentMode
    if ($mode -eq "SICKO") {
        Write-Host "  Already in SICKO mode." -ForegroundColor Yellow
        return
    }

    Backup-Settings
    Set-Content -Path $SettingsPath -Value $SickoConfig -NoNewline

    Write-Host ""
    Write-Host "  SICKO MODE: ON" -ForegroundColor Magenta -BackgroundColor Black
    Write-Host "  Permissions bypassed. Hooks disabled. Guard is sleeping." -ForegroundColor DarkGray
    Write-Host "  You are the safety net." -ForegroundColor DarkGray
    Write-Host ""
}

function Disable-All {
    $mode = Get-CurrentMode
    if ($mode -eq "NORMAL") {
        Write-Host "  Already in NORMAL mode." -ForegroundColor Yellow
        return
    }

    Restore-Settings

    Write-Host ""
    Write-Host "  NORMAL MODE: RESTORED" -ForegroundColor Green
    Write-Host ""
}

function Show-Status {
    $mode = Get-CurrentMode
    switch ($mode) {
        "SICKO"  { Write-Host "  SICKO (bypassPermissions + hooks disabled)" -ForegroundColor Magenta }
        "YOLO"   { Write-Host "  YOLO (bypassPermissions)" -ForegroundColor Red }
        "NORMAL" { Write-Host "  NORMAL" -ForegroundColor Green }
    }
    if (Test-Path $BackupPath) {
        Write-Host "  Backup: .pre-yolo exists" -ForegroundColor DarkGray
    }
}

# --- Main ---
if ($Status) {
    Show-Status
} elseif ($Off) {
    Disable-All
} elseif ($Sicko) {
    Enable-Sicko
} elseif ($On) {
    Enable-Yolo
} else {
    # Auto-toggle: NORMAL <-> YOLO only (sicko requires explicit flag)
    $mode = Get-CurrentMode
    if ($mode -eq "NORMAL") {
        Enable-Yolo
    } else {
        Disable-All
    }
}
