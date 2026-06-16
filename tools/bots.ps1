param(
    [Parameter(Position = 0)]
    [ValidateSet("list", "status", "start", "stop", "restart", "logs")]
    [string] $Command = "status",

    [Parameter(Position = 1)]
    [string] $Bot = "soop"
)

$ErrorActionPreference = "Stop"

$ToolRoot = Split-Path -Parent $PSCommandPath
$ProjectRoot = Split-Path -Parent $ToolRoot
$ManifestPath = Join-Path $ToolRoot "bots.json"

function Read-BotManifest {
    if (-not (Test-Path $ManifestPath)) {
        throw "Bot manifest not found: $ManifestPath"
    }

    return Get-Content -Raw $ManifestPath | ConvertFrom-Json
}

function Get-BotConfig {
    param([string] $Name)

    $manifest = Read-BotManifest
    $config = $manifest.bots.$Name
    if (-not $config) {
        $known = $manifest.bots.PSObject.Properties.Name -join ", "
        throw "Unknown bot '$Name'. Known bots: $known"
    }

    return $config
}

function Resolve-BotPath {
    param([string] $Path)

    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }

    return Join-Path $ProjectRoot $Path
}

function Get-BotProcesses {
    param($Config)

    $needle = [string] $Config.processMatch
    return Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine.Contains($needle) -and
            $_.ProcessId -ne $PID
        }
}

function Show-BotStatus {
    param(
        [string] $Name,
        $Config
    )

    $processes = @(Get-BotProcesses -Config $Config)
    if ($processes.Count -eq 0) {
        Write-Output "$Name stopped"
        return
    }

    foreach ($process in $processes) {
        Write-Output "$Name running pid=$($process.ProcessId)"
    }
}

function Start-Bot {
    param(
        [string] $Name,
        $Config
    )

    $processes = @(Get-BotProcesses -Config $Config)
    if ($processes.Count -gt 0) {
        Show-BotStatus -Name $Name -Config $Config
        return
    }

    $workingDirectory = Resolve-BotPath ([string] $Config.workingDirectory)
    $startScript = Resolve-BotPath ([string] $Config.startScript)
    $logDirectory = Resolve-BotPath ([string] $Config.logDirectory)
    New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $stdoutLog = Join-Path $logDirectory "$Name-$stamp.out.log"
    $stderrLog = Join-Path $logDirectory "$Name-$stamp.err.log"

    Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $startScript) `
        -WorkingDirectory $workingDirectory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog | Out-Null

    Start-Sleep -Seconds 2
    Show-BotStatus -Name $Name -Config $Config
}

function Stop-Bot {
    param(
        [string] $Name,
        $Config
    )

    $processes = @(Get-BotProcesses -Config $Config)
    if ($processes.Count -eq 0) {
        Write-Output "$Name already stopped"
        return
    }

    foreach ($process in $processes) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Output "$Name stopped pid=$($process.ProcessId)"
    }
}

function Show-BotLogs {
    param(
        [string] $Name,
        $Config
    )

    $logDirectory = Resolve-BotPath ([string] $Config.logDirectory)
    if (-not (Test-Path $logDirectory)) {
        Write-Output "$Name has no logs yet"
        return
    }

    $logs = Get-ChildItem -Path $logDirectory -Filter "$Name-*.log" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 4

    if (-not $logs) {
        Write-Output "$Name has no logs yet"
        return
    }

    $logs | ForEach-Object {
        Write-Output "$($_.FullName) size=$($_.Length)"
    }
}

$manifest = Read-BotManifest

if ($Command -eq "list") {
    $manifest.bots.PSObject.Properties | ForEach-Object {
        Write-Output "$($_.Name) - $($_.Value.displayName)"
    }
    exit 0
}

$config = Get-BotConfig -Name $Bot

switch ($Command) {
    "status" { Show-BotStatus -Name $Bot -Config $config }
    "start" { Start-Bot -Name $Bot -Config $config }
    "stop" { Stop-Bot -Name $Bot -Config $config }
    "restart" {
        Stop-Bot -Name $Bot -Config $config
        Start-Bot -Name $Bot -Config $config
    }
    "logs" { Show-BotLogs -Name $Bot -Config $config }
}
