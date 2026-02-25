#Requires -Version 5.1
<#
.SYNOPSIS
    WINENV bootstrap installer. Installs PS7, starship, zoxide, and JetBrainsMono Nerd Font.
.DESCRIPTION
    Designed to run on a fresh Windows 11 machine with only PS5.1 and winget available.
    Idempotent — safe to re-run. Skips already-installed packages.
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File bootstrap\install.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step { param([string]$Message) Write-Host "`n>> $Message" -ForegroundColor Cyan }
function Write-Ok { param([string]$Message) Write-Host "   OK: $Message" -ForegroundColor Green }
function Write-Skip { param([string]$Message) Write-Host "   SKIP: $Message" -ForegroundColor Yellow }
function Write-Err { param([string]$Message) Write-Host "   ERROR: $Message" -ForegroundColor Red }

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machinePath;$userPath"
}

# --- Winget packages ---

$packages = @(
    @{ Id = 'Microsoft.PowerShell';   Name = 'PowerShell 7';    Check = 'pwsh' }
    @{ Id = 'Starship.Starship';      Name = 'Starship';        Check = 'starship' }
    @{ Id = 'ajeetdsouza.zoxide';     Name = 'Zoxide';          Check = 'zoxide' }
)

foreach ($pkg in $packages) {
    Write-Step "Installing $($pkg.Name)"

    # Check if already available
    Refresh-Path
    $existing = Get-Command $pkg.Check -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Skip "$($pkg.Name) already installed ($($existing.Source))"
        continue
    }

    try {
        winget install --id $pkg.Id --source winget --accept-source-agreements --accept-package-agreements --silent
        Refresh-Path
        $verify = Get-Command $pkg.Check -ErrorAction SilentlyContinue
        if ($verify) {
            Write-Ok "$($pkg.Name) installed successfully"
        } else {
            Write-Err "$($pkg.Name) installed but not found on PATH. You may need to restart your terminal."
        }
    } catch {
        Write-Err "Failed to install $($pkg.Name): $_"
    }
}

# --- JetBrainsMono Nerd Font ---

Write-Step "Installing JetBrainsMono Nerd Font"

$fontDir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
$fontCheck = Get-ChildItem -Path $fontDir -Filter "JetBrainsMonoNerdFont*" -ErrorAction SilentlyContinue

if ($fontCheck) {
    Write-Skip "JetBrainsMono Nerd Font already installed ($($fontCheck.Count) files)"
} else {
    try {
        $nfVersion = "3.3.0"
        $zipUrl = "https://github.com/ryanoasis/nerd-fonts/releases/download/v$nfVersion/JetBrainsMono.zip"
        $tempZip = Join-Path $env:TEMP "JetBrainsMono-NF.zip"
        $tempExtract = Join-Path $env:TEMP "JetBrainsMono-NF"

        Write-Host "   Downloading from $zipUrl ..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip -UseBasicParsing

        Write-Host "   Extracting..."
        if (Test-Path $tempExtract) { Remove-Item $tempExtract -Recurse -Force }
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

        Write-Host "   Installing fonts (per-user)..."
        if (-not (Test-Path $fontDir)) { New-Item -Path $fontDir -ItemType Directory -Force | Out-Null }

        $shell = New-Object -ComObject Shell.Application
        $fontsFolder = $shell.Namespace(0x14)  # Windows Fonts folder

        $installed = 0
        Get-ChildItem -Path $tempExtract -Filter "*.ttf" | ForEach-Object {
            $destPath = Join-Path $fontDir $_.Name
            if (-not (Test-Path $destPath)) {
                Copy-Item $_.FullName $destPath -Force
                # Register the font for the current session
                $regPath = "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                $fontName = $_.BaseName -replace 'NerdFont', 'Nerd Font' -replace '-', ' '
                Set-ItemProperty -Path $regPath -Name "$fontName (TrueType)" -Value $destPath -ErrorAction SilentlyContinue
                $installed++
            }
        }

        # Cleanup
        Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
        Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

        Write-Ok "Installed $installed font files to $fontDir"
        Write-Host "   NOTE: You may need to restart Windows Terminal for the font to appear." -ForegroundColor Yellow
    } catch {
        Write-Err "Failed to install Nerd Font: $_"
    }
}

# --- Summary ---

Write-Step "Bootstrap complete"
Write-Host @"

Next steps:
  1. Restart your terminal (required for PATH changes and fonts)
  2. Run: bootstrap\verify.ps1   (to confirm everything works)
  3. Run: scripts\deploy.ps1     (to deploy configs via symlinks)
"@
