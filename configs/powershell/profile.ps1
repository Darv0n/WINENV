# WINENV PowerShell 7 Profile
# Deployed via symlink from WINENV/configs/powershell/profile.ps1

# --- PSReadLine ---
if (Get-Module -ListAvailable PSReadLine) {
    Set-PSReadLineOption -PredictionSource HistoryAndPlugin
    Set-PSReadLineOption -PredictionViewStyle ListView
    Set-PSReadLineOption -EditMode Windows
    Set-PSReadLineOption -BellStyle None
    Set-PSReadLineKeyHandler -Key Tab -Function MenuComplete
    Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward
    Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward
}

# --- Git aliases ---
function gs { git status @args }
function ga { git add @args }
function gc { git commit @args }
function gp { git push @args }
function gl { git log --oneline -20 @args }
function gd { git diff @args }
function gco { git checkout @args }
function gb { git branch @args }

# --- Navigation aliases ---
function proj { Set-Location C:\Users\doubl\projects }
function apps { Set-Location C:\Users\doubl\projects\apps }

# --- WINENV tools ---
function yolo { & pwsh "$env:USERPROFILE\projects\apps\WINENV\scripts\yolo.ps1" @args }
function yolo-status { & pwsh "$env:USERPROFILE\projects\apps\WINENV\scripts\yolo.ps1" -Status }
function github-setup { bash "$env:USERPROFILE\projects\apps\WINENV\scripts\github-setup" @args }
# CodeRabbit via WSL — isolates Windows PATH leakage
function cr { wsl env PATH=/home/doubl/.local/bin:/usr/local/bin:/usr/bin:/bin coderabbit review --plain -t uncommitted }

# --- Zoxide ---
if (Get-Command zoxide -ErrorAction SilentlyContinue) {
    Invoke-Expression (& { (zoxide init powershell | Out-String) })
}

# --- Conda ---
$condaPath = "$env:USERPROFILE\miniconda3\shell\condabin\conda-hook.ps1"
if (Test-Path $condaPath) {
    & $condaPath
}

# --- Starship prompt (must be last) ---
if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (&starship init powershell)
}
