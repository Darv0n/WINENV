#Requires -Version 5.1
<#
.SYNOPSIS
    Toggle Claude Code YOLO mode (bypassPermissions) on/off.
.DESCRIPTION
    Manipulates ~/.claude/settings.local.json between normal mode (accumulated
    allow-list) and YOLO mode (bypassPermissions). PreToolUse hooks in
    settings.json still fire under bypass, so guard-destructive-bash.sh remains
    active as a safety net.

    State detection: reads settings.local.json for "bypassPermissions" string.
    Backup: .pre-yolo file preserves the original settings.local.json.
.PARAMETER On
    Force YOLO mode on.
.PARAMETER Off
    Force YOLO mode off.
.PARAMETER Status
    Show current mode without changing anything.
.EXAMPLE
    pwsh scripts\yolo.ps1           # auto-toggle
    pwsh scripts\yolo.ps1 -On       # force on
    pwsh scripts\yolo.ps1 -Off      # force off
    pwsh scripts\yolo.ps1 -Status   # check current state
#>

param(
    [switch]$On,
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

# --- YOLO config ---
$YoloConfig = @'
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  }
}
'@

# --- Detection ---
function Test-YoloActive {
    if (-not (Test-Path $SettingsPath)) { return $false }
    $content = Get-Content $SettingsPath -Raw
    return $content -match '"bypassPermissions"'
}

# --- Actions ---
function Enable-Yolo {
    if (Test-YoloActive) {
        Write-Host "Already in YOLO mode." -ForegroundColor Yellow
        return
    }

    # Backup current settings if file exists
    if (Test-Path $SettingsPath) {
        Copy-Item $SettingsPath $BackupPath -Force
        Write-Ok "Backed up settings.local.json -> .pre-yolo"
    }

    # Write bypass config
    Set-Content -Path $SettingsPath -Value $YoloConfig -NoNewline
    Write-Host ""
    Write-Host "  YOLO MODE: ON" -ForegroundColor Red -BackgroundColor Black
    Write-Host "  Hooks still active. guard-destructive-bash.sh has your back." -ForegroundColor DarkGray
    Write-Host ""
}

function Disable-Yolo {
    if (-not (Test-YoloActive)) {
        Write-Host "Already in normal mode." -ForegroundColor Yellow
        return
    }

    # Restore from backup
    if (Test-Path $BackupPath) {
        Copy-Item $BackupPath $SettingsPath -Force
        Remove-Item $BackupPath -Force
        Write-Ok "Restored settings.local.json from .pre-yolo"
    } else {
        # No backup — remove the bypass config entirely
        Remove-Item $SettingsPath -Force
        Write-Ok "Removed bypass config (no backup to restore)"
    }

    Write-Host ""
    Write-Host "  YOLO MODE: OFF" -ForegroundColor Green
    Write-Host ""
}

function Show-Status {
    if (Test-YoloActive) {
        Write-Host "  YOLO (bypassPermissions)" -ForegroundColor Red
    } else {
        Write-Host "  NORMAL" -ForegroundColor Green
    }
    if (Test-Path $BackupPath) {
        Write-Host "  Backup: .pre-yolo exists" -ForegroundColor DarkGray
    }
}

# --- Main ---
if ($Status) {
    Show-Status
} elseif ($On) {
    Enable-Yolo
} elseif ($Off) {
    Disable-Yolo
} else {
    # Auto-toggle
    if (Test-YoloActive) {
        Disable-Yolo
    } else {
        Enable-Yolo
    }
}
