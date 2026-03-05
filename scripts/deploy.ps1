#Requires -Version 5.1
<#
.SYNOPSIS
    WINENV symlink deployment engine. Deploys configs from WINENV/configs/ to target locations.
.DESCRIPTION
    Idempotent. Creates backups before overwriting. Supports dry-run mode.
    Git config uses [include] directive instead of symlink.
.PARAMETER DryRun
    Show what would be done without making changes.
.EXAMPLE
    pwsh scripts\deploy.ps1 -DryRun
    pwsh scripts\deploy.ps1
#>

param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$ConfigRoot = Join-Path $RepoRoot 'configs'
$BackupRoot = Join-Path $RepoRoot 'backups'
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

function Write-Step { param([string]$Message) Write-Host "`n>> $Message" -ForegroundColor Cyan }
function Write-Ok { param([string]$Message) Write-Host "   OK: $Message" -ForegroundColor Green }
function Write-Skip { param([string]$Message) Write-Host "   SKIP: $Message" -ForegroundColor Yellow }
function Write-Err { param([string]$Message) Write-Host "   ERROR: $Message" -ForegroundColor Red }
function Write-Dry { param([string]$Message) Write-Host "   DRY: $Message" -ForegroundColor Magenta }

function Backup-File {
    param([string]$Path)
    if (Test-Path $Path) {
        $item = Get-Item $Path -Force
        # Don't back up existing symlinks — just remove them
        if ($item.LinkType -eq 'SymbolicLink') {
            return
        }
        $name = $item.Name
        $dest = Join-Path $BackupRoot "$name.$Timestamp"
        Copy-Item $Path $dest -Force
        Write-Host "   Backed up: $Path -> $dest" -ForegroundColor DarkGray
    }
}

function Deploy-Symlink {
    param(
        [string]$Source,
        [string]$Target
    )

    $sourceFull = Join-Path $ConfigRoot $Source

    if (-not (Test-Path $sourceFull)) {
        Write-Err "Source not found: $sourceFull"
        return
    }

    if ($DryRun) {
        Write-Dry "$Target -> $sourceFull"
        return
    }

    # Ensure parent directory exists
    $parentDir = Split-Path -Parent $Target
    if (-not (Test-Path $parentDir)) {
        New-Item -Path $parentDir -ItemType Directory -Force | Out-Null
    }

    # Check if already correctly linked
    if (Test-Path $Target) {
        $item = Get-Item $Target -Force
        if ($item.LinkType -eq 'SymbolicLink' -and $item.Target -eq $sourceFull) {
            Write-Skip "Already linked: $Target"
            return
        }
        # Backup and remove existing file
        Backup-File $Target
        Remove-Item $Target -Force
    }

    New-Item -ItemType SymbolicLink -Path $Target -Target $sourceFull -Force | Out-Null
    Write-Ok "$Target -> $sourceFull"
}

function Deploy-GitInclude {
    param(
        [string]$Source
    )

    $sourceFull = Join-Path $ConfigRoot $Source
    $gitconfig = Join-Path $env:USERPROFILE '.gitconfig'
    $includeLine = "path = $($sourceFull -replace '\\', '/')"

    if (-not (Test-Path $sourceFull)) {
        Write-Err "Source not found: $sourceFull"
        return
    }

    if ($DryRun) {
        Write-Dry "Would add [include] $includeLine to $gitconfig"
        return
    }

    if (-not (Test-Path $gitconfig)) {
        Write-Err "No ~/.gitconfig found"
        return
    }

    $content = Get-Content $gitconfig -Raw
    if ($content -match [regex]::Escape($includeLine)) {
        Write-Skip "Git include already present"
        return
    }

    # Add include directive
    $includeBlock = "`n[include]`n`t$includeLine`n"
    Add-Content -Path $gitconfig -Value $includeBlock -NoNewline
    Write-Ok "Added [include] to $gitconfig"
}

# --- Windows Terminal special handling ---
function Get-WindowsTerminalSettingsPath {
    $wtPackages = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Filter "Microsoft.WindowsTerminal_*" -Directory -ErrorAction SilentlyContinue
    if ($wtPackages) {
        $settingsPath = Join-Path $wtPackages[0].FullName "LocalState\settings.json"
        return $settingsPath
    }
    return $null
}

# ============================================================
# DEPLOYMENT MAP
# ============================================================

Write-Host "`nWINENV Deploy" -ForegroundColor Cyan
Write-Host ("=" * 50)
if ($DryRun) { Write-Host "MODE: DRY RUN (no changes will be made)" -ForegroundColor Magenta }

# --- Shell configs ---
Write-Step "Shell configs"
Deploy-Symlink "git-bash\.bash_profile" (Join-Path $env:USERPROFILE '.bash_profile')
Deploy-Symlink "git-bash\.bashrc" (Join-Path $env:USERPROFILE '.bashrc')
Deploy-Symlink "starship\starship.toml" (Join-Path $env:USERPROFILE '.config\starship.toml')

# --- PowerShell 7 profile ---
Write-Step "PowerShell 7 profile"
$ps7ProfileDir = Join-Path $env:USERPROFILE 'Documents\PowerShell'
Deploy-Symlink "powershell\profile.ps1" (Join-Path $ps7ProfileDir 'profile.ps1')

# --- Git ---
Write-Step "Git config"
Deploy-GitInclude "git\gitconfig-winenv"
Deploy-Symlink "git\gitignore-global" (Join-Path $env:USERPROFILE '.config\git\ignore')
Deploy-Symlink "git\gitattributes-global" (Join-Path $env:USERPROFILE '.config\git\attributes')

# --- VS Code ---
Write-Step "VS Code"
$vsCodeUser = Join-Path $env:APPDATA 'Code\User'
Deploy-Symlink "vscode\settings.json" (Join-Path $vsCodeUser 'settings.json')
Deploy-Symlink "vscode\keybindings.json" (Join-Path $vsCodeUser 'keybindings.json')

# --- Claude Code ---
Write-Step "Claude Code"
$claudeDir = Join-Path $env:USERPROFILE '.claude'
Deploy-Symlink "claude\settings.json" (Join-Path $claudeDir 'settings.json')
Deploy-Symlink "claude\CLAUDE.md" (Join-Path $claudeDir 'CLAUDE.md')
Deploy-Symlink "claude\hooks\guard-destructive-bash.sh" (Join-Path $claudeDir 'hooks\guard-destructive-bash.sh')
Deploy-Symlink "claude\rules\principles.md" (Join-Path $claudeDir 'rules\principles.md')
Deploy-Symlink "claude\statusline.py" (Join-Path $claudeDir 'statusline.py')

# --- Windows Terminal ---
Write-Step "Windows Terminal"
$wtSettings = Get-WindowsTerminalSettingsPath
if ($wtSettings) {
    Deploy-Symlink "terminal\settings.json" $wtSettings
} else {
    Write-Skip "Windows Terminal package not found"
}

# --- Summary ---
Write-Host "`n" -NoNewline
Write-Host ("=" * 50)
if ($DryRun) {
    Write-Host "Dry run complete. Run without -DryRun to apply." -ForegroundColor Magenta
} else {
    Write-Host "Deployment complete. Restart terminal to pick up changes." -ForegroundColor Green
}
