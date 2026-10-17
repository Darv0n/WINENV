#Requires -Version 5.1
<#
.SYNOPSIS
    Back up Claude Code session history and project data.
.DESCRIPTION
    Incrementally copies Claude's runtime data to a backup destination.
    Safe to run repeatedly — only copies changed files.

    What gets backed up:
      ~/.claude/history.jsonl       Global conversation history
      ~/.claude/projects/           Per-project session transcripts + memory
      ~/.claude/todos/              Todos
      ~/.claude/tasks/              Tasks

    Default destination: C:\Users\<user>\claude-backups\
    Override with -Destination.
.PARAMETER Destination
    Where to write backups. Defaults to ~/claude-backups/.
.PARAMETER DryRun
    Show what would be copied without copying anything.
.EXAMPLE
    pwsh scripts\backup-claude.ps1
    pwsh scripts\backup-claude.ps1 -Destination D:\Backups\claude
    pwsh scripts\backup-claude.ps1 -DryRun
#>

param(
    [string]$Destination = (Join-Path $env:USERPROFILE 'claude-backups'),
    [switch]$DryRun,
    [switch]$Register,
    [switch]$Unregister
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- Scheduled task registration ---
$TaskName   = 'ClaudeBackup'
$ScriptPath = $MyInvocation.MyCommand.Path

if ($Register) {
    $action   = New-ScheduledTaskAction -Execute 'pwsh.exe' -Argument "-NonInteractive -WindowStyle Hidden -File `"$ScriptPath`""
    $triggers = @(
        (New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME),
        (New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -Once -At (Get-Date))
    )
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $triggers -Settings $settings -RunLevel Limited -Force
    Write-Ok "Scheduled task '$TaskName' registered (hourly + at login)"
    return
}

if ($Unregister) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Ok "Scheduled task '$TaskName' removed"
    return
}

$Source = Join-Path $env:USERPROFILE '.claude'

$Items = @(
    'history.jsonl',
    'projects',
    'todos',
    'tasks'
)

function Write-Ok  { param([string]$m) Write-Host "   OK: $m" -ForegroundColor Green }
function Write-Inf { param([string]$m) Write-Host "  INF: $m" -ForegroundColor Cyan }
function Write-Err { param([string]$m) Write-Host "  ERR: $m" -ForegroundColor Red }

if ($DryRun) {
    Write-Host ""
    Write-Host "  DRY RUN — no files will be copied" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Source:      $Source"
Write-Host "  Destination: $Destination"
Write-Host ""

if (-not $DryRun) {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
}

$timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
$anyError = $false

foreach ($item in $Items) {
    $src = Join-Path $Source $item
    $dst = Join-Path $Destination $item

    if (-not (Test-Path $src)) {
        Write-Inf "Skipping $item (not found)"
        continue
    }

    if ($DryRun) {
        Write-Inf "Would copy: $src -> $dst"
        continue
    }

    try {
        if (Test-Path $src -PathType Leaf) {
            # Single file
            $dstDir = Split-Path $dst
            New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
            Copy-Item $src $dst -Force
            Write-Ok "history.jsonl"
        } else {
            # Directory — robocopy incremental
            $result = robocopy $src $dst /E /MIR /NP /NFL /NDL /NJS /NC /NS 2>&1
            $exitCode = $LASTEXITCODE
            # Robocopy exit codes 0-7 are success/partial success
            if ($exitCode -le 7) {
                Write-Ok "$item\"
            } else {
                Write-Err "$item\ (robocopy exit $exitCode)"
                $anyError = $true
            }
        }
    } catch {
        Write-Err "$item — $_"
        $anyError = $true
    }
}

if (-not $DryRun) {
    # Write a timestamp file so we know when the last backup ran
    Set-Content -Path (Join-Path $Destination 'last-backup.txt') -Value $timestamp -NoNewline
}

Write-Host ""
if ($anyError) {
    Write-Host "  Backup completed with errors." -ForegroundColor Red
} elseif ($DryRun) {
    Write-Host "  Dry run complete. Run without -DryRun to execute." -ForegroundColor Yellow
} else {
    Write-Host "  Backup complete — $timestamp" -ForegroundColor Green
}
Write-Host ""
