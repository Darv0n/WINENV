#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Configure power settings for a dev workstation used with remote sessions.
.DESCRIPTION
    Disables sleep, hibernate, Fast Startup, Wi-Fi power saving, USB selective
    suspend. Sets lid close to do nothing. Extends screen lock timeout.
    Sets Windows Update active hours to minimize surprise reboots.
.NOTES
    Must be run as administrator. Idempotent — safe to run repeatedly.
#>

Write-Host "Configuring power settings..." -ForegroundColor Cyan

# --- Sleep: disabled ---
powercfg /change standby-timeout-ac 0
powercfg /change standby-timeout-dc 0
Write-Host "  Sleep: never (AC + battery)"

# --- Display: never on AC, 5 min on battery ---
powercfg /change monitor-timeout-ac 0
powercfg /change monitor-timeout-dc 5
Write-Host "  Display: never AC / 5 min battery"

# --- Hibernate: off ---
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 0
powercfg /hibernate off
Write-Host "  Hibernate: off"

# --- Fast Startup: disabled (depends on hibernate being off) ---
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power' -Name 'HiberbootEnabled' -Value 0
Write-Host "  Fast Startup: off"

# --- Lid close: do nothing ---
# Unhide the setting first (some OEM power plans hide it)
powercfg -attributes SUB_BUTTONS 5ca83367-6e45-459f-a27b-476b1d01c936 -ATTRIB_HIDE 2>$null
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS 5ca83367-6e45-459f-a27b-476b1d01c936 0
powercfg /setdcvalueindex SCHEME_CURRENT SUB_BUTTONS 5ca83367-6e45-459f-a27b-476b1d01c936 0
Write-Host "  Lid close: do nothing"

# --- Wi-Fi power saving: max performance ---
powercfg /setacvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 12bbebe6-58d6-4636-95bb-3217ef867c1a 0
powercfg /setdcvalueindex SCHEME_CURRENT 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 12bbebe6-58d6-4636-95bb-3217ef867c1a 0
Write-Host "  Wi-Fi: max performance"

# --- USB selective suspend: disabled ---
powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
powercfg /setdcvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0
Write-Host "  USB suspend: off"

# --- Screen lock timeout: 15 min AC, 10 min battery ---
powercfg -attributes SUB_VIDEO VIDEOCONLOCK -ATTRIB_HIDE 2>$null
powercfg /setacvalueindex SCHEME_CURRENT SUB_VIDEO VIDEOCONLOCK 900
powercfg /setdcvalueindex SCHEME_CURRENT SUB_VIDEO VIDEOCONLOCK 600
Write-Host "  Screen lock: 15 min AC / 10 min battery"

# --- Apply changes ---
powercfg /setactive SCHEME_CURRENT

# --- Windows Update active hours: 8 AM - 2 AM ---
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -Name 'ActiveHoursStart' -Value 8
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' -Name 'ActiveHoursEnd' -Value 2
Write-Host "  Windows Update: active hours 8 AM - 2 AM"

Write-Host ""
Write-Host "Done. All power settings applied." -ForegroundColor Green
