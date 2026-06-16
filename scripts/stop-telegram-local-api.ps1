$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"

function Import-ProjectEnv {
    if (-not (Test-Path $EnvFile)) {
        return
    }

    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $name, $value = $line.Split("=", 2)
        $name = $name.Trim()
        $value = $value.Trim().Trim('"').Trim("'")
        if ($name) {
            Set-Item -Path "Env:$name" -Value $value
        }
    }
}

function Get-EnvValue {
    param(
        [string] $Name,
        [string] $Default
    )

    $value = [Environment]::GetEnvironmentVariable($Name)
    if ($value) {
        return $value
    }
    return $Default
}

function Resolve-DockerCommand {
    $docker = Get-Command "docker" -ErrorAction SilentlyContinue
    if ($docker) {
        return $docker.Source
    }

    $defaultDocker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
    if (Test-Path $defaultDocker) {
        return $defaultDocker
    }

    return $null
}

function Invoke-DockerText {
    param(
        [string] $Docker,
        [string[]] $Arguments,
        [int] $TimeoutSeconds = 8
    )

    $job = Start-Job -ScriptBlock {
        param($DockerPath, $DockerArguments)
        $output = & $DockerPath @DockerArguments 2>&1
        [pscustomobject]@{
            ExitCode = $LASTEXITCODE
            Output = ($output -join "`n")
        }
    } -ArgumentList $Docker, $Arguments

    if (-not (Wait-Job $job -Timeout $TimeoutSeconds)) {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -Force -ErrorAction SilentlyContinue
        return [pscustomobject]@{
            ExitCode = 124
            Output = "Docker command timed out"
        }
    }

    $result = Receive-Job $job 2>&1
    Remove-Job $job -Force -ErrorAction SilentlyContinue
    return $result
}

Import-ProjectEnv

$docker = Resolve-DockerCommand
if (-not $docker) {
    Write-Output "telegram-local-api already stopped (Docker not found)"
    exit 0
}

$containerName = Get-EnvValue -Name "TELEGRAM_LOCAL_API_CONTAINER" -Default "pp1-telegram-bot-api"
$statusResult = Invoke-DockerText -Docker $docker -Arguments @("inspect", "-f", "{{.State.Status}}", $containerName)
if ($statusResult.ExitCode -eq 124) {
    Write-Output "telegram-local-api already stopped (Docker engine not running)"
    exit 0
}

if ($statusResult.ExitCode -ne 0) {
    Write-Output "telegram-local-api already stopped"
    exit 0
}

$status = $statusResult.Output.Trim()
if ($status -eq "running") {
    Invoke-DockerText -Docker $docker -Arguments @("stop", $containerName) | Out-Null
    Write-Output "telegram-local-api stopped container=$containerName"
    exit 0
}

Write-Output "telegram-local-api already $status container=$containerName"
