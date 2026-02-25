#Requires -Version 5.1
<#
.SYNOPSIS
    Claude Code status line script.
    Shows model, cost, tokens, cache hit rate, and git branch.
.DESCRIPTION
    Designed to be called by Claude Code's statusLine configuration.
    Outputs a single line of text for the status bar.
#>

$parts = @()

# Git branch
$branch = git rev-parse --abbrev-ref HEAD 2>$null
if ($branch) {
    $parts += "[$branch]"
}

# Claude session stats (if available)
$statsFile = Join-Path $env:USERPROFILE '.claude\stats-cache.json'
if (Test-Path $statsFile) {
    try {
        $stats = Get-Content $statsFile -Raw | ConvertFrom-Json
        if ($stats.model) { $parts += $stats.model }
        if ($stats.totalCost) { $parts += "`$$([math]::Round($stats.totalCost, 2))" }
        if ($stats.totalTokens) {
            $tokensK = [math]::Round($stats.totalTokens / 1000, 1)
            $parts += "${tokensK}k tok"
        }
    } catch {
        # Stats file malformed, ignore
    }
}

if ($parts.Count -gt 0) {
    Write-Output ($parts -join ' | ')
}
