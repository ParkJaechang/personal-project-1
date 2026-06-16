$ErrorActionPreference = "Continue"

$logPath = Join-Path $env:TEMP "pp1-enable-wsl-for-docker.log"
"Starting WSL/Docker prerequisite setup: $(Get-Date)" | Set-Content -Path $logPath

function Invoke-Logged {
    param([string] $Command)

    ">>> $Command" | Add-Content -Path $logPath
    cmd.exe /c "$Command >> `"$logPath`" 2>&1"
    "exit_code=$LASTEXITCODE" | Add-Content -Path $logPath
}

Invoke-Logged "dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart"
Invoke-Logged "dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart"
Invoke-Logged "wsl.exe --install --no-distribution"
Invoke-Logged "wsl.exe --set-default-version 2"

"Finished: $(Get-Date)" | Add-Content -Path $logPath
Write-Host "Log written to $logPath"
Write-Host "If Windows says a restart is required, restart manually later."
Read-Host "Press Enter to close"
