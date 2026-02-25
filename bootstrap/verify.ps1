#Requires -Version 5.1
<#
.SYNOPSIS
    Verifies all WINENV tools are installed and accessible.
.EXAMPLE
    powershell -File bootstrap\verify.ps1
#>

Set-StrictMode -Version Latest

$checks = @(
    @{ Name = 'Git';          Command = 'git --version' }
    @{ Name = 'Node.js';      Command = 'node --version' }
    @{ Name = 'Python';       Command = 'python --version' }
    @{ Name = 'PowerShell 7'; Command = 'pwsh --version' }
    @{ Name = 'Starship';     Command = 'starship --version' }
    @{ Name = 'Zoxide';       Command = 'zoxide --version' }
    @{ Name = 'VS Code';      Command = 'code --version' }
    @{ Name = 'GitHub CLI';   Command = 'gh --version' }
    @{ Name = 'Docker';       Command = 'docker --version' }
    @{ Name = 'Claude Code';  Command = 'claude --version' }
    @{ Name = 'Winget';       Command = 'winget --version' }
)

$pass = 0
$fail = 0

Write-Host "`nWINENV Tool Verification" -ForegroundColor Cyan
Write-Host ("=" * 50)

foreach ($check in $checks) {
    try {
        $output = Invoke-Expression $check.Command 2>&1 | Select-Object -First 1
        $version = ($output -replace '^\s+', '').Trim()
        Write-Host ("  PASS  {0,-15} {1}" -f $check.Name, $version) -ForegroundColor Green
        $pass++
    } catch {
        Write-Host ("  FAIL  {0,-15} not found" -f $check.Name) -ForegroundColor Red
        $fail++
    }
}

# Font check
$fontDir = "$env:LOCALAPPDATA\Microsoft\Windows\Fonts"
$nerdFont = Get-ChildItem -Path $fontDir -Filter "JetBrainsMonoNerdFont*" -ErrorAction SilentlyContinue
if ($nerdFont) {
    Write-Host ("  PASS  {0,-15} {1} files installed" -f "Nerd Font", $nerdFont.Count) -ForegroundColor Green
    $pass++
} else {
    Write-Host ("  FAIL  {0,-15} not found in {1}" -f "Nerd Font", $fontDir) -ForegroundColor Red
    $fail++
}

Write-Host ("`n{0} passed, {1} failed" -f $pass, $fail)

if ($fail -gt 0) {
    Write-Host "Run bootstrap\install.ps1 to install missing tools." -ForegroundColor Yellow
    exit 1
}
